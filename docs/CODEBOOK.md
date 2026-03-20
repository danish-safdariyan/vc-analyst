# Codebook — VC Analyst AI

This document describes **users**, **data artifacts**, **variables**, and **test datasets** so the project is reproducible and easy to grade or audit.

---

## 1. Intended user and use-case

| Concept | Description |
|--------|-------------|
| **Primary user** | Venture investors (associates, principals, solo GPs) who want faster first-pass diligence. |
| **Core job-to-be-done** | Turn a short **fund thesis in natural language** into structured criteria, ranked startup ideas, a draft **investment memo**, and a **narrative drift** snapshot for monitoring. |
| **Secondary user** | Anyone using **Ask** (`/chat`) for VC-style Q&A (diligence framing, markets, metrics) powered by the same LLM stack. |
| **Inputs required** | **Minimal:** one thesis paragraph (main flow); optional API keys for live LLM/data. No spreadsheet upload required. |

---

## 2. System outputs (variables)

Outputs are produced by the FastAPI pipeline and stored in the browser (`sessionStorage`) for the results/memo/drift pages.

### 2.1 `ParsedThesis` (`result.thesis`)

| Field | Type | Description |
|-------|------|-------------|
| `raw` | string | Original thesis text submitted by the user. |
| `sectors` | string[] | Inferred sectors (e.g. `Developer Tools`, `FinTech`). |
| `stages` | string[] | Funding stages of interest (e.g. `Pre-Seed`, `Seed`). |
| `geographies` | string[] | Regions (e.g. `US`, `Europe`). |
| `signals` | string[] | Positive signals to look for. |
| `anti_patterns` | string[] | Themes to avoid. |
| `market_type` | string | e.g. `B2B`, `B2C`. |
| `founder_profile` | string[] | Desired founder traits. |
| `signal_preferences` | string[] | Traction/market signals emphasized in the thesis. |

### 2.2 `StartupRecord` / `StartupWithScore` (`result.candidates[]`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier. |
| `name` | string | Company name. |
| `website` | string | URL (may be empty in mocks). |
| `founded` | int | Year founded. |
| `stage` | string | e.g. `Pre-Seed`, `Seed`, `Series A`. |
| `sector` | string | Industry label. |
| `geography` | string | HQ or primary market. |
| `description` | string | Short company description. |
| `founders` | object[] | `{ name, background }`. |
| `metrics` | object | Optional `arr`, `growth`, `customers`, `team_size`. |
| `signals` | string[] | Bullets (funding, certifications, growth claims). |
| `last_updated` | string | Timestamp or label for data freshness. |
| `original_narrative` | string? | Baseline story used for drift analysis. |
| `fit_score` | float | **0–100** thesis fit (on scored records only). |
| `explanation` | string | Narrative justification for the score. |
| `fit_dimensions` | object | **Five** sub-scores (0–100 each): `sector_fit`, `stage_fit`, `team_fit`, `signal_strength`, `market_reasoning`. |

### 2.3 `InvestmentMemo` (`result.memo`)

| Field | Description |
|-------|-------------|
| `startup_id`, `startup_name` | Targets. |
| `generated_at` | ISO timestamp. |
| `sections` | `startup_summary`, `why_it_matches`, `bull_case`, `bear_case`, `key_signals[]`, `next_step`, `recommendation`. |

### 2.4 `DriftReport` (`result.drift_report`)

| Field | Description |
|-------|-------------|
| `startup_id` | Company analyzed. |
| `checked_at` | ISO timestamp. |
| `status` | `Stable` \| `Watch` \| `Drift Risk`. |
| `overall_drift` | 0–100 drift intensity. |
| `signals[]` | Per-dimension drift: `dimension`, `original`, `current`, `drift_score`, `severity`, `evidence[]`, `note`. |
| `summary` | Plain-language conclusion. |

### 2.5 `StepTrace` (`result.pipeline_trace[]`)

| Field | Description |
|-------|-------------|
| `step_id` | `parse_thesis`, `discover_startups`, `score_startups`, `generate_memo`, `check_drift`. |
| `status` | `ok` \| `error` \| `skipped`. |
| `duration_ms` | Step runtime. |
| `error` | Present if failed. |

---

## 3. Test dataset files (`datasets/*.json`)

Each file is **valid JSON** and intended for documentation, manual UI tests, and automated smoke tests.

| JSON key | Meaning |
|----------|---------|
| `dataset_id` | Stable slug. |
| `display_name` | Human-readable label. |
| `persona` | Intended fund/stakeholder. |
| `use_case` | What you are demonstrating. |
| `thesis_raw` | **Paste into the Thesis page** or send as `thesis` in `/api/parse-thesis` / `start-analysis`. |
| `sample_chat_prompts` | Paste into **Ask** (`/chat`) or `message` in `/api/chat`. |
| `demo_notes.mock_mode` | Behavior when `USE_MOCK=true`. |
| `demo_notes.live_mode` | Behavior when live keys and `USE_MOCK=false`. |
| `api_smoke_test` | Canonical HTTP method, path, and JSON body for `scripts/verify_datasets.py`. |

### Mock-mode caveat

When `USE_MOCK=true`, the orchestrator returns a **single high-quality fixture** (`demo_fixtures.py`): candidate companies and memo text are **shared** across all thesis strings, but `ParsedThesis.raw` matches the user’s input. This keeps demos **deterministic** offline. Datasets `02` and `03` still exercise **copy-paste flows** and **API shape**; live mode exercises thesis-specific discovery and LLM.

---

## 4. Environment variables (reproducibility)

| Variable | Location | Role |
|----------|----------|------|
| `OPENROUTER_API_KEY` | `backend/.env` | LLM calls (agents + Ask). |
| `USE_MOCK` | `backend/.env` | `true` = fixture pipeline + chat mock responses when key missing. |
| `CRUSTDATA_API_KEY` | `backend/.env` | Optional startup data; mock if empty. |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Browser/long-running calls to FastAPI (default `http://127.0.0.1:8000`). |
| `NEXT_PUBLIC_DEMO_MODE` | `frontend/.env.local` | `true` = frontend-only demo, no backend. |

See root `.env.example` for a template.

---

## 5. References

- OpenAPI UI: `http://localhost:8000/docs` (when backend is running).
- Demonstration script: [DEMONSTRATION.md](./DEMONSTRATION.md).
