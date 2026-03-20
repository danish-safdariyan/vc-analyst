from typing import Literal, Optional
from pydantic import BaseModel


# ── Shared ────────────────────────────────────────────────────────────────────

class FounderInfo(BaseModel):
    name: str
    background: str


class StartupMetrics(BaseModel):
    arr: Optional[str] = None
    growth: Optional[str] = None
    customers: Optional[int] = None
    team_size: Optional[int] = None


# ── Startup ───────────────────────────────────────────────────────────────────

class StartupRecord(BaseModel):
    id: str
    name: str
    website: str = ""
    founded: int = 2020
    stage: str  # Pre-Seed | Seed | Series A | Series B
    sector: str
    geography: str
    description: str
    founders: list[FounderInfo] = []
    metrics: StartupMetrics = StartupMetrics()
    signals: list[str] = []
    last_updated: str = ""
    original_narrative: Optional[str] = None


# ── Thesis ────────────────────────────────────────────────────────────────────

class ParsedThesis(BaseModel):
    raw: str
    sectors: list[str] = []
    stages: list[str] = []
    geographies: list[str] = []
    signals: list[str] = []
    anti_patterns: list[str] = []
    # Extended thesis criteria
    market_type: str = ""                # e.g. "B2B", "B2C", "Enterprise", "SMB"
    founder_profile: list[str] = []      # e.g. ["technical founders", "repeat founders"]
    signal_preferences: list[str] = []  # specific traction / growth signals to look for


# ── Scoring ───────────────────────────────────────────────────────────────────

class FitDimensions(BaseModel):
    sector_fit: float = 0       # how well the sector matches thesis sectors
    stage_fit: float = 0        # how well the funding stage matches
    team_fit: float = 0         # founding team credibility and thesis alignment
    signal_strength: float = 0  # traction signals vs. thesis signal preferences
    market_reasoning: float = 0 # market type, GTM motion, and buyer fit


class StartupWithScore(StartupRecord):
    fit_score: float = 0
    explanation: str = ""
    fit_dimensions: FitDimensions = FitDimensions()


# ── Memo ─────────────────────────────────────────────────────────────────────

class MemoSections(BaseModel):
    startup_summary: str = ""    # who they are, what they build, team & traction snapshot
    why_it_matches: str = ""     # specific fit vs. fund thesis criteria
    bull_case: str = ""          # upside scenario and biggest opportunity
    bear_case: str = ""          # key risks and downside scenarios
    key_signals: list[str] = [] # evidence bullets (rendered as a list by the frontend)
    next_step: str = ""          # concrete suggested action
    recommendation: str = "Take Meeting"  # Pass | Take Meeting | Fast Track


class InvestmentMemo(BaseModel):
    startup_id: str
    startup_name: str
    generated_at: str
    sections: MemoSections = MemoSections()


# ── Drift ─────────────────────────────────────────────────────────────────────

class DriftSignal(BaseModel):
    dimension: str
    original: str
    current: str
    drift_score: float = 0
    severity: Literal["none", "low", "medium", "high"] = "none"
    evidence: list[str] = []  # supporting quotes / signal bullets
    note: str = ""


class DriftReport(BaseModel):
    startup_id: str
    checked_at: str
    status: Literal["Stable", "Watch", "Drift Risk"] = "Stable"
    overall_drift: float = 0          # 0 = no drift, 100 = complete pivot
    signals: list[DriftSignal] = []
    summary: str = ""


# ── Orchestrator ──────────────────────────────────────────────────────────────

class StepTrace(BaseModel):
    step_id: str
    status: Literal["ok", "error", "skipped"] = "ok"
    duration_ms: float = 0.0
    error: Optional[str] = None


class VCAnalysisResult(BaseModel):
    thesis: "ParsedThesis"
    candidates: "list[StartupWithScore]" = []
    best_startup: "Optional[StartupWithScore]" = None
    memo: "Optional[InvestmentMemo]" = None
    drift_report: "Optional[DriftReport]" = None
    pipeline_trace: list[StepTrace] = []


# ── Request / Response bodies ─────────────────────────────────────────────────

class ParseThesisRequest(BaseModel):
    thesis: str


class ParseThesisResponse(BaseModel):
    parsed: ParsedThesis


class DiscoverRequest(BaseModel):
    thesis: ParsedThesis


class DiscoverResponse(BaseModel):
    startups: list[StartupRecord]


class ScoreRequest(BaseModel):
    thesis: ParsedThesis
    startups: list[StartupRecord]


class ScoreResponse(BaseModel):
    scored: list[StartupWithScore]


class MemoRequest(BaseModel):
    thesis: ParsedThesis
    startup: StartupWithScore  # carries fit_score + fit_dimensions from the match step


class MemoResponse(BaseModel):
    memo: InvestmentMemo


class DriftRequest(BaseModel):
    startup: StartupRecord


class DriftResponse(BaseModel):
    report: DriftReport


class AnalyzeRequest(BaseModel):
    thesis: str


class AnalyzeResponse(BaseModel):
    result: VCAnalysisResult


class ScrapeRequest(BaseModel):
    url: str
    instruction: str = "Extract the main content from this page"


class ScrapeResponse(BaseModel):
    content: str
    url: str
    scraped_at: str


# ── General VC Q&A (LLM chat) ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    used_mock: bool = False
