"""
VC Analyst — Agent Orchestrator
─────────────────────────────────
Mastra-inspired step-based pipeline that chains all five agents in sequence.

Mastra concepts mapped to Python
─────────────────────────────────
  Workflow   → VCWorkflow   (named, owns the ordered step list)
  Step       → Step         (id + async execute(ctx) → Any)
  Context    → PipelineCtx  (mutable bag of typed outputs + traces)
  Trigger    → thesis_input (the raw string passed to run_vc_analysis)

Pipeline
─────────
  Step 1  parse_thesis       str              → ParsedThesis
  Step 2  discover_startups  ParsedThesis     → list[StartupRecord]
  Step 3  score_startups     (thesis, list)   → list[StartupWithScore]
  Step 4  generate_memo      (thesis, best)   → InvestmentMemo
  Step 5  check_drift        best_startup     → DriftReport

Demo mode
─────────
  When USE_MOCK=true (no real API keys configured), the orchestrator
  returns a complete, high-quality pre-baked result from demo_fixtures.py
  instead of running the agents. This ensures the full demo works offline.

Entry point
───────────
  run_vc_analysis(thesis_input: str) -> VCAnalysisResult

Each step:
  - Receives the shared PipelineCtx (typed outputs from all prior steps)
  - Appends a StepTrace (id, status, duration_ms, error)
  - On error: marks the trace, skips downstream steps that depend on failed output
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

from app.config.settings import settings
from app.services.demo_fixtures import build_demo_result
from app.agents import (
    memo_generation_agent,
    narrative_drift_agent,
    startup_discovery_agent,
    thesis_match_agent,
    thesis_parser_agent,
)
from app.schemas.models import (
    DriftReport,
    InvestmentMemo,
    ParsedThesis,
    StartupRecord,
    StartupWithScore,
    StepTrace,
    VCAnalysisResult,
)


# ── Pipeline context ──────────────────────────────────────────────────────────

@dataclass
class PipelineCtx:
    """Mutable context object passed through every step."""
    thesis_input: str

    # Outputs — populated progressively as steps succeed
    thesis: Optional[ParsedThesis] = None
    candidates: list[StartupRecord] = field(default_factory=list)
    scored: list[StartupWithScore] = field(default_factory=list)
    memo: Optional[InvestmentMemo] = None
    drift_report: Optional[DriftReport] = None

    # Execution trace — one entry per step
    traces: list[StepTrace] = field(default_factory=list)

    @property
    def best_startup(self) -> Optional[StartupWithScore]:
        return self.scored[0] if self.scored else None

    def to_result(self) -> VCAnalysisResult:
        return VCAnalysisResult(
            thesis=self.thesis or ParsedThesis(raw=self.thesis_input),
            candidates=self.scored or [],
            best_startup=self.best_startup,
            memo=self.memo,
            drift_report=self.drift_report,
            pipeline_trace=self.traces,
        )


# ── Step abstraction ──────────────────────────────────────────────────────────

StepFn = Callable[[PipelineCtx], Coroutine[Any, Any, None]]


@dataclass
class Step:
    """A named, async pipeline step.

    execute(ctx) mutates ctx in-place (writing its output field).
    Raising an exception marks the step as "error" without crashing the pipeline.
    """
    step_id: str
    fn: StepFn


async def _run_step(step: Step, ctx: PipelineCtx) -> StepTrace:
    start = time.perf_counter()
    try:
        await step.fn(ctx)
        duration_ms = (time.perf_counter() - start) * 1000
        trace = StepTrace(step_id=step.step_id, status="ok", duration_ms=round(duration_ms, 1))
    except Exception as exc:  # noqa: BLE001
        duration_ms = (time.perf_counter() - start) * 1000
        trace = StepTrace(
            step_id=step.step_id,
            status="error",
            duration_ms=round(duration_ms, 1),
            error=str(exc),
        )
        print(f"[orchestrator] Step '{step.step_id}' failed: {exc}")
    ctx.traces.append(trace)
    return trace


# ── Step implementations ──────────────────────────────────────────────────────

async def _parse_thesis(ctx: PipelineCtx) -> None:
    ctx.thesis = await thesis_parser_agent.run(ctx.thesis_input)


async def _discover_startups(ctx: PipelineCtx) -> None:
    if ctx.thesis is None:
        raise RuntimeError("parse_thesis must succeed before discover_startups")
    ctx.candidates = await startup_discovery_agent.run(ctx.thesis)


async def _score_startups(ctx: PipelineCtx) -> None:
    if ctx.thesis is None or not ctx.candidates:
        raise RuntimeError("discover_startups must succeed before score_startups")
    ctx.scored = await thesis_match_agent.run(ctx.thesis, ctx.candidates)


async def _generate_memo(ctx: PipelineCtx) -> None:
    if ctx.thesis is None or ctx.best_startup is None:
        raise RuntimeError("score_startups must succeed before generate_memo")
    ctx.memo = await memo_generation_agent.run(ctx.thesis, ctx.best_startup)


async def _check_drift(ctx: PipelineCtx) -> None:
    if ctx.best_startup is None:
        raise RuntimeError("score_startups must succeed before check_drift")
    # StartupWithScore extends StartupRecord so it satisfies narrative_drift_agent.run()
    ctx.drift_report = await narrative_drift_agent.run(ctx.best_startup)


# ── Workflow definition ───────────────────────────────────────────────────────

class VCWorkflow:
    """Mastra-style workflow: a named, ordered list of Steps."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: list[Step] = []

    def step(self, step_id: str, fn: StepFn) -> "VCWorkflow":
        """Register a step and return self for chaining."""
        self._steps.append(Step(step_id=step_id, fn=fn))
        return self

    async def execute(self, thesis_input: str) -> VCAnalysisResult:
        ctx = PipelineCtx(thesis_input=thesis_input)
        for step in self._steps:
            trace = await _run_step(step, ctx)
            # Stop pipeline if a critical early step fails
            if trace.status == "error" and step.step_id in {
                "parse_thesis",
                "discover_startups",
                "score_startups",
            }:
                # Mark remaining steps as skipped
                remaining = self._steps[self._steps.index(step) + 1:]
                for skipped in remaining:
                    ctx.traces.append(
                        StepTrace(step_id=skipped.step_id, status="skipped", duration_ms=0)
                    )
                break
        return ctx.to_result()


