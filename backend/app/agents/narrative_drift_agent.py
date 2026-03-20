"""
Narrative Drift Agent
──────────────────────
Detects if a portfolio company's story has drifted from its original narrative.

Evaluation dimensions:
  1. Message Consistency  — does current messaging match the original positioning?
  2. Hiring Alignment     — do recent hires signal the same direction?
  3. Product Alignment    — do product updates stay true to the original thesis?
  4. Contradictions       — explicit contradictions between then and now.

Output:
  status        : "Stable" | "Watch" | "Drift Risk"
  overall_drift : 0–100 (0 = no drift, 100 = complete pivot)
  signals       : per-dimension breakdown with supporting evidence
  summary       : plain-English verdict

Status thresholds:
  overall_drift < 30  → Stable
  overall_drift 30–60 → Watch
  overall_drift > 60  → Drift Risk

Falls back to keyword-overlap heuristic when OpenRouter is unavailable or
USE_MOCK=true.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from app.config.settings import settings
from app.schemas.models import DriftReport, DriftSignal, StartupRecord
from app.services.browser_use_client import scrape
from app.services.openrouter_client import run_structured_llm

# ── Constants ─────────────────────────────────────────────────────────────────

_DIMENSIONS = [
    "Message Consistency",
    "Hiring Alignment",
    "Product Alignment",
    "Contradictions",
]

_SYSTEM = """\
You are a VC portfolio analyst specialising in narrative drift detection.

Your job is to compare a startup's *original narrative* (what they said at raise
time) with *current signals* (recent hiring, messaging updates, product news).

Evaluate four dimensions:
  1. Message Consistency  — is the external story still the same?
  2. Hiring Alignment     — do recent hires reinforce the original direction?
  3. Product Alignment    — do product changes fit the original positioning?
  4. Contradictions       — list any explicit contradictions you can identify.

Rules:
- Only include a dimension when you have concrete evidence to evaluate it.
- drift_score per dimension: 0 = perfect alignment, 100 = complete departure.
- Derive overall_drift as the weighted average of dimension scores.
- overall_drift < 30  → status "Stable"
  overall_drift 30-60 → status "Watch"
  overall_drift > 60  → status "Drift Risk"
- Populate evidence[] with 1-3 short bullet phrases (not full sentences) that
  justify your score for each dimension.\
"""


# ── Pydantic shapes for structured LLM output ─────────────────────────────────

class _SignalOut(BaseModel):
    dimension: str = ""
    original: str = ""
    current: str = ""
    drift_score: float = 0
    severity: Literal["none", "low", "medium", "high"] = "none"
    evidence: list[str] = []
    note: str = ""


class _DriftOut(BaseModel):
    status: Literal["Stable", "Watch", "Drift Risk"] = "Stable"
    overall_drift: float = 0
    signals: list[_SignalOut] = []
    summary: str = ""


# ── Public entry-point ────────────────────────────────────────────────────────

async def run(startup: StartupRecord) -> DriftReport:
    """Evaluate narrative drift for *startup* and return a DriftReport."""
    if not startup.original_narrative:
        return _no_baseline_report(startup)

    # Optionally enrich with live homepage content
    web_content = ""
    if startup.website and not settings.use_mock:
        try:
            web_content = await scrape(
                startup.website,
                instruction=(
                    "Extract the company's current positioning, product description, "
                    "target market, and any hiring mentions."
                ),
            )
        except Exception as exc:
            print(f"[drift] Web scrape failed for {startup.name}: {exc}")

    result = await run_structured_llm(
        _build_prompt(startup, web_content),
        _DriftOut,
        system=_SYSTEM,
    )

    if not result:
        return _rule_based_drift(startup)

    signals = [
        DriftSignal(
            dimension=sig.get("dimension", ""),
            original=sig.get("original", ""),
            current=sig.get("current", ""),
            drift_score=float(sig.get("drift_score", 0)),
            severity=sig.get("severity", "none"),
            evidence=sig.get("evidence", []),
            note=sig.get("note", ""),
        )
        for sig in result.get("signals", [])
    ]

    overall = float(result.get("overall_drift", 0))
    status = _derive_status(overall)

    return DriftReport(
        startup_id=startup.id,
        checked_at=datetime.now(timezone.utc).isoformat(),
        status=status,
        overall_drift=overall,
        signals=signals,
        summary=result.get("summary", ""),
    )


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(startup: StartupRecord, web_content: str) -> str:
    signals_str = "\n  - ".join(startup.signals) if startup.signals else "None provided"
    web_section = (
        f"\nCURRENT WEB CONTENT (homepage excerpt):\n{web_content[:1000]}"
        if web_content
        else ""
    )
    dims = ", ".join(_DIMENSIONS)
    return f"""\
