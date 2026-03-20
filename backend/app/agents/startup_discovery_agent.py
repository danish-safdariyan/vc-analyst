"""
Startup Discovery Agent
────────────────────────
Finds startups that match the parsed fund thesis.

Flow
────
1. Build keyword queries from sectors → signal_preferences → market_type
   (up to 4 unique queries to avoid hammering the API)
2. Search ALL available sources in parallel:
      • Crustdata  — professional company database (LinkedIn-backed)
      • Product Hunt — recently launched products (needs PRODUCTHUNT_API_KEY)
3. Merge & de-duplicate results by company id
4. Enrich each result with people data via get_company_people()
5. Filter by stage and industry (hard + soft rules)
6. Score remaining candidates by signal relevance
7. Return top 5 by relevance score as normalised StartupRecords

Sources fall back gracefully:
  - Crustdata: falls back to built-in mock data if API fails
  - Product Hunt: returns empty list if key absent or API fails
"""

import asyncio
import re
import unicodedata

from app.schemas.models import FounderInfo, ParsedThesis, StartupMetrics, StartupRecord
from app.services.crustdata_client import (
    CompanyProfile,
    PersonProfile,
    get_company_people,
    search_companies_by_keyword,
)
from app.services.producthunt_client import search_startups as ph_search_startups

_TOP_N = 10  # send top 10 to the LLM scorer; scorer returns all, UI shows best 5


async def run(thesis: ParsedThesis) -> list[StartupRecord]:
    """Discover startups matching the thesis; return at most _TOP_N results."""
    keywords = _build_keywords(thesis)

    # ── 1. Fetch from all sources in parallel ─────────────────────────────────
    seen: dict[str, CompanyProfile] = {}

    # Build coroutines for all keyword × source combinations
    crust_tasks = [search_companies_by_keyword(kw) for kw in keywords]
    ph_tasks    = [ph_search_startups(kw) for kw in keywords[:2]]  # cap PH to 2 queries

    all_results = await asyncio.gather(*crust_tasks, *ph_tasks, return_exceptions=True)

    for result in all_results:
        if isinstance(result, Exception):
            print(f"[discovery] source error (skipped): {result}")
            continue
        for company in result:
            if company.id not in seen:
                seen[company.id] = company

    print(f"[discovery] total unique companies from all sources: {len(seen)}")
    companies = list(seen.values())

    # ── 2. Enrich with founder data (best-effort, skip on failure) ───────────
    # Note: Crustdata people search endpoint requires a different auth tier.
    # We skip enrichment silently to avoid flooding logs with 404s.
    # Founder data from company profiles is still preserved where available.

    # ── 3. Score by signal relevance, keep top N ──────────────────────────────
    # Skip the blunt keyword pre-filter — Crustdata/PH industry labels rarely
    # match thesis vocabulary, so it was discarding good real companies.
    # The LLM scorer in thesis_match_agent handles relevance much more accurately.
    scored = sorted(companies, key=lambda c: _relevance_score(c, thesis), reverse=True)
    top = scored[:_TOP_N]

    return [_to_startup_record(c) for c in top]


# ── Keyword building ──────────────────────────────────────────────────────────

def _build_keywords(thesis: ParsedThesis) -> list[str]:
    """
    Priority order: sectors → signal_preferences → market_type
    Cap at 4 to stay API-friendly in the demo context.
    """
    candidates: list[str] = []

    # Sectors are the strongest discriminator
    candidates.extend(thesis.sectors[:2])

    # signal_preferences carry more nuance than generic signals
    prefs = thesis.signal_preferences or thesis.signals
    candidates.extend(prefs[:2])

    # market_type adds a useful B2B / Enterprise / etc. filter
    if thesis.market_type:
        candidates.append(thesis.market_type)

    # Raw thesis text as last resort
    if not candidates and thesis.raw:
        candidates.append(thesis.raw[:80])

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for kw in candidates:
        key = kw.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(kw)

    return unique[:4]


# ── Filtering ─────────────────────────────────────────────────────────────────

