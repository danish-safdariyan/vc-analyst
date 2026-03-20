"""
Thesis Match Agent
───────────────────
Scores each startup's fit against the parsed fund thesis (0–100).

For each startup one LLM call scores 5 dimensions:

  Dimension          Weight   What it measures
  ─────────────────  ──────   ──────────────────────────────────────────────
  sector_fit           30%    Industry vertical vs. thesis target sectors
  stage_fit            20%    Funding stage vs. thesis investment stages
  signal_strength      20%    Traction signals vs. thesis signal preferences
  team_fit             15%    Founder profile vs. thesis founder criteria
  market_reasoning     15%    Market type, GTM motion, and buyer fit

  fit_score = weighted sum (0–100, rounded to 1 dp)

Output shape
────────────
  {
    "fit_score":       float,        # total_score (0–100)
    "fit_dimensions": {
      "sector_fit":       float,
      "stage_fit":        float,
      "team_fit":         float,
      "signal_strength":  float,
      "market_reasoning": float
    },
    "explanation":     str           # 2–3 sentence reasoning
  }

Falls back to rule-based scoring when USE_MOCK=true or LLM call fails.
"""

from pydantic import BaseModel, Field

from app.schemas.models import FitDimensions, ParsedThesis, StartupRecord, StartupWithScore
from app.services.openrouter_client import run_structured_llm

_SYSTEM = """\
You are a senior VC analyst scoring startup–thesis fit.

Score each of the 5 dimensions from 0 to 100:

  sector_fit       — Does the startup's sector/vertical match the thesis target sectors?
                     100 = exact match, 0 = completely outside thesis scope.

  stage_fit        — Is the startup's current funding stage within the thesis investment range?
                     100 = perfect stage match, 0 = too early or too late.

  signal_strength  — How strongly do the startup's traction signals, growth metrics, and
                     recent news match the thesis signal preferences?
                     100 = every preferred signal present, 0 = no signal overlap.

  team_fit         — Does the founding team match the thesis founder profile requirements
                     (e.g. technical founders, repeat founders, domain experts)?
                     100 = ideal team profile, 0 = no match.

  market_reasoning — Does the startup's market type (B2B/B2C/Enterprise/SMB), GTM motion,
                     and buyer segment align with the thesis market preferences?
                     100 = perfect market alignment, 0 = wrong buyer and motion.

Scoring calibration:
  80–100  Strong conviction — recommend for pipeline
  60–79   Reasonable fit — worth a second look
  40–59   Weak fit — notable gaps vs. thesis
  0–39    Poor fit — outside thesis scope

Be critical and justify your scores in the explanation field.\
"""


class _MatchResponse(BaseModel):
    sector_fit: float = Field(default=50, ge=0, le=100)
    stage_fit: float = Field(default=50, ge=0, le=100)
    team_fit: float = Field(default=50, ge=0, le=100)
    signal_strength: float = Field(default=50, ge=0, le=100)
    market_reasoning: float = Field(default=50, ge=0, le=100)
    explanation: str = ""


# ── Weights must sum to 1.0 ───────────────────────────────────────────────────
_WEIGHTS = {
    "sector_fit":       0.30,
    "stage_fit":        0.20,
    "signal_strength":  0.20,
    "team_fit":         0.15,
    "market_reasoning": 0.15,
}


async def run(
    thesis: ParsedThesis,
    startups: list[StartupRecord],
) -> list[StartupWithScore]:
    """Score every startup against the thesis; return sorted highest-first."""
    import asyncio
    scored = await asyncio.gather(*[_score_one(thesis, s) for s in startups])
    return sorted(scored, key=lambda s: s.fit_score, reverse=True)


async def _score_one(thesis: ParsedThesis, startup: StartupRecord) -> StartupWithScore:
    result = await run_structured_llm(
        _build_prompt(thesis, startup),
        _MatchResponse,
        system=_SYSTEM,
    )

    if not result:
        return _rule_based_score(thesis, startup)

    dims = FitDimensions(
        sector_fit=float(result.get("sector_fit", 50)),
        stage_fit=float(result.get("stage_fit", 50)),
        team_fit=float(result.get("team_fit", 50)),
        signal_strength=float(result.get("signal_strength", 50)),
        market_reasoning=float(result.get("market_reasoning", 50)),
    )
    fit_score = _weighted_score(dims)

    return StartupWithScore(
        **startup.model_dump(),
        fit_score=fit_score,
        explanation=result.get("explanation", ""),
        fit_dimensions=dims,
    )


