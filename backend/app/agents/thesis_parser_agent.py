"""
Thesis Parser Agent
────────────────────
Converts a natural-language VC fund thesis into a structured ParsedThesis.

Extracted criteria
------------------
sectors           – target industry verticals          (e.g. ["Developer Tools"])
stages            – investment stages                  (e.g. ["Pre-Seed", "Seed"])
geographies       – target markets                     (e.g. ["US", "EU"])
market_type       – buyer / go-to-market motion        (e.g. "B2B", "Enterprise")
founder_profile   – desired founder characteristics    (e.g. ["technical founders"])
signal_preferences– traction / growth signals to seek  (e.g. ["developer-led growth"])
anti_patterns     – things to exclude from pipeline    (e.g. ["consumer", "hardware"])

Falls back to keyword-based rule extraction when OpenRouter is unavailable.
"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.models import ParsedThesis
from app.services.openrouter_client import run_structured_llm

_SYSTEM = """\
You are an expert VC analyst. Parse the fund thesis below into structured investment criteria.

Guidelines:
- sectors:           Specific industry verticals (e.g. "Developer Tools", "B2B SaaS", "Fintech").
- stages:            Funding stages (e.g. "Pre-Seed", "Seed", "Series A"). Normalise to Title Case.
- geographies:       Target geographies (e.g. "US", "EU", "Global"). Default to "US" if unspecified.
- market_type:       Primary buyer motion — exactly one of: B2B, B2C, Enterprise, SMB, Marketplace, Consumer.
                     Infer from context if not stated explicitly.
- founder_profile:   Required founder traits or backgrounds (e.g. "technical founders",
                     "repeat founders", "domain experts", "ex-FAANG").
- signal_preferences:Traction or growth signals the fund values (e.g. "developer-led growth",
                     "strong word-of-mouth", "high NPS", "low CAC").
- anti_patterns:     Explicit exclusions or red flags (e.g. "consumer apps", "deep hardware").