COMPANY: {startup.name}
Stage: {startup.stage} | Sector: {startup.sector}

ORIGINAL NARRATIVE (at raise time):
{startup.original_narrative}

CURRENT SIGNALS (hiring, messaging, product updates):
  - {signals_str}
{web_section}

Evaluate narrative drift across: {dims}.
Only include a dimension when you have concrete evidence.
Return JSON conforming to the schema."""


# ── Status helper ─────────────────────────────────────────────────────────────

def _derive_status(drift: float) -> Literal["Stable", "Watch", "Drift Risk"]:
    if drift < 30:
        return "Stable"
    if drift < 60:
        return "Watch"
    return "Drift Risk"


# ── Fallbacks ─────────────────────────────────────────────────────────────────

def _no_baseline_report(startup: StartupRecord) -> DriftReport:
    return DriftReport(
        startup_id=startup.id,
        checked_at=datetime.now(timezone.utc).isoformat(),
        status="Stable",
        overall_drift=0,
        signals=[],
        summary=(
            "No original narrative on record. "
            "Set original_narrative on the startup to enable drift detection."
        ),
    )


def _rule_based_drift(startup: StartupRecord) -> DriftReport:
    """Keyword-overlap heuristic used when OpenRouter is unavailable."""
    stop_words = {"the", "a", "an", "and", "or", "in", "of", "to", "for", "is", "are", "with"}

    original_words = set((startup.original_narrative or "").lower().split()) - stop_words
    current_words = set(" ".join(startup.signals).lower().split()) - stop_words

    if not original_words:
        return _no_baseline_report(startup)

    overlap = len(original_words & current_words) / max(len(original_words), 1)
    drift = round((1 - overlap) * 100)
    status = _derive_status(drift)
    severity: Literal["none", "low", "medium", "high"] = (
        "none" if drift < 20
        else "low" if drift < 40
        else "medium" if drift < 65
        else "high"
    )

    lost = sorted(original_words - current_words)[:5]
    gained = sorted(current_words - original_words)[:5]
    evidence: list[str] = []
    if lost:
        evidence.append(f"Missing from signals: {', '.join(lost)}")
    if gained:
        evidence.append(f"New in signals: {', '.join(gained)}")

    return DriftReport(
        startup_id=startup.id,
        checked_at=datetime.now(timezone.utc).isoformat(),
        status=status,
        overall_drift=float(drift),
        signals=[
            DriftSignal(
                dimension="Message Consistency",
                original=startup.original_narrative or "",
                current=" | ".join(startup.signals[:3]),
                drift_score=float(drift),
                severity=severity,
                evidence=evidence,
                note=(
                    f"Keyword-overlap heuristic: {round(overlap * 100)}% of original "
                    "narrative terms still appear in current signals."
                ),
            )
        ],
        summary=(
            f"Rule-based verdict: {status} (drift score {drift}/100). "
            f"{round(overlap * 100)}% keyword overlap between original story and "
            "current signals. OpenRouter was unavailable; upgrade to LLM-based "
            "analysis for dimension-level evidence."
        ),
    )