def _weighted_score(dims: FitDimensions) -> float:
    return round(
        _WEIGHTS["sector_fit"]       * dims.sector_fit
        + _WEIGHTS["stage_fit"]      * dims.stage_fit
        + _WEIGHTS["signal_strength"] * dims.signal_strength
        + _WEIGHTS["team_fit"]       * dims.team_fit
        + _WEIGHTS["market_reasoning"] * dims.market_reasoning,
        1,
    )


# ── Prompt construction ───────────────────────────────────────────────────────

def _build_prompt(thesis: ParsedThesis, s: StartupRecord) -> str:
    founders_str = "; ".join(
        f"{f.name} ({f.background})" for f in s.founders
    ) or "Unknown"

    metrics_parts: list[str] = []
    if s.metrics.arr:
        metrics_parts.append(f"ARR {s.metrics.arr}")
    if s.metrics.growth:
        metrics_parts.append(f"growth {s.metrics.growth}")
    if s.metrics.customers:
        metrics_parts.append(f"{s.metrics.customers} customers")
    if s.metrics.team_size:
        metrics_parts.append(f"{s.metrics.team_size} employees")
    metrics_str = " | ".join(metrics_parts) or "No metrics available"

    # Merge signal_preferences (primary) + signals (legacy) for the prompt
    signal_prefs = list(dict.fromkeys(
        (thesis.signal_preferences or []) + (thesis.signals or [])
    ))

    return f"""\
FUND THESIS
───────────
Sectors:           {", ".join(thesis.sectors) or "Any"}
Stages:            {", ".join(thesis.stages) or "Any"}
Geographies:       {", ".join(thesis.geographies) or "Any"}
Market Type:       {thesis.market_type or "Not specified"}
Founder Profile:   {", ".join(thesis.founder_profile) or "Not specified"}
Signal Prefs:      {", ".join(signal_prefs) or "None"}
Anti-patterns:     {", ".join(thesis.anti_patterns) or "Nothing specified"}

STARTUP PROFILE
───────────────
Name:        {s.name}
Stage:       {s.stage}
Sector:      {s.sector}
Geography:   {s.geography}
Description: {s.description}
Founders:    {founders_str}
Metrics:     {metrics_str}
Signals:     {" | ".join(s.signals) or "None"}

Score this startup's fit with the fund thesis across all 5 dimensions.\
"""


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _rule_based_score(thesis: ParsedThesis, s: StartupRecord) -> StartupWithScore:
    sector_fit = _keyword_overlap(thesis.sectors, [s.sector]) * 100
    stage_fit  = _keyword_overlap(thesis.stages,  [s.stage])  * 100

    # signal_strength: thesis signal prefs vs. startup signals + description
    signal_terms = list(dict.fromkeys(
        (thesis.signal_preferences or []) + (thesis.signals or [])
    ))
    signal_strength = _keyword_overlap(signal_terms, s.signals + [s.description]) * 100

    # team_fit: founder count as a rough proxy; boost if founder_profile keywords match
    team_fit = min(len(s.founders) * 35.0, 70.0)
    if thesis.founder_profile:
        founder_text = " ".join(
            f.name + " " + f.background for f in s.founders
        ).lower()
        profile_hits = sum(
            1 for kw in thesis.founder_profile
            if kw.lower() in founder_text
        )
        team_fit = min(team_fit + profile_hits * 15.0, 100.0)

    # market_reasoning: market_type keyword + signal-preference overlap
    market_haystack = (s.description + " " + s.sector + " " + " ".join(s.signals)).lower()
    market_reasoning = 50.0  # neutral baseline
    if thesis.market_type and thesis.market_type.lower() in market_haystack:
        market_reasoning = 80.0
    elif thesis.market_type:
        market_reasoning = 25.0

    dims = FitDimensions(
        sector_fit=sector_fit,
        stage_fit=stage_fit,
        team_fit=team_fit,
        signal_strength=signal_strength,
        market_reasoning=market_reasoning,
    )
    fit_score = _weighted_score(dims)

    parts = [
        f"sector={sector_fit:.0f}",
        f"stage={stage_fit:.0f}",
        f"signals={signal_strength:.0f}",
        f"team={team_fit:.0f}",
        f"market={market_reasoning:.0f}",
    ]
    explanation = f"Rule-based score ({', '.join(parts)}). LLM unavailable."

    return StartupWithScore(
        **s.model_dump(),
        fit_score=fit_score,
        explanation=explanation,
        fit_dimensions=dims,
    )


def _keyword_overlap(targets: list[str], haystack: list[str]) -> float:
    """Fraction of targets found (case-insensitive) in haystack. 0.75 if unconstrained."""
    if not targets:
        return 0.75
    combined = " ".join(haystack).lower()
    hits = sum(1 for t in targets if t.lower() in combined)
    return hits / len(targets)
