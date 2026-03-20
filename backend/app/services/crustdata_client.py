"""
Crustdata API client
────────────────────
Public functions
  search_companies_by_keyword(keyword)   → list[CompanyProfile]
  get_company_profile(company_id)        → CompanyProfile | None
  get_company_people(company_id)         → list[PersonProfile]

All three fall back to mock data when CRUSTDATA_API_KEY is absent or USE_MOCK=true.
The Startup Discovery Agent consumes these functions.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import httpx

from app.config.settings import settings

# ── Crustdata base URL ────────────────────────────────────────────────────────

_BASE = "https://api.crustdata.com"
_TIMEOUT = 15  # seconds

# Map our sector keywords → Crustdata INDUSTRY filter values
# https://docs.crustdata.com  (valid INDUSTRY values from the screener)
_SECTOR_TO_INDUSTRY: dict[str, list[str]] = {
    "developer tools":      ["Software Development"],
    "devtools":             ["Software Development"],
    "b2b saas":             ["Software Development", "IT Services and IT Consulting"],
    "saas":                 ["Software Development"],
    "infrastructure":       ["Software Development", "IT Services and IT Consulting"],
    "ai":                   ["Software Development", "Technology, Information and Internet"],
    "ai/ml":                ["Software Development", "Technology, Information and Internet"],
    "fintech":              ["Financial Services", "Banking"],
    "healthtech":           ["Hospitals and Health Care", "Medical Practices"],
    "cybersecurity":        ["Computer and Network Security"],
    "security":             ["Computer and Network Security"],
    "marketplace":          ["Technology, Information and Internet"],
    "vertical saas":        ["Software Development"],
    "enterprise software":  ["Software Development", "IT Services and IT Consulting"],
    "edtech":               ["E-Learning Providers", "Education Management"],
    "climate tech":         ["Utilities", "Renewable Energy Semiconductor Manufacturing"],
    "b2b":                  ["Software Development"],
}

# Headcount ranges that represent early-stage startups
_STARTUP_HEADCOUNT = ["1-10", "11-50", "51-200", "201-500"]


# ── Normalised schemas (plain dataclasses — no Pydantic overhead here) ─────────

@dataclass
class PersonProfile:
    name: str
    title: str = ""
    linkedin_url: str = ""
    background: str = ""          # derived: title + notable past roles


@dataclass
class CompanyProfile:
    """
    Normalised company record consumed by the Startup Discovery Agent
    and mapped to StartupRecord for the rest of the pipeline.
    """
    id: str
    name: str
    description: str = ""
    industry: str = ""            # primary sector / vertical
    funding_stage: str = ""       # Pre-Seed | Seed | Series A | Series B | …
    employee_count: int = 0
    website: str = ""
    linkedin_url: str = ""
    geography: str = ""
    founded: int = 0
    founders: list[PersonProfile] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    # raw crustdata payload kept for debugging / drift baseline
    _raw: dict = field(default_factory=dict, repr=False)


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Token {settings.crustdata_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ── Public API ────────────────────────────────────────────────────────────────

async def search_companies_by_keyword(keyword: str) -> list[CompanyProfile]:
    """
    Search Crustdata for startups matching a keyword / sector.

    Crustdata endpoint:
        POST /screener/company/search
        {
          filters: [
            { filter_type: "INDUSTRY", type: "in", value: [...] },
            { filter_type: "COMPANY_HEADCOUNT", type: "in", value: [...] }
          ],
          page: 1
        }

    The keyword is mapped to one or more Crustdata INDUSTRY values via
    _SECTOR_TO_INDUSTRY. Headcount is restricted to startup range (1–500).
    Falls back to filtered mock data if API key is missing.
    """
    if not settings.crustdata_api_key or settings.use_mock:
        return _mock_search(keyword)

    industries = _keyword_to_industries(keyword)

    try:
        # Use different pages per keyword so different theses surface different companies.
        # Simple deterministic offset: hash the keyword to pick page 1, 2, or 3.
        import hashlib
        page_offset = (int(hashlib.md5(keyword.encode()).hexdigest(), 16) % 3) + 1

        base_filters: list[dict] = [
            {"filter_type": "INDUSTRY",          "type": "in", "value": industries},
            {"filter_type": "COMPANY_HEADCOUNT", "type": "in", "value": _STARTUP_HEADCOUNT},
        ]

        print(f"[crustdata] POST /screener/company/search  industries={industries} page_offset={page_offset}")
        raw_list: list[dict] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            # Fetch the keyword-specific page plus the next page for more candidates
            for page in (page_offset, page_offset + 1):
                resp = await http.post(
                    f"{_BASE}/screener/company/search",
                    headers=_headers(),
                    json={"filters": base_filters, "page": page},
                )
                print(f"[crustdata] page={page} status={resp.status_code}")
                if resp.status_code != 200:
                    # Fall back to page 1 if the offset page doesn't exist
                    if page != 1:
                        resp = await http.post(
                            f"{_BASE}/screener/company/search",
                            headers=_headers(),
                            json={"filters": base_filters, "page": 1},
                        )
                        if resp.status_code == 200:
                            body = resp.json()
                            raw_list.extend(
                                body.get("companies") or body.get("data") or
                                body.get("results") or body.get("items") or
                                (body if isinstance(body, list) else [])
                            )
                    break
                body = resp.json()
                page_items = (
                    body.get("companies")
                    or body.get("data")
                    or body.get("results")
                    or body.get("items")
                    or (body if isinstance(body, list) else [])
                )
                raw_list.extend(page_items)
                if not page_items:
                    break

            print(f"[crustdata] got {len(raw_list)} raw companies for keyword='{keyword}'")
            # Post-filter: prefer companies founded 2018+, fall back gracefully
            def _year(c: dict) -> int:
                try:
                    return int(c.get("founded_year") or c.get("founded") or 0)
                except (ValueError, TypeError):
                    return 0

            recent_2018 = [c for c in raw_list if _year(c) >= 2018]
            recent_2015 = [c for c in raw_list if _year(c) >= 2015]
            recent_2010 = [c for c in raw_list if _year(c) >= 2010]

            if len(recent_2018) >= 5:
                filtered = recent_2018
            elif len(recent_2015) >= 3:
                filtered = recent_2015
            elif len(recent_2010) >= 3:
                filtered = recent_2010
            else:
                filtered = raw_list  # no founding year data — use all

            print(f"[crustdata] {len(filtered)} companies after recency filter")
            return [_normalise_company(c) for c in filtered[:10]]

    except httpx.HTTPStatusError as exc:
        print(f"[crustdata] HTTP {exc.response.status_code} — {exc.response.text[:200]}")
        return []  # never inject mock data — let other sources fill the gap
    except Exception as exc:
        print(f"[crustdata] search_companies_by_keyword failed: {exc!r}")
        return []  # never inject mock data — let other sources fill the gap


async def get_company_profile(company_id: str) -> CompanyProfile | None:
    """
    Fetch a single company's full profile from Crustdata.

    Crustdata endpoint used:
        GET /screener/company/{company_id}

    Falls back to finding the company in mock data by id.
    """
    if not settings.crustdata_api_key or settings.use_mock:
        return _mock_by_id(company_id)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            resp = await http.get(
                f"{_BASE}/screener/company/{company_id}",
                headers=_headers(),
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return _normalise_company(resp.json())

    except Exception as exc:
        print(f"[crustdata] get_company_profile({company_id}) failed → mock: {exc}")
        return _mock_by_id(company_id)


async def get_company_people(company_id: str) -> list[PersonProfile]:
    """
    Fetch founders / executives at a company using the people screener.

    Crustdata endpoint:
        POST /screener/company/search
        { filters: [{ filter_type: "CURRENT_COMPANY", type: "in", value: [company_id] },
                    { filter_type: "CURRENT_TITLE", type: "in", value: [...] }], page: 1 }

    Falls back to the founders embedded in the mock record.
    """
    if not settings.crustdata_api_key or settings.use_mock:
        record = _mock_by_id(company_id)
        return record.founders if record else []

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            resp = await http.post(
                f"{_BASE}/screener/people/search",
                headers=_headers(),
                json={
                    "filters": [
                        {"filter_type": "CURRENT_COMPANY", "type": "in", "value": [company_id]},
                        {"filter_type": "CURRENT_TITLE",   "type": "in",
                         "value": ["Founder", "Co-Founder", "CEO", "CTO", "CPO"]},
                    ],
                    "page": 1,
                },
            )
            resp.raise_for_status()
            people = resp.json().get("people", resp.json().get("profiles", []))
            return [_normalise_person(p) for p in people[:5]]

    except Exception as exc:
        print(f"[crustdata] get_company_people({company_id}) failed → mock: {exc}")
        record = _mock_by_id(company_id)
        return record.founders if record else []


# ── Normalisation helpers ─────────────────────────────────────────────────────

def _keyword_to_industries(keyword: str) -> list[str]:
    """
    Map a free-text sector keyword to Crustdata INDUSTRY filter values.

    Tries an exact lookup in _SECTOR_TO_INDUSTRY first, then checks if any
    key is a substring of the keyword (or vice-versa). Falls back to
    "Software Development" so the search always has a valid filter.
    """
    kw = keyword.lower().strip()
    # Exact match
    if kw in _SECTOR_TO_INDUSTRY:
        return _SECTOR_TO_INDUSTRY[kw]
    # Partial / substring match
    for key, industries in _SECTOR_TO_INDUSTRY.items():
        if key in kw or kw in key:
            return industries
    # Generic fallback
    return ["Software Development", "Technology, Information and Internet"]


def _stage_from_headcount(headcount_range: str) -> str:
    """Derive a rough funding stage from employee_count_range when no stage is provided."""
    _hc_to_stage = {
        "1-10":    "Pre-Seed",
        "11-50":   "Seed",
        "51-200":  "Series A",
        "201-500": "Series B",
    }
    return _hc_to_stage.get(headcount_range, "Seed")


def _normalise_company(raw: dict) -> CompanyProfile:
    """
    Map the Crustdata /screener/company/search API payload to CompanyProfile.

    Actual Crustdata response fields (discovered via live API probe):
        name, description, linkedin_company_id, website, industry,
        founded_year, headquarters.country, employee_count,
        employee_count_range, specialties, revenue_range, logo_urls
    """
    # Geography: headquarters.country → fallback to top-level location/country
    hq = raw.get("headquarters") or {}
    geography = (
        hq.get("country")
        or hq.get("city")
        or raw.get("location")
        or raw.get("country")
        or raw.get("hq_country")
        or ""
    )

    # Signals: specialties list + recent_news headlines + tags
    signals: list[str] = []
    for spec in (raw.get("specialties") or [])[:5]:
        if isinstance(spec, str) and spec:
            signals.append(spec)
        elif isinstance(spec, dict):
            s = spec.get("name") or spec.get("value") or ""
            if s:
                signals.append(s)
    for item in (raw.get("recent_news") or [])[:3]:
        headline = item.get("title") or item.get("headline") or ""
        if headline:
            signals.append(headline)
    for tag in (raw.get("tags") or [])[:3]:
        if isinstance(tag, str) and tag and tag not in signals:
            signals.append(tag)

    # Employee count: prefer integer field, fall back to parsing range
    employee_raw = raw.get("employee_count") or raw.get("headcount") or 0
    try:
        employee_count = int(employee_raw)
    except (ValueError, TypeError):
        employee_count = 0

    # Funding stage: use explicit field if present; derive from headcount range otherwise
    stage_raw = (
        raw.get("funding_stage")
        or raw.get("last_funding_stage")
        or raw.get("latest_funding_stage")
        or ""
    )
    if stage_raw:
        funding_stage = _normalise_stage(stage_raw)
    else:
        funding_stage = _stage_from_headcount(raw.get("employee_count_range") or "")

    # Company ID: linkedin_company_id is the canonical Crustdata identifier
    company_id = str(
        raw.get("linkedin_company_id")
        or raw.get("id")
        or raw.get("company_id")
        or ""
    )

    return CompanyProfile(
        id=company_id,
        name=raw.get("name") or raw.get("company_name") or "",
        description=raw.get("description") or raw.get("short_description") or "",
        industry=raw.get("industry") or raw.get("sector") or "",
        funding_stage=funding_stage,
        employee_count=employee_count,
        website=raw.get("website") or "",
        linkedin_url=(
            raw.get("linkedin_url")
            or (f"https://linkedin.com/company/{company_id}" if company_id else "")
        ),
        geography=geography,
        founded=int(raw.get("founded_year") or raw.get("founded") or 0),
        signals=signals,
        _raw=raw,
    )


def _normalise_person(raw: dict) -> PersonProfile:
    """
    Map a Crustdata people-search profile to PersonProfile.

    Crustdata field names:
        full_name, current_title, linkedin_url, past_companies
    """
    past = [
        p.get("company_name") or p.get("name") or ""
        for p in (raw.get("past_companies") or [])[:2]
    ]
    background_parts = [raw.get("current_title") or ""]
    if past:
        background_parts.append("prev: " + ", ".join(p for p in past if p))

    return PersonProfile(
        name=raw.get("full_name") or raw.get("name") or "",
        title=raw.get("current_title") or "",
        linkedin_url=raw.get("linkedin_url") or "",
        background=" | ".join(b for b in background_parts if b),
    )


def _normalise_stage(raw: str) -> str:
    """Map Crustdata funding stage strings to our enum values."""
    _stage_map = {
        "pre_seed": "Pre-Seed",
        "pre-seed": "Pre-Seed",
        "preseed": "Pre-Seed",
        "seed": "Seed",
        "series_a": "Series A",
        "series a": "Series A",
        "seriesa": "Series A",
        "series_b": "Series B",
        "series b": "Series B",
        "seriesb": "Series B",
        "series_c": "Series C+",
        "series c": "Series C+",
        "growth": "Series C+",
    }
    key = raw.lower().strip()
    return _stage_map.get(key, raw.title() if raw else "Seed")


# ── Mock data ─────────────────────────────────────────────────────────────────

_MOCK_COMPANIES: list[CompanyProfile] = [
    CompanyProfile(
        id="devflow_ai",
        name="DevFlow AI",
        description="AI-native code review platform that understands PR context at the repo level. Helps engineering teams ship faster with fewer regressions.",
        industry="Developer Tools",
        funding_stage="Seed",
        employee_count=18,
        website="https://devflow.ai",
        geography="US",
        founded=2022,
        founders=[
            PersonProfile(name="Alex Chen", title="CEO & Co-founder", background="CEO & Co-founder | prev: Google Brain, Stanford PhD"),
            PersonProfile(name="Sara Kim", title="CTO & Co-founder", background="CTO & Co-founder | prev: GitHub, Stripe"),
        ],
        signals=[
            "AI-native code review with PR-level context",
            "Seed round led by Gradient Ventures ($3M)",
            "SOC2 Type II certified",
            "4x YoY revenue growth",
            "45 paying enterprise customers",
        ],
    ),
    CompanyProfile(
        id="stackpilot",
        name="StackPilot",
        description="Infrastructure observability platform built for AI workloads. Gives MLOps teams real-time cost attribution and anomaly detection across GPU clusters.",
        industry="Developer Tools",
        funding_stage="Series A",
        employee_count=42,
        website="https://stackpilot.io",
        geography="US",
        founded=2021,
        founders=[
            PersonProfile(name="Marcus Webb", title="CEO", background="CEO | prev: Datadog (Staff Eng), MIT"),
            PersonProfile(name="Jin Park", title="CTO", background="CTO | prev: Cloudflare, UC Berkeley"),
        ],
        signals=[
            "Series A ($12M) led by Sequoia",
            "$3.1M ARR, 2.5x YoY",
            "120 customers including 3 unicorns",
            "Integrates with all major cloud GPU providers",
            "Named Gartner Cool Vendor 2024",
        ],
    ),
    CompanyProfile(
        id="revenueai",
        name="RevenueAI",
        description="AI-powered revenue forecasting and pipeline intelligence for SaaS CFOs. Connects to CRM, billing, and product usage data to predict churn and expansion.",
        industry="B2B SaaS",
        funding_stage="Seed",
        employee_count=12,
        website="https://revenueai.co",
        geography="US",
        founded=2023,
        founders=[
            PersonProfile(name="Diana Osei", title="CEO", background="CEO | prev: Stripe (Revenue products), Wharton MBA"),
            PersonProfile(name="Tom Nguyen", title="CTO", background="CTO | prev: Palantir (ML lead)"),
        ],
        signals=[
            "Seed round ($2M) from First Round Capital",
            "$600K ARR, 22 customers",
            "Net revenue retention >120%",
            "Integrates with Salesforce, HubSpot, Stripe",
            "AI forecasting accuracy 94% vs industry avg 71%",
        ],
    ),
    CompanyProfile(
        id="clarityhq",
        name="ClarityHQ",
        description="AI compliance management platform for European fintech companies navigating DORA, PSD2, and AML regulations. Automates evidence collection and audit trails.",
        industry="Vertical SaaS",
        funding_stage="Pre-Seed",
        employee_count=6,
        website="https://clarityhq.eu",
        geography="EU",
        founded=2023,
        founders=[
            PersonProfile(name="Lena Brandt", title="CEO", background="CEO | prev: N26 (Compliance lead), EBA regulator"),
            PersonProfile(name="Radu Ionescu", title="CTO", background="CTO | prev: Revolut (Engineering)"),
        ],
        signals=[
            "Pre-Seed €800K from Seedcamp",
            "5 pilot customers (EU neobanks)",
            "First-mover in DORA compliance automation",
            "Regulatory co-design with BaFin advisor",
            "Strong founder-market fit (ex-regulator)",
        ],
    ),
    CompanyProfile(
        id="meshnet_ai",
        name="MeshNet AI",
        description="Distributed GPU orchestration platform for cost-efficient AI inference. Routes workloads across cloud and on-prem clusters to minimise latency and cost.",
        industry="Infrastructure",
        funding_stage="Series A",
        employee_count=55,
        website="https://meshnet.ai",
        geography="US",
        founded=2021,
        founders=[
            PersonProfile(name="Priya Nair", title="CEO", background="CEO | prev: AWS (Distributed Systems, Principal Eng)"),
            PersonProfile(name="David Osei", title="CTO", background="CTO | prev: Meta AI Infrastructure, Caltech"),
        ],
        signals=[
            "Series A ($15M) led by a16z",
            "$4.2M ARR, 3x YoY",
            "60% cost reduction vs direct GPU rental",
            "Partnerships with AWS, GCP, CoreWeave",
            "18 enterprise customers including 2 AI labs",
        ],
    ),
    CompanyProfile(
        id="legacybridge",
        name="LegacyBridge",
        description="LLM-powered modernisation platform that translates COBOL and mainframe logic into modern microservices. Targets large financial institutions and insurers.",
        industry="Enterprise Software",
        funding_stage="Seed",
        employee_count=24,
        website="https://legacybridge.io",
        geography="US",
        founded=2022,
        founders=[
            PersonProfile(name="Robert Falk", title="CEO", background="CEO | prev: IBM Mainframe (20 yrs), MIT CSAIL"),
            PersonProfile(name="Aisha Mensah", title="CPO", background="CPO | prev: Accenture (FS transformation lead)"),
        ],
        signals=[
            "Seed ($4M) from Bessemer Venture Partners",
            "$1.1M ARR, 8 Fortune 500 customers",
            "Average deal size $140K ACV",
            "Reduces migration time by 70% vs manual rewrite",
            "JP Morgan and MetLife pilot programmes active",
        ],
    ),
]


def _mock_search(keyword: str) -> list[CompanyProfile]:
    """
    Return mock companies whose name, description, industry, or signals
    contain the keyword (case-insensitive, accent-folded).
    Always returns at least 2 results so the UI has something to show.
    """
    kw = _fold(keyword)

    def score(c: CompanyProfile) -> int:
        haystack = " ".join([
            c.name, c.description, c.industry, c.funding_stage,
            *c.signals,
        ])
        return sum(1 for word in kw.split() if word in _fold(haystack))

    ranked = sorted(_MOCK_COMPANIES, key=score, reverse=True)
    # Always include at least 2 even if score is 0
    hits = [c for c in ranked if score(c) > 0]
    return hits if len(hits) >= 2 else ranked[:4]


def _mock_by_id(company_id: str) -> CompanyProfile | None:
    for c in _MOCK_COMPANIES:
        if c.id == company_id:
            return c
    return None


def _fold(text: str) -> str:
    """Lowercase + strip accents for fuzzy matching."""
    normalised = unicodedata.normalize("NFD", text.lower())
    return re.sub(r"[^\x00-\x7f]", "", normalised)
