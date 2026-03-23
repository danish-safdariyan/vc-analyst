"""
Always-On VC Analyst — FastAPI Backend

Local: uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}
Or: python -m app.main (reads PORT, defaults to 8000)

DigitalOcean App Platform: the container CMD uses PORT (set by the platform).
Keep App Spec http_port aligned with the port your process binds to.

If the component route is /vc-analyst-backend, set APP_URL_PREFIX=/vc-analyst-backend
so /vc-analyst-backend/api/... reaches this app.

Swagger: /docs locally, or /vc-analyst-backend/docs behind a path-based route.
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


def _normalize_url_prefix(raw: str) -> str:
    p = raw.strip()
    if not p:
        return ""
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")


def create_api_app() -> FastAPI:
    api = FastAPI(
        title="VC Analyst Backend",
        description="AI-powered agentic platform for venture capital investors.",
        version="0.1.0",
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api.include_router(health.router)
    api.include_router(scrape.router)
    api.include_router(agent_router, prefix="/api")
    return api


_api = create_api_app()
_prefix = _normalize_url_prefix(settings.app_url_prefix)

if _prefix:
    # DigitalOcean forwards paths like /vc-analyst-backend/api/... unchanged; mount
    # strips the prefix so routes match /api/... and /health inside the inner app.
    _root = FastAPI()

    @_root.get("/health")
    async def _root_health():
        """For load-balancer probes that hit /health on the container without the route prefix."""
        return {"status": "ok", "service": "vc-analyst-backend"}

    _root.mount(_prefix, _api)
    app = _root
else:
    app = _api


if __name__ == "__main__":
    import os

    import uvicorn

    _port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=_port)
