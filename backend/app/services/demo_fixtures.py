"""
Demo Fixtures
─────────────
Pre-baked, high-quality VCAnalysisResult for the demo thesis:
  "Pre-seed developer tools startups with strong technical founders."

Used by the orchestrator when USE_MOCK=true (no real API keys present)
so the full pipeline still produces impressive, realistic output.

The fixture is keyed to DevFlow AI as the best match.
"""

from datetime import datetime, timezone

from app.schemas.models import (
    DriftReport,
    DriftSignal,
    FitDimensions,
    FounderInfo,
    InvestmentMemo,
    MemoSections,
    ParsedThesis,
    StartupMetrics,
    StartupWithScore,
    StepTrace,
    VCAnalysisResult,
)

# ── Demo thesis ───────────────────────────────────────────────────────────────

DEMO_PARSED_THESIS = ParsedThesis(
    raw="Pre-seed developer tools startups with strong technical founders.",
    sectors=["Developer Tools"],
    stages=["Pre-Seed", "Seed"],
    geographies=["US"],
    market_type="B2B",
    founder_profile=["technical founders", "ex-FAANG", "strong engineering background"],
    signal_preferences=["developer-led growth", "strong technical moat", "early enterprise traction"],
    signals=["developer-led growth", "strong technical moat", "early enterprise traction"],
    anti_patterns=["consumer apps", "hardware"],
)

# ── Demo candidates (5 scored startups) ──────────────────────────────────────

def _make_candidate(
    id: str,
    name: str,
    stage: str,
    sector: str,
    geography: str,
    description: str,
    website: str,
    founded: int,
    founders: list[FounderInfo],
    metrics: StartupMetrics,
    signals: list[str],
    fit_score: float,
    dims: FitDimensions,
    explanation: str,
) -> StartupWithScore:
    return StartupWithScore(
        id=id,
        name=name,
        stage=stage,
        sector=sector,
        geography=geography,
        description=description,
        website=website,
        founded=founded,
        founders=founders,
        metrics=metrics,
        signals=signals,
        last_updated="",
        original_narrative=(
            f"{name} is building developer tooling that reduces engineering toil "
            f"for modern software teams. The founding vision is a world where developers "
            f"spend >80% of their time on product logic rather than infra and process."
        ),
        fit_score=fit_score,
        explanation=explanation,
        fit_dimensions=dims,
    )


