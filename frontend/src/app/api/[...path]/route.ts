import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const PROXY_TIMEOUT_MS = 300_000;

/**
 * Resolve FastAPI base URL (no trailing slash).
 * Prefer BACKEND_URL / API_UPSTREAM at runtime (Docker, DigitalOcean) so you
 * do not need to rebuild when the API URL changes. Fallback to NEXT_PUBLIC_* for local dev.
 */
function backendBase(): string {
  const raw =
    process.env.BACKEND_URL ||
    process.env.API_UPSTREAM ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";
  return raw.replace(/\/$/, "");
}

async function proxy(req: NextRequest, pathSegments: string[]): Promise<NextResponse> {
  const subpath = pathSegments.join("/");
  const target = `${backendBase()}/api/${subpath}${req.nextUrl.search}`;

  const headers = new Headers();
  const ct = req.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  const auth = req.headers.get("authorization");
  if (auth) headers.set("authorization", auth);

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
    signal: AbortSignal.timeout(PROXY_TIMEOUT_MS),
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    const buf = await req.arrayBuffer();
    if (buf.byteLength) init.body = buf;
  }

  const res = await fetch(target, init);

  const out = new Headers(res.headers);
  return new NextResponse(res.body, {
    status: res.status,
    headers: out,
  });
}

type RouteCtx = { params: { path: string[] } };

export async function GET(req: NextRequest, ctx: RouteCtx) {
  return proxy(req, ctx.params.path);
}

export async function POST(req: NextRequest, ctx: RouteCtx) {
  return proxy(req, ctx.params.path);
}

export async function PUT(req: NextRequest, ctx: RouteCtx) {
  return proxy(req, ctx.params.path);
}

export async function PATCH(req: NextRequest, ctx: RouteCtx) {
  return proxy(req, ctx.params.path);
}

export async function DELETE(req: NextRequest, ctx: RouteCtx) {
  return proxy(req, ctx.params.path);
}
