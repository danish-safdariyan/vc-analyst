// ── Shared ────────────────────────────────────────────────────────────────────

export interface FounderInfo {
  name: string;
  background: string;
}

export interface StartupMetrics {
  arr?: string | null;
  growth?: string | null;
  customers?: number | null;
  team_size?: number | null;
}

// ── Startup ───────────────────────────────────────────────────────────────────

export interface StartupRecord {
  id: string;
  name: string;
  website: string;
  founded: number;
  stage: string;
  sector: string;
  geography: string;
  description: string;
  founders: FounderInfo[];
  metrics: StartupMetrics;
  signals: string[];
  last_updated: string;
  original_narrative?: string | null;
}

// ── Thesis ────────────────────────────────────────────────────────────────────

export interface ParsedThesis {
  raw: string;
  sectors: string[];
  stages: string[];
  geographies: string[];
  signals: string[];
  anti_patterns: string[];
  market_type: string;
  founder_profile: string[];
  signal_preferences: string[];
}

// ── Scoring ───────────────────────────────────────────────────────────────────

export interface FitDimensions {
  sector_fit: number;
  stage_fit: number;
  team_fit: number;
  signal_strength: number;
  market_reasoning: number;
}

export interface StartupWithScore extends StartupRecord {
  fit_score: number;
  explanation: string;
  fit_dimensions: FitDimensions;
}

// ── Memo ──────────────────────────────────────────────────────────────────────

export interface MemoSections {
  startup_summary: string;
  why_it_matches: string;
  bull_case: string;
  bear_case: string;
  key_signals: string[];
  next_step: string;
  recommendation: "Pass" | "Take Meeting" | "Fast Track";
}

export interface InvestmentMemo {
  startup_id: string;
  startup_name: string;
  generated_at: string;
  sections: MemoSections;
}

// ── Drift ─────────────────────────────────────────────────────────────────────

export interface DriftSignal {
  dimension: string;
  original: string;
  current: string;
  drift_score: number;
  severity: "none" | "low" | "medium" | "high";
  evidence: string[];
  note: string;
}

export interface DriftReport {
  startup_id: string;
  checked_at: string;
  status: "Stable" | "Watch" | "Drift Risk";
  overall_drift: number;
  signals: DriftSignal[];
  summary: string;
}

// ── Orchestrator ──────────────────────────────────────────────────────────────

export interface StepTrace {
  step_id: string;
  status: "ok" | "error" | "skipped";
  duration_ms: number;
  error?: string | null;
}

export interface VCAnalysisResult {
  thesis: ParsedThesis;
  candidates: StartupWithScore[];
  best_startup: StartupWithScore | null;
  memo: InvestmentMemo | null;
  drift_report: DriftReport | null;
  pipeline_trace: StepTrace[];
}

// ── API response wrappers ─────────────────────────────────────────────────────

export interface AnalyzeResponse {
  result: VCAnalysisResult;
}

export interface ChatApiResponse {
  reply: string;
  used_mock: boolean;
}