# ── Build the pipeline ────────────────────────────────────────────────────────

_workflow = (
    VCWorkflow("vc_analysis")
    .step("parse_thesis",       _parse_thesis)
    .step("discover_startups",  _discover_startups)
    .step("score_startups",     _score_startups)
    .step("generate_memo",      _generate_memo)
    .step("check_drift",        _check_drift)
)


# ── Public entry point ────────────────────────────────────────────────────────

async def run_vc_analysis(thesis_input: str) -> VCAnalysisResult:
    """Run the full VC analysis pipeline for a given thesis string.

    Steps (in order):
      1. parse_thesis       — extract structured criteria from raw text
      2. discover_startups  — find matching companies via Crustdata
      3. score_startups     — rank candidates by thesis fit (0–100)
      4. generate_memo      — write investment memo for the best candidate
      5. check_drift        — detect narrative drift for the best candidate

    Demo mode: when USE_MOCK=true, returns pre-baked fixture data from
    demo_fixtures.py so the full pipeline works offline without any API keys.

    Returns a VCAnalysisResult with all outputs and a step-by-step trace.
    """
    if not thesis_input or not thesis_input.strip():
        raise ValueError("thesis_input must not be empty")

    thesis_input = thesis_input.strip()

    # ── Demo mode ─────────────────────────────────────────────────────────────
    # When USE_MOCK=true (no real API keys) return a high-quality pre-baked
    # result rather than the sparse rule-based fallbacks.
    if settings.use_mock:
        return build_demo_result(thesis_input)

    return await _workflow.execute(thesis_input)
