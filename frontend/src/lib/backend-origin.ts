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
  const raw =
    process.env.BACKEND_URL ||
    process.env.API_UPSTREAM ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";
  return normalizeBackendOrigin(raw);
}