DEMO_CANDIDATES: list[StartupWithScore] = [
    _make_candidate(
        id="devflow_ai",
        name="DevFlow AI",
        stage="Seed",
        sector="Developer Tools",
        geography="US",
        description=(
            "AI-native code review platform that understands PR context at the repo level. "
            "Helps engineering teams ship faster with fewer regressions by surfacing "
            "deep semantic issues human reviewers miss."
        ),
        website="https://devflow.ai",
        founded=2022,
        founders=[
            FounderInfo(name="Alex Chen", background="CEO & Co-founder | ex-Google Brain, Stanford PhD CS"),
            FounderInfo(name="Sara Kim", background="CTO & Co-founder | ex-GitHub Staff Eng, ex-Stripe"),
        ],
        metrics=StartupMetrics(arr="$420K", growth="4x YoY", customers=45, team_size=18),
        signals=[
            "Seed round ($3M) led by Gradient Ventures",
            "SOC2 Type II certified",
            "4x YoY revenue growth",
            "45 paying enterprise customers",
            "AI-native code review with PR-level semantic context",
            "Developer NPS of 72 — top decile for B2B dev tools",
        ],
        fit_score=87.0,
        dims=FitDimensions(
            sector_fit=95.0,
            stage_fit=90.0,
            team_fit=92.0,
            signal_strength=82.0,
            market_reasoning=78.0,
        ),
        explanation=(
            "DevFlow AI is a textbook thesis match: Developer Tools sector, Seed stage, "
            "and a deeply technical founding team (ex-Google Brain PhD + ex-GitHub Staff Eng). "
            "4x YoY growth and 45 enterprise customers signal strong early PMF. "
            "The developer-led adoption pattern and SOC2 certification reduce enterprise "
            "sales friction — exactly the signal preferences the fund values."
        ),
    ),
    _make_candidate(
        id="stackpilot",
        name="StackPilot",
        stage="Series A",
        sector="Developer Tools",
        geography="US",
        description=(
            "Infrastructure observability platform built for AI workloads. "
            "Gives MLOps teams real-time cost attribution and anomaly detection "
            "across GPU clusters."
        ),
        website="https://stackpilot.io",
        founded=2021,
        founders=[
            FounderInfo(name="Marcus Webb", background="CEO | ex-Datadog Staff Eng, MIT"),
            FounderInfo(name="Jin Park", background="CTO | ex-Cloudflare, UC Berkeley"),
        ],
        metrics=StartupMetrics(arr="$3.1M", growth="2.5x YoY", customers=120, team_size=42),
        signals=[
            "Series A ($12M) led by Sequoia",
            "$3.1M ARR — 2.5x YoY",
            "120 customers including 3 unicorns",
            "Named Gartner Cool Vendor 2024",
        ],
        fit_score=71.0,
        dims=FitDimensions(
            sector_fit=90.0,
            stage_fit=55.0,
            team_fit=82.0,
            signal_strength=75.0,
            market_reasoning=68.0,
        ),
        explanation=(
            "Strong sector fit and technical team, but Series A stage falls outside the "
            "Pre-Seed/Seed thesis sweet spot. The observability category is crowded at "
            "Series A — valuation expectations will be stretched. Worth monitoring for "
            "earlier-stage spinouts from this team."
        ),
    ),
    _make_candidate(
        id="revenueai",
        name="RevenueAI",
        stage="Seed",
        sector="B2B SaaS",
        geography="US",
        description=(
            "AI-powered revenue forecasting and pipeline intelligence for SaaS CFOs. "
            "Connects to CRM, billing, and product usage data to predict churn and expansion."
        ),
        website="https://revenueai.co",
        founded=2023,
        founders=[
            FounderInfo(name="Diana Osei", background="CEO | ex-Stripe Revenue Products, Wharton MBA"),
            FounderInfo(name="Tom Nguyen", background="CTO | ex-Palantir ML Lead"),
        ],
        metrics=StartupMetrics(arr="$600K", growth="3x YoY", customers=22, team_size=12),
        signals=[
            "Seed round ($2M) from First Round Capital",
            "$600K ARR — 22 customers",
            "Net revenue retention >120%",
            "AI forecast accuracy 94% vs 71% industry avg",
        ],
        fit_score=62.0,
        dims=FitDimensions(
            sector_fit=55.0,
            stage_fit=88.0,
            team_fit=70.0,
            signal_strength=65.0,
            market_reasoning=60.0,
        ),
        explanation=(
            "Right stage and strong retention metrics, but the sector is B2B SaaS "
            "finance tooling — a stretch from the core Developer Tools thesis. "
            "The CTO's ML background is a plus. De-risk with a quick sector-fit "
            "conversation before moving forward."
        ),
    ),
    _make_candidate(
        id="clarityhq",
        name="ClarityHQ",
        stage="Pre-Seed",
        sector="Vertical SaaS",
        geography="EU",
        description=(
            "AI compliance management platform for European fintech companies "
            "navigating DORA, PSD2, and AML regulations. Automates evidence "
            "collection and audit trails."
        ),
        website="https://clarityhq.eu",
        founded=2023,
        founders=[
            FounderInfo(name="Lena Brandt", background="CEO | ex-N26 Compliance Lead, ex-EBA regulator"),
            FounderInfo(name="Radu Ionescu", background="CTO | ex-Revolut Engineering"),
        ],
        metrics=StartupMetrics(customers=5, team_size=6),
        signals=[
            "Pre-Seed €800K from Seedcamp",
            "5 EU neobank pilot customers",
            "First-mover in DORA compliance automation",
            "Regulatory co-design with BaFin advisor",
        ],
        fit_score=48.0,
        dims=FitDimensions(
            sector_fit=40.0,
            stage_fit=92.0,
            team_fit=58.0,
            signal_strength=40.0,
            market_reasoning=45.0,
        ),
        explanation=(
            "Stage is ideal but the sector (compliance/regtech) and geography (EU) fall "
            "outside the thesis target. Founder-market fit is exceptional for fintech "
            "compliance specifically. Pass for this thesis; flag for any EU regtech mandate."
        ),
    ),
    _make_candidate(
        id="meshnet_ai",
        name="MeshNet AI",
        stage="Series A",
        sector="Infrastructure",
        geography="US",
        description=(
            "Distributed GPU orchestration platform for cost-efficient AI inference. "
            "Routes workloads across cloud and on-prem clusters to minimise latency and cost."
        ),
        website="https://meshnet.ai",
        founded=2021,
        founders=[
            FounderInfo(name="Priya Nair", background="CEO | ex-AWS Distributed Systems Principal Eng"),
            FounderInfo(name="David Osei", background="CTO | ex-Meta AI Infrastructure, Caltech"),
        ],
        metrics=StartupMetrics(arr="$4.2M", growth="3x YoY", customers=18, team_size=55),
        signals=[
            "Series A ($15M) led by a16z",
            "$4.2M ARR — 3x YoY",
            "60% cost reduction vs direct GPU rental",
            "18 enterprise customers including 2 AI labs",
        ],
        fit_score=44.0,
        dims=FitDimensions(
            sector_fit=50.0,
            stage_fit=42.0,
            team_fit=80.0,
            signal_strength=45.0,
            market_reasoning=38.0,
        ),
        explanation=(
            "World-class technical founders (ex-AWS, ex-Meta AI Infra) but the stage "
            "(Series A, $15M raised) and price point are well outside the Pre-Seed/Seed "
            "mandate. Strong team to keep on the radar for follow-on checks in portfolio "
            "companies that need GPU infrastructure partnerships."
        ),
    ),
]

