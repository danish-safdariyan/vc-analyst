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
uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}
```

On **DigitalOcean App Platform** with the **root `Dockerfile`**, the **web** process must bind to the **`PORT`** env the platform provides (Next.js `server.js`). Your App Spec **`http_port`** must match that port (e.g. `3000`). If you deploy **only** `backend/Dockerfile`, bind **`uvicorn`** to **`PORT`** (e.g. `8000`) and set **`http_port`** accordingly.

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

**Full stack (recommended):** one image runs Next.js on **`PORT`** (default 3000) and FastAPI on **127.0.0.1:8000**. Create `backend/.env` first (see `backend/.env.example`), then:

```bash
docker compose up --build
```

Open **http://localhost:3000**.

**API only** (for local frontend dev): build and run `backend/Dockerfile` from the `backend/` directory, then:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 NEXT_PUBLIC_DEMO_MODE=false npm run dev
```

---

## Deployment (DigitalOcean & others)

### DigitalOcean App Platform (recommended for this repo)

- **Spec:** [`.do/app.yaml`](.do/app.yaml) — **one** service (`app`) built from the repo root [`Dockerfile`](Dockerfile) (`source_dir: /`). Next.js listens on the platform **`PORT`**; FastAPI runs inside the same container on **127.0.0.1:8000**. The Next route `src/app/api/[...path]/route.ts` proxies `/api/*` to that internal URL via **`BACKEND_URL`** (set to `http://127.0.0.1:8000` in the spec).

| Variable | Purpose |
|----------|--------|
| **`OPENROUTER_API_KEY`** (SECRET) | LLM + agents on the API process. |
| **`USE_MOCK`** | `"true"` for fixture-only runs without an LLM key. |
| **`BACKEND_URL`** | Keep **`http://127.0.0.1:8000`** for this single-container layout (server-side proxy only). |
| **`NEXT_PUBLIC_DEMO_MODE`** | Build-time; usually `"false"`. |

**Health check:** **`GET /health`** is served by Next.js for the load balancer; the FastAPI **`/health`** is still available internally.

**Async analysis jobs (`POST /api/start-analysis` + polling):** Job state is stored on **local disk** inside the container (default **`/tmp/vc-analysis-jobs`** in the unified Docker image) and **must not** be shared across multiple containers unless you use a shared volume or external store. Keep **`instance_count: 1`** and disable autoscaling for the `app` component, or polls can hit another instance and return **404**. Responses and the Next `/api` proxy set **`Cache-Control: no-store`** so the App Platform CDN does not serve a stale **404** for **`GET /api/analysis/{id}`**.

**Split deploy (two components):** you can still deploy **`backend/Dockerfile`** and **`frontend/Dockerfile`** as separate services. Then set **`BACKEND_URL`** (runtime) on the web service to the API’s public base URL (**no** trailing slash, **not** ending with `/api`). If the API is under a path prefix, set **`APP_URL_PREFIX`** on the API and include that path in **`BACKEND_URL`**. If the gateway strips `/api` before forwarding, set **`GATEWAY_STRIPS_API_PREFIX=true`** on the API (see `backend/app/main.py`). Set **`CORS_ORIGINS`** on the API only if the browser calls the API host directly (`NEXT_PUBLIC_API_DIRECT=true`).

### Other hosts (Railway, Render, Fly, Vercel, …)

Prefer the **root [`Dockerfile`](Dockerfile)** for a single URL. Alternatively, deploy the API from **`backend/Dockerfile`**, the web from **`frontend/Dockerfile`**, and set **`BACKEND_URL`** on the web container to the API’s public base URL.

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
Dockerfile         Production image: Next + FastAPI (repo root)
docker/            entrypoint for unified container
backend/           FastAPI app, agents, job persistence, Dockerfile
frontend/          Next.js UI, Dockerfile
datasets/          Test datasets (JSON) + INDEX
docs/              Codebook + demonstration guide
scripts/           verify_datasets.py
docker-compose.yml Full stack (root Dockerfile)
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
