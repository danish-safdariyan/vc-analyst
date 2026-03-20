"""
Agent API routes — all 5 agent endpoints + orchestrator.
Mounted at /api in main.py

Routes
──────
  POST /api/parse-thesis        Parse raw thesis text → structured criteria
  POST /api/discover-startups   Find matching companies (Crustdata / mock)
  POST /api/score-startups      Score candidates by thesis fit (0–100)
  POST /api/generate-memo       Write investment memo for a startup
  POST /api/check-drift         Detect narrative drift for a portfolio company
  POST /api/run-analysis        Run the full 5-step pipeline end-to-end
  POST /api/chat                Ask the VC analyst assistant (OpenRouter LLM)
"""

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.agents import (
    memo_generation_agent,
    narrative_drift_agent,
    startup_discovery_agent,
    thesis_match_agent,
    thesis_parser_agent,
)
from app.orchestrator.workflow import run_vc_analysis
from app.schemas.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    DiscoverRequest,
    DiscoverResponse,
    DriftRequest,
    DriftResponse,
    MemoRequest,
    MemoResponse,
    ParseThesisRequest,
    ParseThesisResponse,
    ScoreRequest,
    ScoreResponse,
)
from app.config.settings import settings
from app.services.analysis_jobs import load_job, save_job
from app.services.openrouter_client import run_llm

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agents"])

_CHAT_SYSTEM = """You are a senior venture capital analyst assistant. Answer clearly and concisely.
When the user asks about startups, markets, diligence, or fund strategy, give practical VC-style insight.
If a question is outside investing or startups, answer helpfully but keep it brief.
Do not claim to have private or real-time data; frame opinions as analytical judgment, not facts."""

# ── Job store (memory + disk) ─────────────────────────────────────────────────
# Memory is fast; disk survives uvicorn --reload so GET /api/analysis/{id} keeps working.
_jobs: dict[str, dict[str, Any]] = {}


def _persist_job(job_id: str, status: str, result: Any = None, error: str | None = None) -> None:
    payload: dict[str, Any] = {"status": status, "error": error}
    if result is not None:
        payload["result"] = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    else:
        payload["result"] = None
    _jobs[job_id] = payload
    try:
        save_job(job_id, payload)
    except (OSError, ValueError) as exc:
        logger.warning("failed to persist job %s: %s", job_id, exc)


