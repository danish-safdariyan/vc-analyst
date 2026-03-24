# Demonstration guide (test datasets)

Follow these scenarios to show **working AI integration** and **reproducible** behavior. Assume the backend is on **port 8000** and the frontend on **3000** unless noted.

**Prerequisite:** see root [README.md](../README.md) for install and env.

---

## Scenario A — Full pipeline (Dataset 01)

**Dataset file:** [datasets/dataset_01_devtools_preseed.json](../datasets/dataset_01_devtools_preseed.json)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set `USE_MOCK=true` in `backend/.env` (optional: add `OPENROUTER_API_KEY` later for live). | Backend starts without external data. |
| 2 | Start backend: `uvicorn app.main:app --reload --port 8000` from `backend/`. | Swagger at http://localhost:8000/docs |
| 3 | Set `NEXT_PUBLIC_DEMO_MODE=false` and `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` in `frontend/.env.local`. | Frontend talks to API. |
| 4 | Start frontend: `npm run dev` from `frontend/`. | App at http://localhost:3000 |
| 5 | Open **Thesis**, paste the **`thesis_raw`** from dataset 01, click **Run Analysis →**. | Progress steps; then redirect to **Results** with ranked candidates, memo, drift. |
| 6 | Open **Memo** and **Drift** in the nav. | Same run’s memo and drift panels populate from session. |

**AI in this scenario:** With mock, the orchestrator uses a fixed analytical fixture; with `USE_MOCK=false` and a key, **thesis parsing, scoring, memo, drift, and discovery** use **OpenRouter** (plus optional Crustdata/Product Hunt discovery sources).

---

## Scenario B — Different thesis wording (Dataset 02)

**Dataset file:** [datasets/dataset_02_vertical_enterprise_saas.json](../datasets/dataset_02_vertical_enterprise_saas.json)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Same stack as Scenario A. | — |
| 2 | Paste **`thesis_raw`** from dataset 02 into **Thesis** and run analysis. | UI shows **your** thesis text in headers; mock mode still shows the **same illustrative companies** (documented limitation). |
| 3 | Compare **Results** thesis panel to dataset 02. | Confirms input is wired through the pipeline. |

**Grading note:** Differentiates “user only types one field” (the thesis) while the tool does multi-step AI work.

---

## Scenario C — Ask assistant (Dataset 03)

**Dataset file:** [datasets/dataset_03_fintech_infrastructure.json](../datasets/dataset_03_fintech_infrastructure.json)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Backend running; `NEXT_PUBLIC_DEMO_MODE=false`. | — |
| 2 | Open **Ask** (`/chat`). | Chat UI loads. |
| 3 | Paste prompts from **`sample_chat_prompts`** (or `api_smoke_test` message). | **With API key + `USE_MOCK=false`:** Markdown-formatted LLM reply. **Mock/offline:** placeholder text marked mock. |
| 4 | Optional: `POST /api/chat` with the dataset body. | JSON `{ "reply": "...", "used_mock": false|true }`. |

---

## Automated smoke test

From repo root (Python 3.11+):

```bash
python scripts/verify_datasets.py --base-url http://127.0.0.1:8000
```

Requires the backend running. Validates each dataset’s `api_smoke_test` and prints HTTP status.

---

## Frontend-only demo (no Python)

Set `NEXT_PUBLIC_DEMO_MODE=true` in `frontend/.env.local`, run `npm run dev`, use **Thesis** with any dataset `thesis_raw`. The UI simulates delay and loads a fixture in the browser (no LLM call).

---

## Suggested screen recording checklist

1. Show `.env` / `.env.local` flags (blur secrets).  
2. Run Scenario A end-to-end.  
3. Show one **Ask** prompt with a visible LLM answer (Scenario C).  
4. Show `./docs/CODEBOOK.md` and `datasets/INDEX.md` in the repo.