def _filter(companies: list[CompanyProfile], thesis: ParsedThesis) -> list[CompanyProfile]:
    """
    Apply stage and industry filters.

    Stage  – hard filter: if the thesis specifies stages and a company's stage
             clearly doesn't match any of them, exclude it.
    Industry – soft filter: if the thesis specifies sectors, companies whose
             industry has zero keyword overlap are excluded.  We use a soft
             approach here (keyword overlap rather than exact match) because
             Crustdata industry labels don't always match the thesis vocabulary.
    """
    result: list[CompanyProfile] = []

    for company in companies:
        if thesis.stages and not _stage_matches(company.funding_stage, thesis.stages):
            continue
        if thesis.sectors and not _industry_matches(company.industry, thesis.sectors):
            continue
        result.append(company)

    # If filtering is too aggressive (e.g. vague thesis), fall back to all
    return result if result else companies


def _stage_matches(company_stage: str, thesis_stages: list[str]) -> bool:
    """
    True when company_stage is compatible with at least one thesis stage.
    Uses normalised token overlap so "Series A" matches "series_a", etc.
    """
    c = _tokens(company_stage)
    for ts in thesis_stages:
        if c & _tokens(ts):
            return True
    return False


def _industry_matches(industry: str, sectors: list[str]) -> bool:
    """
    True when industry shares at least one meaningful token with any thesis sector.
    Handles cases like "Developer Tools" ↔ "developer", "B2B SaaS" ↔ "saas".
    """
    ind_tokens = _tokens(industry)
    for sector in sectors:
        if ind_tokens & _tokens(sector):
            return True
    return False


# ── Relevance scoring ─────────────────────────────────────────────────────────

def _relevance_score(company: CompanyProfile, thesis: ParsedThesis) -> float:
    """
    0–100 score based on how well a company's content matches the thesis.

    Component weights
    -----------------
    Sector match      35 %  – industry ↔ thesis sectors
    Stage match       20 %  – funding_stage ↔ thesis stages
    Signal match      30 %  – company signals + description ↔ thesis signals/prefs
    Geo match         15 %  – geography ↔ thesis geographies
    """
    haystack = _fold(
        " ".join([
            company.name,
            company.description,
            company.industry,
            company.funding_stage,
            company.geography,
            *company.signals,
        ])
    )

    def overlap(terms: list[str]) -> float:
        if not terms:
            return 0.75  # unconstrained → neutral
        hits = sum(1 for t in terms if _fold(t) in haystack)
        return hits / len(terms)

    # Gather all thesis signal terms
    signal_terms = list(dict.fromkeys(
        (thesis.signal_preferences or []) + (thesis.signals or [])
    ))

    sector_score  = overlap(thesis.sectors)    * 100
    stage_score   = overlap(thesis.stages)     * 100
    signal_score  = overlap(signal_terms)      * 100
    geo_score     = overlap(thesis.geographies)* 100

    return (
        0.35 * sector_score
        + 0.20 * stage_score
        + 0.30 * signal_score
        + 0.15 * geo_score
    )


# ── Schema mapping ────────────────────────────────────────────────────────────

def _to_startup_record(c: CompanyProfile) -> StartupRecord:
    return StartupRecord(
        id=c.id,
        name=c.name,
        website=c.website,
        founded=c.founded or 2020,
        stage=c.funding_stage or "Seed",
        sector=c.industry,
        geography=c.geography,
        description=c.description,
        founders=[_to_founder_info(p) for p in c.founders],
        metrics=StartupMetrics(team_size=c.employee_count or None),
        signals=c.signals,
        last_updated="",
        original_narrative=None,
    )


def _to_founder_info(p: PersonProfile) -> FounderInfo:
    return FounderInfo(
        name=p.name,
        background=p.background or p.title,
    )


# ── String utilities ──────────────────────────────────────────────────────────

_STOP = {"the", "a", "an", "and", "or", "in", "of", "to", "for", "is", "are", "at"}


def _tokens(text: str) -> set[str]:
    """Lower-case, accent-fold, split into words, drop stop-words."""
    return {w for w in _fold(text).split() if w not in _STOP and len(w) > 1}


def _fold(text: str) -> str:
    """Lowercase + strip Unicode accents for fuzzy matching."""
    normalised = unicodedata.normalize("NFD", text.lower())
    return re.sub(r"[^\x00-\x7f]", "", normalised)