async def _run_analysis_job(job_id: str, thesis: str) -> None:
    """Run the full pipeline in the background and store the result."""
    try:
        result = await run_vc_analysis(thesis)
        _persist_job(job_id, "done", result=result)
    except Exception as exc:
        _persist_job(job_id, "error", error=str(exc))


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Open-ended Q&A powered by the same OpenRouter LLM as the rest of the app."""
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message must not be empty")

    if not settings.openrouter_api_key or settings.use_mock:
        return ChatResponse(
            reply=(
                "[Offline / mock mode] Hook up OPENROUTER_API_KEY and set USE_MOCK=false in "
                "backend/.env to get live answers. Meanwhile: as a VC analyst you’d look for "
                "clear ICP, repeatability in GTM, and evidence of retention or depth of use — "
                "ask something specific about a sector or stage and I can expand once the LLM is enabled."
            ),
            used_mock=True,
        )

    text = await run_llm(msg, system=_CHAT_SYSTEM, model=settings.fast_model, temperature=0.35)
    if not text.strip():
        return ChatResponse(
            reply=(
                "The model did not return an answer (check your OpenRouter key, quota, or try again)."
            ),
            used_mock=False,
        )
    return ChatResponse(reply=text.strip(), used_mock=False)


@router.post("/parse-thesis", response_model=ParseThesisResponse)
async def parse_thesis(req: ParseThesisRequest):
    """Parse a raw fund thesis string into structured investment criteria.

    Request body:
      { "thesis": "Pre-seed developer tools startups with strong technical founders." }

    Response:
      { "parsed": { "sectors": [...], "stages": [...], "market_type": "...", ... } }
    """
    if not req.thesis.strip():
        raise HTTPException(status_code=400, detail="thesis must not be empty")
    parsed = await thesis_parser_agent.run(req.thesis)
    return ParseThesisResponse(parsed=parsed)


@router.post("/discover-startups", response_model=DiscoverResponse)
async def discover_startups(req: DiscoverRequest):
    """Find startups matching the parsed thesis criteria.

    Request body:
      { "thesis": <ParsedThesis> }

    Response:
      { "startups": [ <StartupRecord>, ... ] }   (up to 5 results)
    """
    startups = await startup_discovery_agent.run(req.thesis)
    return DiscoverResponse(startups=startups)


@router.post("/score-startups", response_model=ScoreResponse)
async def score_startups(req: ScoreRequest):
    """Score each startup's fit against the thesis (0–100) across 5 dimensions.

    Request body:
      { "thesis": <ParsedThesis>, "startups": [ <StartupRecord>, ... ] }

    Response:
      { "scored": [ <StartupWithScore>, ... ] }   sorted highest-first
    """
    if not req.startups:
        raise HTTPException(status_code=400, detail="startups list must not be empty")
    scored = await thesis_match_agent.run(req.thesis, req.startups)
    return ScoreResponse(scored=scored)


@router.post("/generate-memo", response_model=MemoResponse)
async def generate_memo(req: MemoRequest):
    """Generate a structured 1-page investment memo for the selected startup.

    Request body:
      { "thesis": <ParsedThesis>, "startup": <StartupWithScore> }

    Response:
      { "memo": { "sections": { "startup_summary": "...", "bull_case": "...", ... } } }
    """
    memo = await memo_generation_agent.run(req.thesis, req.startup)
    return MemoResponse(memo=memo)


@router.post("/check-drift", response_model=DriftResponse)
async def check_drift(req: DriftRequest):
    """Detect narrative drift for a portfolio company vs. its original story.

    Request body:
      { "startup": <StartupRecord with original_narrative set> }

    Response:
      { "report": { "status": "Stable|Watch|Drift Risk", "overall_drift": 0-100, ... } }
    """
    report = await narrative_drift_agent.run(req.startup)
    return DriftResponse(report=report)


@router.post("/start-analysis")
async def start_analysis(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Submit a thesis and get back a job_id immediately.

    The analysis runs in the background (40-70 s).
    Poll GET /api/analysis/{job_id} until status == "done".
    """
    if not req.thesis.strip():
        raise HTTPException(status_code=400, detail="thesis must not be empty")
    job_id = str(uuid.uuid4())
    _persist_job(job_id, "running")
    background_tasks.add_task(_run_analysis_job, job_id, req.thesis)
    return {"job_id": job_id, "status": "running"}


@router.get("/analysis/{job_id}")
async def get_analysis(job_id: str):
    """Poll for the result of a submitted analysis job.

    Returns:
      { "status": "running" }                  — still in progress
      { "status": "done", "result": { ... } }  — finished
      { "status": "error", "error": "..." }    — failed
    """
    job = _jobs.get(job_id) or load_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    _jobs[job_id] = job  # warm cache after reload
    if job["status"] == "done":
        return {"status": "done", "result": job["result"]}
    return {"status": job["status"], "error": job.get("error")}


@router.post("/run-analysis", response_model=AnalyzeResponse)
async def run_analysis(req: AnalyzeRequest):
    """Run the full VC analysis pipeline end-to-end from a raw thesis string.

    Executes five steps in sequence:
      1. parse-thesis       — extract structured criteria
      2. discover-startups  — find matching companies (Crustdata / mock)
      3. score-startups     — rank candidates by thesis fit (0–100)
      4. generate-memo      — write investment memo for the best candidate
      5. check-drift        — detect narrative drift for the best candidate

    Request body:
      { "thesis": "Pre-seed developer tools startups with strong technical founders." }

    Response:
      {
        "result": {
          "thesis":          <ParsedThesis>,
          "candidates":      [ <StartupWithScore>, ... ],
          "best_startup":    <StartupWithScore>,
          "memo":            <InvestmentMemo>,
          "drift_report":    <DriftReport>,
          "pipeline_trace":  [ { "step_id": "...", "status": "ok|error|skipped", "duration_ms": 0 }, ... ]
        }
      }
    """
    if not req.thesis.strip():
        raise HTTPException(status_code=400, detail="thesis must not be empty")
    result = await run_vc_analysis(req.thesis)
    return AnalyzeResponse(result=result)
