/**
 * Demo fixture — mirrors backend app/services/demo_fixtures.py
 *
 * Used when NEXT_PUBLIC_DEMO_MODE=true so the UI works completely
 * offline (no backend required).
 */

import type { VCAnalysisResult } from "./types";

export const DEMO_RESULT: VCAnalysisResult = {
  thesis: {
    raw: "Pre-seed developer tools startups with strong technical founders.",
    sectors: ["Developer Tools"],
    stages: ["Pre-Seed", "Seed"],
    geographies: ["US"],
    market_type: "B2B",
    founder_profile: ["technical founders", "ex-FAANG", "strong engineering background"],
    signal_preferences: ["developer-led growth", "strong technical moat", "early enterprise traction"],
    signals: ["developer-led growth", "strong technical moat", "early enterprise traction"],
    anti_patterns: ["consumer apps", "hardware"],
  },

  candidates: [
    {
      id: "devflow_ai",
      name: "DevFlow AI",
      stage: "Seed",
      sector: "Developer Tools",
      geography: "US",
      description:
        "AI-native code review platform that understands PR context at the repo level. Helps engineering teams ship faster with fewer regressions by surfacing deep semantic issues human reviewers miss.",
      website: "https://devflow.ai",
      founded: 2022,
      founders: [
        { name: "Alex Chen", background: "CEO & Co-founder | ex-Google Brain, Stanford PhD CS" },
        { name: "Sara Kim", background: "CTO & Co-founder | ex-GitHub Staff Eng, ex-Stripe" },
      ],
      metrics: { arr: "$420K", growth: "4x YoY", customers: 45, team_size: 18 },
      signals: [
        "Seed round ($3M) led by Gradient Ventures",
        "SOC2 Type II certified",
        "4x YoY revenue growth",
        "45 paying enterprise customers",
        "Developer NPS of 72 — top decile for B2B dev tools",
      ],
      last_updated: "",
      original_narrative:
        "DevFlow AI is building developer tooling that reduces engineering toil for modern software teams.",
      fit_score: 87,
      explanation:
        "DevFlow AI is a textbook thesis match: Developer Tools sector, Seed stage, and a deeply technical founding team (ex-Google Brain PhD + ex-GitHub Staff Eng). 4x YoY growth and 45 enterprise customers signal strong early PMF. Developer-led adoption and SOC2 directly match the fund's signal preferences.",
      fit_dimensions: {
        sector_fit: 95,
        stage_fit: 90,
        team_fit: 92,
        signal_strength: 82,
        market_reasoning: 78,
      },
    },
    {
      id: "stackpilot",
      name: "StackPilot",
      stage: "Series A",
      sector: "Developer Tools",
      geography: "US",
      description:
        "Infrastructure observability platform built for AI workloads. Gives MLOps teams real-time cost attribution and anomaly detection across GPU clusters.",
      website: "https://stackpilot.io",
      founded: 2021,
      founders: [
        { name: "Marcus Webb", background: "CEO | ex-Datadog Staff Eng, MIT" },
        { name: "Jin Park", background: "CTO | ex-Cloudflare, UC Berkeley" },
      ],
      metrics: { arr: "$3.1M", growth: "2.5x YoY", customers: 120, team_size: 42 },
      signals: [
        "Series A ($12M) led by Sequoia",
        "$3.1M ARR — 2.5x YoY",
        "120 customers including 3 unicorns",
        "Named Gartner Cool Vendor 2024",
      ],
      last_updated: "",
      fit_score: 71,
      explanation:
        "Strong sector fit and technical team, but Series A stage falls outside the Pre-Seed/Seed thesis sweet spot. Valuation expectations will be stretched at this stage in the observability category.",
      fit_dimensions: {
        sector_fit: 90,
        stage_fit: 55,
        team_fit: 82,
        signal_strength: 75,
        market_reasoning: 68,
      },
    },
    {
      id: "revenueai",
      name: "RevenueAI",
      stage: "Seed",
      sector: "B2B SaaS",
      geography: "US",
      description:
        "AI-powered revenue forecasting and pipeline intelligence for SaaS CFOs. Connects to CRM, billing, and product usage data to predict churn and expansion.",
      website: "https://revenueai.co",
      founded: 2023,
      founders: [
        { name: "Diana Osei", background: "CEO | ex-Stripe Revenue Products, Wharton MBA" },
        { name: "Tom Nguyen", background: "CTO | ex-Palantir ML Lead" },
      ],
      metrics: { arr: "$600K", growth: "3x YoY", customers: 22, team_size: 12 },
      signals: [
        "Seed round ($2M) from First Round Capital",
        "$600K ARR — 22 customers",
        "Net revenue retention >120%",
        "AI forecast accuracy 94% vs 71% industry avg",
      ],
      last_updated: "",
      fit_score: 62,
      explanation:
        "Right stage and strong retention metrics, but the sector is B2B SaaS finance tooling — a stretch from the core Developer Tools thesis. De-risk with a sector-fit conversation before moving forward.",
      fit_dimensions: {
        sector_fit: 55,
        stage_fit: 88,
        team_fit: 70,
        signal_strength: 65,
        market_reasoning: 60,
      },
    },
    {
      id: "clarityhq",
      name: "ClarityHQ",
      stage: "Pre-Seed",
      sector: "Vertical SaaS",
      geography: "EU",
      description:
        "AI compliance management platform for European fintech companies navigating DORA, PSD2, and AML regulations. Automates evidence collection and audit trails.",
      website: "https://clarityhq.eu",
      founded: 2023,
      founders: [
        { name: "Lena Brandt", background: "CEO | ex-N26 Compliance Lead, ex-EBA regulator" },
        { name: "Radu Ionescu", background: "CTO | ex-Revolut Engineering" },
      ],
      metrics: { customers: 5, team_size: 6 },
      signals: [
        "Pre-Seed €800K from Seedcamp",
        "5 EU neobank pilot customers",
        "First-mover in DORA compliance automation",
      ],
      last_updated: "",
      fit_score: 48,
      explanation:
        "Stage is ideal but the sector (compliance/regtech) and geography (EU) fall outside the thesis target. Pass for this thesis; flag for any EU regtech mandate.",
      fit_dimensions: {
        sector_fit: 40,
        stage_fit: 92,
        team_fit: 58,
        signal_strength: 40,
        market_reasoning: 45,
      },
    },
    {
      id: "meshnet_ai",
      name: "MeshNet AI",
      stage: "Series A",
      sector: "Infrastructure",
      geography: "US",
      description:
        "Distributed GPU orchestration platform for cost-efficient AI inference. Routes workloads across cloud and on-prem clusters to minimise latency and cost.",
      website: "https://meshnet.ai",
      founded: 2021,
      founders: [
        { name: "Priya Nair", background: "CEO | ex-AWS Distributed Systems Principal Eng" },
        { name: "David Osei", background: "CTO | ex-Meta AI Infrastructure, Caltech" },
      ],
      metrics: { arr: "$4.2M", growth: "3x YoY", customers: 18, team_size: 55 },
      signals: [
        "Series A ($15M) led by a16z",
        "$4.2M ARR — 3x YoY",
        "60% cost reduction vs direct GPU rental",
        "18 enterprise customers including 2 AI labs",
      ],
      last_updated: "",
      fit_score: 44,
      explanation:
        "World-class technical founders but Stage (Series A, $15M raised) and price point are well outside the Pre-Seed/Seed mandate. Keep on the radar for portfolio GPU infrastructure partnerships.",
      fit_dimensions: {
        sector_fit: 50,
        stage_fit: 42,
        team_fit: 80,
        signal_strength: 45,
        market_reasoning: 38,
      },
    },
  ],

  best_startup: null, // resolved below

  memo: {
    startup_id: "devflow_ai",
    startup_name: "DevFlow AI",
    generated_at: new Date().toISOString(),
    sections: {
      startup_summary:
        "DevFlow AI is an AI-native code review platform that provides PR-level semantic context, helping engineering teams ship 30% faster with fewer regressions. Founded by Alex Chen (ex-Google Brain PhD) and Sara Kim (ex-GitHub Staff Eng), the company has reached $420K ARR with 45 paying enterprise customers after 18 months.",
      why_it_matches:
        "DevFlow is a precision fit: Developer Tools sector (95/100), Seed stage within the Pre-Seed/Seed mandate, and a founding team with the rare combination of deep ML research (Google Brain PhD) and platform-scale engineering experience (GitHub, Stripe). The 4x YoY growth and developer-led adoption pattern directly match the fund's signal preferences.",
      bull_case:
        "The AI code review market is nascent but growing fast — every engineering team of 5+ is a prospect. DevFlow's semantic PR understanding creates a data moat (each review improves the model) that widens with scale. At $420K ARR growing 4x, a $3-4M Seed check could fuel the Series A milestone in 18 months at 5-10x revenue multiple.",
      bear_case:
        "1. GitHub Copilot and Amazon CodeWhisperer could enter code review with platform distribution advantages. 2. Enterprise AI-in-the-loop security reviews are lengthening sales cycles. 3. Differentiation from Sourcegraph, CodeClimate, and Reviewpad needs continuous sharpening as the category matures.",
      key_signals: [
        "$420K ARR — 4x YoY growth in 18 months post-launch",
        "Developer NPS 72 — top decile for B2B developer tools",
        "SOC2 Type II certified — enterprise sales friction removed",
        "45 paying enterprise customers — strong early PMF signal",
        "Seed round led by Gradient Ventures (Google's AI fund) — validates AI moat",
        "ex-Google Brain PhD + ex-GitHub Staff Eng — rare founder pairing",
      ],
      next_step:
        "Move quickly — schedule a 45-minute technical deep-dive with Alex and Sara this week to stress-test the AI moat narrative and request access to their data room before the round fills.",
      recommendation: "Fast Track",
    },
  },

  drift_report: {
    startup_id: "devflow_ai",
    checked_at: new Date().toISOString(),
    status: "Stable",
    overall_drift: 14,
    signals: [
      {
        dimension: "Message Consistency",
        original: "AI-native code review that understands PR context at the repo level",
        current: "AI-native code review with PR-level semantic context",
        drift_score: 8,
        severity: "none",
        evidence: [
          "Core positioning unchanged: 'AI-native code review' in all channels",
          "Target buyer (engineering teams) consistent across website and outreach",
          "Minor wording update: 'repo-level' → 'semantic context' (clarification, not pivot)",
        ],
        note: "Messaging evolution is tightening the value prop, not changing it.",
      },
      {
        dimension: "Hiring Alignment",
        original: "Deep ML and platform engineering team — Google Brain, GitHub, Stripe pedigree",
        current: "Recent JDs: Senior ML Engineer (LLM fine-tuning), Staff Backend Eng (data pipeline)",
        drift_score: 12,
        severity: "none",
        evidence: [
          "ML hiring reinforces core product: LLM fine-tuning aligns with AI moat narrative",
          "Backend data-pipeline hire supports the model-improvement flywheel",
          "No GTM or sales-engineer hires yet — still founder-led sales (expected at Seed)",
        ],
        note: "Hiring directly reinforces the original technical thesis.",
      },
      {
        dimension: "Product Alignment",
        original: "Code review automation — PR context understanding",
        current: "New features: automated test generation, AI-assisted PR description drafting",
        drift_score: 22,
        severity: "low",
        evidence: [
          "Test generation is adjacent to code review — same buyer, same workflow",
          "PR description drafting is table-stakes for AI dev tool competitors",
          "No evidence of pivot toward CI/CD orchestration or deployment tooling",
        ],
        note: "Slight scope expansion is normal at Seed — watch for GTM confusion if >2 non-review features added in next 6 months.",
      },
      {
        dimension: "Contradictions",
        original: "Focused on 'PR review quality' as the primary value lever",
        current: "Website now leads with 'ship faster' — speed over quality framing",
        drift_score: 18,
        severity: "low",
        evidence: [
          "Speed and quality are complementary for code review — not contradictory",
          "Buyer feedback likely driving the messaging shift (EMs care about velocity)",
          "The AI model still surfaces semantic issues — core function unchanged",
        ],
        note: "Message reframing from 'quality' to 'velocity' is buyer-driven and defensible.",
      },
    ],
    summary:
      "DevFlow AI shows Stable drift at 14/100. The core positioning and hiring remain tightly aligned with the original narrative. The minor product scope expansion and velocity-first messaging reframe are both buyer-driven and expected at Seed. No red flags — continue to monitor product breadth over the next 2 quarters.",
  },

  pipeline_trace: [
    { step_id: "parse_thesis",      status: "ok", duration_ms: 0 },
    { step_id: "discover_startups", status: "ok", duration_ms: 0 },
    { step_id: "score_startups",    status: "ok", duration_ms: 0 },
    { step_id: "generate_memo",     status: "ok", duration_ms: 0 },
    { step_id: "check_drift",       status: "ok", duration_ms: 0 },
  ],
};

// Resolve best_startup reference
DEMO_RESULT.best_startup = DEMO_RESULT.candidates[0];

/** Return a copy of the demo result with the user's thesis text substituted in. */
export function buildDemoResult(thesisInput: string): VCAnalysisResult {
  return {
    ...DEMO_RESULT,
    thesis: { ...DEMO_RESULT.thesis, raw: thesisInput || DEMO_RESULT.thesis.raw },
    memo: DEMO_RESULT.memo
      ? { ...DEMO_RESULT.memo, generated_at: new Date().toISOString() }
      : null,
    drift_report: DEMO_RESULT.drift_report
      ? { ...DEMO_RESULT.drift_report, checked_at: new Date().toISOString() }
      : null,
  };
}
