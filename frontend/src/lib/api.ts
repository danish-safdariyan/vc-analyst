import type { AnalyzeResponse, ChatApiResponse, VCAnalysisResult } from "./types";
import { buildDemoResult } from "./demo";

// All browser calls use same-origin `/api/*` so Next can rewrite to the backend
// (see next.config.mjs). This avoids CORS on DigitalOcean and other hosts. The
// analysis pipeline uses an async job + short polls, so we stay under proxy timeouts.
// Set NEXT_PUBLIC_API_DIRECT=true to call the backend URL directly (local debugging).
const DIRECT_BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const API_DIRECT = process.env.NEXT_PUBLIC_API_DIRECT === "true";

const BASE = "/api";

// Set NEXT_PUBLIC_DEMO_MODE=true in .env.local to skip the backend entirely
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

async function post<T>(path: string, body: unknown, direct = false, timeoutMs = 300_000): Promise<T> {
  const useDirect = direct || API_DIRECT;
  const url = useDirect ? `${DIRECT_BACKEND}/api${path}` : `${BASE}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`${res.status} ${path}: ${text}`);
    }

    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

// ── Session storage helpers ────────────────────────────────────────────────────

const STORAGE_KEY = "vc_analysis_result";

export function saveResult(result: VCAnalysisResult): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(result));
}

export function loadResult(): VCAnalysisResult | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as VCAnalysisResult) : null;
  } catch {
    return null;
  }
}

export function clearResult(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}

export { DEMO_MODE };

// ── helpers ───────────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const url = API_DIRECT ? `${DIRECT_BACKEND}/api${path}` : `${BASE}${path}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export async function runAnalysis(thesis: string): Promise<VCAnalysisResult> {
  // Frontend offline demo mode — no backend required
  if (DEMO_MODE) {
    await new Promise((r) => setTimeout(r, 2400));
    return buildDemoResult(thesis);
  }

  // ── Submit job (returns immediately with a job_id) ────────────────────────
  let jobId: string;
  try {
    const submit = await post<{ job_id: string; status: string }>(
      "/start-analysis",
      { thesis },
      false,
      10_000, // short timeout — this call should respond in <1 s
    );
    jobId = submit.job_id;
  } catch (err) {
    // If submit itself fails the backend is truly down — show error
    console.error("[api] failed to submit analysis job", err);
    throw new Error("Could not reach the backend. Make sure it is running on port 8000.");
  }

  // ── Poll until done (each poll is a tiny GET, immune to long-request suspension) ──
  const POLL_INTERVAL_MS = 2500;
  const MAX_POLLS = 120; // 5 minutes max
  for (let i = 0; i < MAX_POLLS; i++) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    try {
      const poll = await get<{ status: string; result?: VCAnalysisResult; error?: string }>(
        `/analysis/${jobId}`,
      );
      if (poll.status === "done" && poll.result) {
        return poll.result;
      }
      if (poll.status === "error") {
        throw new Error(`Analysis failed: ${poll.error ?? "unknown error"}`);
      }
      // status === "running" — keep polling
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      // 404 = job never existed or disk/memory store was wiped before we added persistence
      if (msg.startsWith("404 ")) {
        throw new Error(
          "This analysis job no longer exists on the server (e.g. API restarted). Run analysis again.",
        );
      }
      // A single failed poll shouldn't kill everything — log and retry
      console.warn(`[api] poll attempt ${i + 1} failed, retrying…`, err);
    }
  }

  throw new Error("Analysis timed out after 5 minutes.");
}

export async function askAssistant(message: string): Promise<ChatApiResponse> {
  const trimmed = message.trim();
  if (!trimmed) {
    throw new Error("Message is empty.");
  }

  if (DEMO_MODE) {
    await new Promise((r) => setTimeout(r, 500));
    return {
      reply:
        `[Demo mode — no LLM] You asked: “${trimmed.slice(0, 200)}${trimmed.length > 200 ? "…" : ""}”.\n\n` +
        "In a live setup, OpenRouter would answer with VC-style analysis. Turn off NEXT_PUBLIC_DEMO_MODE " +
        "and run the backend with a real OPENROUTER_API_KEY to get real replies.",
      used_mock: true,
    };
  }

  return post<ChatApiResponse>("/chat", { message: trimmed }, false, 120_000);
}