# ── Demo investment memo (for DevFlow AI) ────────────────────────────────────

DEMO_MEMO = InvestmentMemo(
    startup_id="devflow_ai",
    startup_name="DevFlow AI",
    generated_at=datetime.now(timezone.utc).isoformat(),
    sections=MemoSections(
        startup_summary=(
            "DevFlow AI is an AI-native code review platform that provides PR-level "
            "semantic context, helping engineering teams ship 30% faster with fewer "
            "regressions. Founded by Alex Chen (ex-Google Brain PhD) and Sara Kim "
            "(ex-GitHub Staff Eng), the company has reached $420K ARR with 45 paying "
            "enterprise customers after 18 months."
        ),
        why_it_matches=(
            "DevFlow is a precision fit for the thesis: Developer Tools sector (95/100), "
            "Seed stage within the Pre-Seed/Seed mandate, and a founding team with the "
            "rare combination of deep ML research (Google Brain PhD) and platform-scale "
            "engineering experience (GitHub, Stripe). The 4x YoY revenue growth and "
            "developer-led adoption pattern directly match the fund's signal preferences."
        ),
        bull_case=(
            "The AI code review market is nascent but growing fast — every engineering "
            "team running more than 5 engineers is a prospect. DevFlow's semantic PR "
            "understanding creates a data moat (each review improves the model) that "
            "widens with scale. At $420K ARR growing 4x, a $3-4M Seed check could "
            "fuel the Series A milestone in 18 months at 5-10x revenue multiple."
        ),
        bear_case=(
            "1. GitHub Copilot and Amazon CodeWhisperer are obvious acqui-hire targets "
            "that could enter code review with platform distribution advantages. "
            "2. Enterprise security reviews for AI-in-the-loop tooling are lengthening "
            "sales cycles at late-stage companies. "
            "3. Differentiation from Sourcegraph, CodeClimate, and Reviewpad needs "
            "continuous sharpening as the category matures."
        ),
        key_signals=[
            "$420K ARR — 4x YoY growth in 18 months post-launch",
            "Developer NPS 72 — top decile for B2B developer tools",
            "SOC2 Type II certified — enterprise sales friction removed",
            "45 paying enterprise customers — strong early PMF signal",
            "Seed round led by Gradient Ventures (Google's AI fund) — validates AI moat",
            "ex-Google Brain PhD + ex-GitHub Staff Eng — rare founder pairing",
        ],
        next_step=(
            "Move quickly — schedule a 45-minute technical deep-dive with Alex and Sara "
            "this week to stress-test the AI moat narrative and request access to their "
            "data room before the round fills."
        ),
        recommendation="Fast Track",
    ),
)

# ── Demo drift report (for DevFlow AI) ───────────────────────────────────────

