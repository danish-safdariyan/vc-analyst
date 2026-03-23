/**
 * FastAPI mounts routes at `/api/...`. The env base URL must be the service
 * origin + optional path prefix (e.g. /vc-analyst-backend), but must NOT end
 * with `/api` — we append `/api/...` ourselves. Trailing `/api` causes
 * `/api/api/start-analysis` and FastAPI returns 404.
 */
function ensureUrlScheme(raw: string): string {
  const t = raw.trim();
  if (!t) return t;
  if (/^https?:\/\//i.test(t)) return t;
  // Local dev often omits scheme
  if (t.startsWith("127.0.0.1") || t.startsWith("localhost")) {
    return `http://${t}`;
  }
  return `https://${t}`;
}

export function normalizeBackendOrigin(raw: string): string {
  let s = ensureUrlScheme(raw).replace(/\/$/, "");
  while (s.endsWith("/api")) {
    s = s.slice(0, -4);
  }
  return s;
}

export function backendOriginFromEnv(): string {
  // Unified image only (root Dockerfile). Checked first so DO UI env (BACKEND_URL, etc.)
  // cannot point the server proxy at the public URL or localhost quirks break polling.
  if (process.env["UNIFIED_CONTAINER"] === "1") {
    return "http://127.0.0.1:8000";
  }
  // Unified Docker / App Platform (Next + FastAPI in one container): the server-side
  // proxy must call loopback. If BACKEND_URL is set to the public app URL in the DO UI,
  // requests would go back through the load balancer and hit a *different* instance
  // than POST /start-analysis — job polling then 404s. INTERNAL_FASTAPI_URL wins.
  const internal = process.env.INTERNAL_FASTAPI_URL?.trim();
  if (internal) {
    return normalizeBackendOrigin(internal);
  }
  const raw =
    process.env.BACKEND_URL ||
    process.env.API_UPSTREAM ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";
  return normalizeBackendOrigin(raw);
}
