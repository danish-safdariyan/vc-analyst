import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { backendOriginFromEnv } from "@/lib/backend-origin";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const PROXY_TIMEOUT_MS = 300_000;

async function proxy(req: NextRequest, pathSegments: string[]): Promise<NextResponse> {
  const base = backendOriginFromEnv();
  const subpath = pathSegments.join("/");
  const target = `${base}/api/${subpath}${req.nextUrl.search}`;

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
  // App Platform / CDN may cache GETs; polling /api/analysis/* must always hit origin.
  out.set("Cache-Control", "private, no-store, max-age=0");
  out.set("Pragma", "no-cache");
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