Be specific. Extract every piece of information present; do not invent criteria absent from the text.\
"""


class _ThesisResponse(BaseModel):
    sectors: list[str] = []
    stages: list[str] = []
    geographies: list[str] = []
    market_type: Literal["B2B", "B2C", "Enterprise", "SMB", "Marketplace", "Consumer", ""] = ""
    founder_profile: list[str] = []
    signal_preferences: list[str] = []
    anti_patterns: list[str] = []


async def run(thesis: str) -> ParsedThesis:
    """Parse a raw thesis string into a structured ParsedThesis."""
    result = await run_structured_llm(
        f"Fund thesis: {thesis}",
        _ThesisResponse,
        system=_SYSTEM,
    )

    if not result:
        return _rule_based_parse(thesis)

    return ParsedThesis(
        raw=thesis,
        sectors=result.get("sectors", []),
        stages=result.get("stages", []),
        geographies=result.get("geographies", []),
        market_type=result.get("market_type", ""),
        founder_profile=result.get("founder_profile", []),
        signal_preferences=result.get("signal_preferences", []),
        signals=result.get("signal_preferences", []),  # keep legacy field in sync
        anti_patterns=result.get("anti_patterns", []),
    )


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _rule_based_parse(thesis: str) -> ParsedThesis:
    """Keyword-based extraction used when the LLM is unavailable."""
    t = thesis.lower()

    # Stages
    stages: list[str] = []
    for stage in ["pre-seed", "seed", "series a", "series b"]:
        if stage in t:
            stages.append(stage.title())

    # Sectors
    sectors: list[str] = []
    _SECTOR_MAP = {
        "developer tools": "Developer Tools",
        "devtools":        "Developer Tools",
        "dev tools":       "Developer Tools",
        "saas":            "B2B SaaS",
        "infrastructure":  "Infrastructure",
        "fintech":         "Fintech",
        "healthtech":      "Healthtech",
        "health tech":     "Healthtech",
        "enterprise":      "Enterprise Software",
        "vertical saas":   "Vertical SaaS",
        "vertical":        "Vertical SaaS",
        "ai":              "AI/ML",
        "machine learning":"AI/ML",
        "security":        "Cybersecurity",
        "cybersecurity":   "Cybersecurity",
        "marketplace":     "Marketplace",
        "climate":         "Climate Tech",
        "edtech":          "EdTech",
    }
    for keyword, sector in _SECTOR_MAP.items():
        if keyword in t and sector not in sectors:
            sectors.append(sector)

    # Geographies
    geographies: list[str] = []
    if any(kw in t for kw in ["us", "united states", "america", "north america"]):
        geographies.append("US")
    if any(kw in t for kw in ["eu", "europe", "european"]):
        geographies.append("EU")
    if "latam" in t or "latin america" in t:
        geographies.append("LatAm")
    if "global" in t:
        geographies.append("Global")

    # Market type
    market_type = ""
    if any(kw in t for kw in ["b2b", "business-to-business", "enterprise", "smb"]):
        market_type = "B2B"
        if "enterprise" in t:
            market_type = "Enterprise"
        elif "smb" in t or "small business" in t:
            market_type = "SMB"
    elif any(kw in t for kw in ["b2c", "consumer", "business-to-consumer"]):
        market_type = "B2C"
    elif "marketplace" in t:
        market_type = "Marketplace"

    # Founder profile
    founder_profile: list[str] = []
    _FOUNDER_MAP = {
        "technical founder":    "technical founders",
        "technical co-founder": "technical founders",
        "engineer":             "technical founders",
        "repeat founder":       "repeat founders",
        "serial entrepreneur":  "repeat founders",
        "domain expert":        "domain experts",
        "operator":             "operator background",
        "ex-google":            "ex-FAANG",
        "ex-facebook":          "ex-FAANG",
        "ex-amazon":            "ex-FAANG",
        "ex-faang":             "ex-FAANG",
        "phd":                  "PhD / research background",
        "research":             "research background",
        "strong team":          "strong founding team",
    }
    for keyword, profile in _FOUNDER_MAP.items():
        if keyword in t and profile not in founder_profile:
            founder_profile.append(profile)

    # Signal preferences
    signal_preferences: list[str] = []
    _SIGNAL_MAP = {
        "developer-led":      "developer-led growth",
        "developer led":      "developer-led growth",
        "product-led":        "product-led growth",
        "product led":        "product-led growth",
        "bottom-up":          "bottom-up adoption",
        "api-first":          "API-first",
        "open source":        "open-source traction",
        "ai-native":          "AI-native product",
        "ai native":          "AI-native product",
        "high growth":        "high revenue growth",
        "strong retention":   "strong user retention",
        "word of mouth":      "strong word-of-mouth",
        "low cac":            "low customer acquisition cost",
    }
    for keyword, signal in _SIGNAL_MAP.items():
        if keyword in t and signal not in signal_preferences:
            signal_preferences.append(signal)

    # Anti-patterns
    anti_patterns: list[str] = []
    _ANTI_MAP = {
        "no consumer":  "consumer apps",
        "not consumer": "consumer apps",
        "no hardware":  "hardware",
        "not hardware": "hardware",
        "no crypto":    "crypto / web3",
        "not crypto":   "crypto / web3",
        "no b2c":       "B2C",
    }
    for keyword, pattern in _ANTI_MAP.items():
        if keyword in t and pattern not in anti_patterns:
            anti_patterns.append(pattern)

    return ParsedThesis(
        raw=thesis,
        sectors=sectors or ["Technology"],
        stages=stages or ["Seed", "Series A"],
        geographies=geographies or ["US"],
        market_type=market_type,
        founder_profile=founder_profile,
        signal_preferences=signal_preferences,
        signals=signal_preferences,  # keep legacy field in sync
        anti_patterns=anti_patterns,
    )
