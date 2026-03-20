"""
Memo Generation Agent
──────────────────────
Generates a structured investment memo from a startup profile, fund thesis,
and thesis match score produced by the Thesis Match Agent.

Output sections
───────────────
  startup_summary   – who they are, what they build, team & key metrics
  why_it_matches    – specific fit vs. fund thesis (sector, stage, signals)
  bull_case         – best-case upside and opportunity framing
  bear_case         – key risks and downside scenarios
  key_signals       – list of concrete evidence bullets (frontend renders as list)
  next_step         – suggested concrete action (e.g. "Schedule technical deep-dive")
  recommendation    – "Pass" | "Take Meeting" | "Fast Track"

Falls back to a template-filled mock memo when USE_MOCK=true or LLM fails.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from app.config.settings import settings
from app.schemas.models import (
    FitDimensions,
    InvestmentMemo,
    MemoSections,
    ParsedThesis,
    StartupWithScore,
)
from app.services.openrouter_client import run_structured_llm

_SYSTEM = """\
You are a VC analyst writing a structured investment memo.

Rules:
- startup_summary:  2–3 sentences. Cover what the company does, the founding team in one
                    phrase, and the strongest metric or milestone.
- why_it_matches:   2–3 sentences. Be specific — cite thesis sectors, stage, and signal
                    preferences that this startup satisfies.
- bull_case:        2–3 sentences. Frame the upside: market size, timing, moat.
- bear_case:        2–3 sentences. Name the 2–3 most significant risks directly.
- key_signals:      Array of 3–5 short evidence strings (each < 15 words). These are
                    specific facts: metrics, milestones, partnerships, notable customers.
- next_step:        One concrete sentence. What should the fund do next?
                    (e.g. "Schedule a technical deep-dive with the CTO this week.")
- recommendation:   Exactly one of: "Pass", "Take Meeting", "Fast Track".
                    Use "Fast Track" only when fit_score ≥ 75.

No filler phrases. Be direct. Cite numbers when available.\
"""


class _MemoResponse(BaseModel):
    startup_summary: str = ""
    why_it_matches: str = ""
    bull_case: str = ""
    bear_case: str = ""
    key_signals: list[str] = []
    next_step: str = ""
    recommendation: Literal["Pass", "Take Meeting", "Fast Track"] = "Take Meeting"


async def run(thesis: ParsedThesis, startup: StartupWithScore) -> InvestmentMemo:
    result = await run_structured_llm(
        _build_prompt(thesis, startup),
        _MemoResponse,
        system=_SYSTEM,
        model=settings.memo_model,
        temperature=0.4,
    )

    if not result:
        return _mock_memo(thesis, startup)

    return InvestmentMemo(
        startup_id=startup.id,
        startup_name=startup.name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        sections=MemoSections(
            startup_summary=result.get("startup_summary", ""),
            why_it_matches=result.get("why_it_matches", ""),
            bull_case=result.get("bull_case", ""),
            bear_case=result.get("bear_case", ""),
            key_signals=result.get("key_signals", []),
            next_step=result.get("next_step", ""),
            recommendation=result.get("recommendation", "Take Meeting"),
        ),
    )


# ── Prompt construction ───────────────────────────────────────────────────────

def _build_prompt(thesis: ParsedThesis, s: StartupWithScore) -> str:
    founders_str = "; ".join(
        f"{f.name} — {f.background}" for f in s.founders
    ) or "Team info not available"

    metrics_parts: list[str] = []
    if s.metrics.arr:
        metrics_parts.append(f"ARR: {s.metrics.arr}")
    if s.metrics.growth:
        metrics_parts.append(f"Growth: {s.metrics.growth}")
    if s.metrics.customers:
        metrics_parts.append(f"Customers: {s.metrics.customers}")
    if s.metrics.team_size:
        metrics_parts.append(f"Team size: {s.metrics.team_size}")
    metrics_str = " | ".join(metrics_parts) or "Metrics not available"

    signals_str = "\n  - ".join(s.signals) or "No signals recorded"

    # Merge signal_preferences + signals for the thesis section
    signal_prefs = list(dict.fromkeys(
        (thesis.signal_preferences or []) + (thesis.signals or [])
    ))

    dims = s.fit_dimensions
    subscore_lines = (
        f"  sector_fit={dims.sector_fit:.0f}  stage_fit={dims.stage_fit:.0f}"
        f"  signal_strength={dims.signal_strength:.0f}"
        f"  team_fit={dims.team_fit:.0f}  market_reasoning={dims.market_reasoning:.0f}"
    )

    return f"""\
