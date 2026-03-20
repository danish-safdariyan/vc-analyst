"""
Always-On VC Analyst — FastAPI Backend
Run with: uvicorn app.main:app --reload --port 8000
Swagger UI: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, scrape
from app.api.routes import router as agent_router
from app.config.settings import settings


def _cors_allow_origins() -> list[str]:
    base = ["http://localhost:3000", "http://127.0.0.1:3000"]
    extra = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for o in base + extra:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


app = FastAPI(
    title="VC Analyst Backend",
    description="AI-powered agentic platform for venture capital investors.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(scrape.router)
app.include_router(agent_router, prefix="/api")
