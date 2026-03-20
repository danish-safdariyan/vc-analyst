# VC Analyst AI (Always-On VC Analyst)

**VC Analyst AI** is an AI-powered assistant for venture investors. You type a **fund thesis in plain English**; the system structures it, surfaces matching-style startups, **LLM-scores** fit, drafts an **investment memo**, checks **narrative drift**, and exposes an **Ask** tab for open-ended VC Q&A.

**Target user:** associates, principals, or GPs doing first-pass screening and diligence.  
**Design goal:** **one primary input** (the thesis) for the main workflow, plus optional API keys for live data/LLM.

---

## Table of contents

- [Architecture](#architecture)
- [AI integration](#ai-integration)
- [Quick start (local)](#quick-start-local)
- [Docker](#docker)
- [Deployment (DigitalOcean & others)](#deployment-digitalocean--others)
- [Test datasets & demonstration](#test-datasets--demonstration)
- [Documentation](#documentation)
- [Project layout](#project-layout)

---

## Architecture

```mermaid
flowchart LR
  subgraph client [Browser]
    UI[Next.js 14 App]
  end
  subgraph api [FastAPI Backend]
    OR[OpenRouter LLM]
    CD[Crustdata / mocks]
    AG[Five agents + orchestrator]
  end
  UI -->|HTTP JSON| AG
  AG --> OR
  AG --> CD
```

| Layer | Stack | Role |
|-------|--------|------|
| **Frontend** | Next.js 14, TypeScript, Tailwind | Thesis form, results, memo, drift, **Ask** (`/chat`); rewrites `/api/*` to FastAPI (local + production). |
| **Backend** | FastAPI, Python 3.12, Pydantic | REST API, background analysis jobs, agent orchestration. |
| **Model access** | OpenAI-compatible client → [OpenRouter](https://openrouter.ai) | Parsing, scoring, memo, drift, chat. Default model family configured in `backend/app/config/settings.py`. |
| **Data** | Crustdata (optional), in-app mocks | Startup discovery; safe offline demo via `USE_MOCK=true`. |

Persistent analysis jobs (for long runs) are written under `backend/.analysis_jobs/` so `uvicorn --reload` does not lose polling state.

---

## AI integration

| Feature | AI? | Implementation |
|---------|-----|----------------|
| Thesis → structured criteria | Yes | `thesis_parser_agent` → `run_structured_llm` (fallback rules if no key/mock). |
| Startup fit scores | Yes | `thesis_match_agent` scores five dimensions (0–100). |
| Investment memo | Yes | `memo_generation_agent`. |
| Narrative drift | Yes | `narrative_drift_agent`. |
| **Ask** | Yes | `POST /api/chat` → `run_llm` with VC-analyst system prompt. |
| Offline demo | Deterministic fixture | `USE_MOCK=true` or `NEXT_PUBLIC_DEMO_MODE=true` uses baked JSON (no external LLM). |

API explorer (when running): **http://localhost:8000/docs**

---

## Quick start (local)

### Prerequisites

- **Node.js 18+**
- **Python 3.11+** (3.12 recommended; matches Docker image)
- Optional: **OpenRouter** API key for live LLM

### 1. Environment

Copy secrets from `.env.example`:

- **`backend/.env`** — at minimum set `OPENROUTER_API_KEY` (or leave `USE_MOCK=true` for fixture-only runs).
- **`frontend/.env.local`** — e.g.  
  `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`  
  `NEXT_PUBLIC_DEMO_MODE=false`  
  (Use `NEXT_PUBLIC_DEMO_MODE=true` only for a purely offline UI demo without Python.)

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# ensure backend/.env exists
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — use **Thesis** for the pipeline or **Ask** for chat.

### Clean rebuild (Next.js cache issues)

```bash
cd frontend && npm run clean && npm run dev
```

---

## Docker

Run the API in a container (create `backend/.env` first):

```bash
docker compose up --build
```

Then start the frontend locally pointed at the API:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 NEXT_PUBLIC_DEMO_MODE=false npm run dev
```

---

## Deployment (DigitalOcean & others)

### DigitalOcean App Platform (recommended for this repo)

- **Spec:** [`.do/app.yaml`](.do/app.yaml) — two services (`api` + `web`) with `source_dir` set to `backend` and `frontend`.
- **Step-by-step:** [docs/DEPLOY_DIGITALOCEAN.md](docs/DEPLOY_DIGITALOCEAN.md)

The browser calls **same-origin** `/api/...`; Next.js rewrites to your FastAPI URL (`NEXT_PUBLIC_API_URL` at **build** time), so you typically **do not** need extra CORS. Optional: set `CORS_ORIGINS` and `NEXT_PUBLIC_API_DIRECT=true` only if you want the browser to hit the API host directly.

Set **`OPENROUTER_API_KEY`** (and optional data keys) as **RUN_TIME** secrets on the API service. Use **`GET /health`** for health checks.

### Other hosts (Railway, Render, Fly, Vercel, …)

Same pattern: deploy the API container from `backend/Dockerfile`, deploy the web container from `frontend/Dockerfile` with `NEXT_PUBLIC_API_URL` pointing at the public API URL.

---

## Test datasets & demonstration

We ship **three** curated JSON datasets under **`datasets/`**:

| File | Intent |
|------|--------|
| `dataset_01_devtools_preseed.json` | Full pipeline demo; aligns with the built-in **mock** fixture. |
| `dataset_02_vertical_enterprise_saas.json` | Alternate thesis wording (vertical SaaS). |
| `dataset_03_fintech_infrastructure.json` | Fintech thesis + chat-oriented smoke test payload. |

**Index:** [datasets/INDEX.md](datasets/INDEX.md)

**Step-by-step demos:** [docs/DEMONSTRATION.md](docs/DEMONSTRATION.md)

**Automated smoke test** (backend must be running):

```bash
python scripts/verify_datasets.py --base-url http://127.0.0.1:8000
```

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/CODEBOOK.md](docs/CODEBOOK.md) | User, use case, variable definitions, dataset schema, env vars |
| [docs/DEMONSTRATION.md](docs/DEMONSTRATION.md) | Grader-friendly scenarios A–C + optional recording checklist |
| [datasets/INDEX.md](datasets/INDEX.md) | Dataset catalog |

---

## Project layout

```
backend/           FastAPI app, agents, job persistence, Dockerfile
frontend/          Next.js UI
datasets/          Test datasets (JSON) + INDEX
docs/              Codebook + demonstration guide
scripts/           verify_datasets.py
docker-compose.yml API service
```

---

## Core workflow (UI)

1. Enter thesis → **Run analysis** (async job + polling).  
2. **Results** — ranked startups and fit dimensions.  
3. **Memo** / **Drift** — generated narrative outputs.  
4. **Ask** — free-form VC Q&A with markdown rendering.

---

## License / course submission

Push this repository to GitHub when required and add the public link plus a deployed app URL per instructor instructions.