DEMO_DRIFT = DriftReport(
    startup_id="devflow_ai",
    checked_at=datetime.now(timezone.utc).isoformat(),
    status="Stable",
    overall_drift=14.0,
    signals=[
        DriftSignal(
            dimension="Message Consistency",
            original="AI-native code review that understands PR context at the repo level",
            current="AI-native code review with PR-level semantic context",
            drift_score=8.0,
            severity="none",
            evidence=[
                "Core positioning unchanged: 'AI-native code review' in all channels",
                "Target buyer (engineering teams) consistent across website and outreach",
                "Minor wording update: 'repo-level context' → 'semantic context' (clarification, not pivot)",
            ],
            note="Messaging evolution is tightening the value prop, not changing it.",
        ),
        DriftSignal(
            dimension="Hiring Alignment",
            original="Deep ML and platform engineering team — Google Brain, GitHub, Stripe pedigree",
            current="Recent JDs: Senior ML Engineer (LLM fine-tuning), Staff Backend Eng (data pipeline)",
            drift_score=12.0,
            severity="none",
            evidence=[
                "ML hiring reinforces core product: LLM fine-tuning aligns with AI moat narrative",
                "Backend data-pipeline hire supports the model-improvement flywheel",
                "No GTM or sales-engineer hires yet — still founder-led sales (expected at Seed)",
            ],
            note="Hiring directly reinforces the original technical thesis.",
        ),
        DriftSignal(
            dimension="Product Alignment",
            original="Code review automation — PR context understanding",
            current="New features: automated test generation, AI-assisted PR description drafting",
            drift_score=22.0,
            severity="low",
            evidence=[
                "Test generation is adjacent to code review — same buyer, same workflow",
                "PR description drafting is table-stakes for AI dev tool competitors",
                "No evidence of pivot toward CI/CD orchestration or deployment tooling",
            ],
            note=(
                "Slight scope expansion is normal at Seed — watch for GTM confusion "
                "if the product adds >2 more non-review features in the next 6 months."
            ),
        ),
        DriftSignal(
            dimension="Contradictions",
            original="Focused on 'PR review quality' as the primary value lever",
            current="Website now leads with 'ship faster' — speed over quality framing",
            drift_score=18.0,
            severity="low",
            evidence=[
                "Speed and quality are complementary for code review — not contradictory",
                "Buyer feedback likely driving the messaging shift (engineering managers care about velocity)",
                "The AI model still surfaces semantic issues — core function unchanged",
            ],
            note="Message reframing from 'quality' to 'velocity' is buyer-driven and defensible.",
        ),
    ],
    summary=(
        "DevFlow AI shows Stable drift at 14/100. The core positioning and hiring remain "
        "tightly aligned with the original narrative. The minor product scope expansion "
        "(test generation, PR drafts) and velocity-first messaging reframe are both "
        "buyer-driven and expected at Seed. No red flags — continue to monitor product "
        "breadth over the next 2 quarters."
    ),
)

# ── Demo pipeline trace ───────────────────────────────────────────────────────

DEMO_TRACE: list[StepTrace] = [
    StepTrace(step_id="parse_thesis",      status="ok", duration_ms=0.0),
    StepTrace(step_id="discover_startups", status="ok", duration_ms=0.0),
    StepTrace(step_id="score_startups",    status="ok", duration_ms=0.0),
    StepTrace(step_id="generate_memo",     status="ok", duration_ms=0.0),
    StepTrace(step_id="check_drift",       status="ok", duration_ms=0.0),
]

# ── Public builder ────────────────────────────────────────────────────────────

def build_demo_result(thesis_input: str) -> VCAnalysisResult:
    """Return a complete, high-quality demo VCAnalysisResult.

    The thesis in the result reflects the user's input so the UI shows
    the actual thesis they typed, while all other data is pre-baked.
    """
    thesis = ParsedThesis(
        **{**DEMO_PARSED_THESIS.model_dump(), "raw": thesis_input or DEMO_PARSED_THESIS.raw}
    )
    memo = InvestmentMemo(
        **{**DEMO_MEMO.model_dump(), "generated_at": datetime.now(timezone.utc).isoformat()}
    )
    drift = DriftReport(
        **{**DEMO_DRIFT.model_dump(), "checked_at": datetime.now(timezone.utc).isoformat()}
    )
    return VCAnalysisResult(
        thesis=thesis,
        candidates=DEMO_CANDIDATES,
        best_startup=DEMO_CANDIDATES[0],
        memo=memo,
        drift_report=drift,
        pipeline_trace=DEMO_TRACE,
    )