FUND THESIS
───────────
Raw:             {thesis.raw}
Sectors:         {", ".join(thesis.sectors) or "Any"}
Stages:          {", ".join(thesis.stages) or "Any"}
Market Type:     {thesis.market_type or "Not specified"}
Founder Profile: {", ".join(thesis.founder_profile) or "Not specified"}
Signal Prefs:    {", ".join(signal_prefs) or "None"}
Anti-patterns:   {", ".join(thesis.anti_patterns) or "Nothing specified"}

STARTUP PROFILE
───────────────
Name:        {s.name}
Stage:       {s.stage}  |  Sector: {s.sector}  |  Geography: {s.geography}
Founded:     {s.founded}  |  Website: {s.website or "N/A"}
Description: {s.description}
Founders:    {founders_str}
Metrics:     {metrics_str}

Key Signals:
  - {signals_str}

THESIS MATCH SCORE
──────────────────
Overall fit_score: {s.fit_score}/100
Subscores:
{subscore_lines}
Explanation: {s.explanation or "Not available"}

Write the investment memo. Be direct and specific.\
"""


# ── Template fallback ─────────────────────────────────────────────────────────

def _mock_memo(thesis: ParsedThesis, s: StartupWithScore) -> InvestmentMemo:
    founder_name = s.founders[0].name if s.founders else "the founding team"
    founder_bg   = s.founders[0].background if s.founders else "background details pending"
    lead_signal  = s.signals[0] if s.signals else "early momentum"
    metrics_str  = s.metrics.arr or "early-stage"

    recommendation = _recommend_from_score(s.fit_score)

    # Pull top 3–5 signals from the startup record for key_signals
    key_signals: list[str] = s.signals[:5] if s.signals else [
        f"{s.stage} stage in {s.sector}",
        f"Based in {s.geography}",
        f"Founded {s.founded}",
    ]

    return InvestmentMemo(
        startup_id=s.id,
        startup_name=s.name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        sections=MemoSections(
            startup_summary=(
                f"{s.name} is a {s.stage} {s.sector} company based in {s.geography}. "
                f"Founded by {founder_name} ({founder_bg}). "
                f"Current traction: {metrics_str}."
            ),
            why_it_matches=(
                f"Fits thesis on sector ({s.sector}), stage ({s.stage}), "
                f"and geography ({s.geography}). "
                f"Thesis match score: {s.fit_score}/100."
            ),
            bull_case=(
                f"The {s.sector} market is in early-adoption phase — "
                f"{s.name} is positioned to capture share before consolidation. "
                f"{lead_signal}."
            ),
            bear_case=(
                "1. Market timing risk — category may still be too early. "
                "2. Competition from well-funded incumbents entering the space. "
                "3. GTM execution risk at current team size."
            ),
            key_signals=key_signals,
            next_step=_suggest_next_step(recommendation, s),
            recommendation=recommendation,
        ),
    )


def _recommend_from_score(fit_score: float) -> str:
    if fit_score >= 75:
        return "Fast Track"
    if fit_score >= 45:
        return "Take Meeting"
    return "Pass"


def _suggest_next_step(recommendation: str, s: StartupWithScore) -> str:
    if recommendation == "Fast Track":
        return (
            f"Move quickly — schedule a 45-minute introductory call with {s.name}'s "
            f"CEO this week and request access to their data room."
        )
    if recommendation == "Take Meeting":
        return (
            f"Schedule a 30-minute intro call with {s.name} to validate "
            f"the thesis fit before the next partner meeting."
        )
    return (
        f"Pass at this stage — monitor {s.name} for 6 months and revisit "
        f"if they close a strong lead investor or hit $1M ARR."
    )
