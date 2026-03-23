import { NextResponse } from "next/server";

/** App Platform / load balancer liveness (public port serves Next only). */
export async function GET() {
  return NextResponse.json({ status: "ok", service: "vc-analyst" });
}
