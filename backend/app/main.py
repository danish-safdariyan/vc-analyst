"""
Always-On VC Analyst — FastAPI Backend

Local: uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}
Or: python -m app.main (reads PORT, defaults to 8000)

DigitalOcean App Platform: the container CMD uses PORT (set by the platform).
Keep App Spec http_port aligned with the port your process listens to.

If the API is exposed under a path (e.g. /vc-analyst-backend), set APP_URL_PREFIX
to that value. Middleware strips it when present; if the gateway already strips
the prefix, requests still match /api/... (mount() alone could 404 in that case).

Set GATEWAY_STRIPS_API_PREFIX=true when DigitalOcean routes /api/* to this service
with path trimming (incoming path is /start-analysis, not /api/start-analysis).

Swagger: /docs locally, or /prefix/docs when the full path includes the prefix.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

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


class StripPrefixMiddleware:
    """Strip APP_URL_PREFIX from the request path so routes stay at /api/..., /health."""

    def __init__(self, app: ASGIApp, prefix: str):
        self.app = app
        self.prefix = prefix.rstrip("/") or ""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.prefix and scope["type"] == "http":
            path = scope.get("path")
            if isinstance(path, str) and (
                path == self.prefix or path.startswith(self.prefix + "/")
            ):
                new_path = path[len(self.prefix) :] or "/"
                scope = dict(scope)
                scope["path"] = new_path
        await self.app(scope, receive, send)


# Routes FastAPI mounts at the app root (not under /api/)
_GATEWAY_ROOT_PATHS = frozenset({"/health", "/scrape"})


def _is_openapi_docs_path(path: str) -> bool:
    if path in ("/openapi.json", "/redoc"):
        return True
    return path.startswith("/docs")


class PrependApiPrefixMiddleware:
    """When the ingress strips /api before forwarding (e.g. DO path trim), restore it."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path")
        if not isinstance(path, str):
            await self.app(scope, receive, send)
            return
        if path.startswith("/api") or path in _GATEWAY_ROOT_PATHS or _is_openapi_docs_path(path):
            await self.app(scope, receive, send)
            return
        if path == "/":
            await self.app(scope, receive, send)
            return
        scope = dict(scope)
        scope["path"] = "/api" + path
        await self.app(scope, receive, send)


def create_api_app() -> FastAPI:
    api = FastAPI(
        title="VC Analyst Backend",
        description="AI-powered agentic platform for venture capital investors.",
        version="0.1.0",
    )

    # Strip prefix first (outermost) so paths match before CORS and routing.
    pfx = _normalize_url_prefix(settings.app_url_prefix)
    if pfx:
        api.add_middleware(StripPrefixMiddleware, prefix=pfx)

    if settings.gateway_strips_api_prefix:
        api.add_middleware(PrependApiPrefixMiddleware)

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


app = create_api_app()


if __name__ == "__main__":
    import os

    import uvicorn

    _port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=_port)
