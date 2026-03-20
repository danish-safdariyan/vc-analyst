"use client";

import { useState } from "react";
import type { StepTrace } from "@/lib/types";

const STEP_LABELS: Record<string, string> = {
  parse_thesis: "1. Parse Thesis",
  discover_startups: "2. Discover Startups",
  score_startups: "3. Score Startups",
  generate_memo: "4. Generate Memo",
  check_drift: "5. Check Drift",
};

function statusIcon(status: StepTrace["status"]) {
  if (status === "ok") return <span className="text-emerald-500">✓</span>;
  if (status === "error") return <span className="text-rose-500">✗</span>;
  return <span className="text-slate-400">–</span>;
}

function statusBg(status: StepTrace["status"]) {
  if (status === "ok") return "bg-emerald-50 border-emerald-200 text-emerald-700";
  if (status === "error") return "bg-rose-50 border-rose-200 text-rose-700";
  return "bg-slate-50 border-slate-200 text-slate-400";
}

export default function PipelineTrace({ traces }: { traces: StepTrace[] }) {
  const [open, setOpen] = useState(false);
  const totalMs = traces.reduce((s, t) => s + t.duration_ms, 0);
  const errors = traces.filter((t) => t.status === "error").length;

  return (
    <div className="border border-slate-200 rounded-xl bg-white overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
      >
        <span className="flex items-center gap-2 font-medium">
          <span>Pipeline Trace</span>
          {errors > 0 && (
            <span className="text-xs bg-rose-100 text-rose-600 px-1.5 py-0.5 rounded-full">
              {errors} error{errors > 1 ? "s" : ""}
            </span>
          )}
        </span>
        <span className="flex items-center gap-3 text-slate-400">
          <span>{(totalMs / 1000).toFixed(1)}s total</span>
          <span>{open ? "▲" : "▼"}</span>
        </span>
      </button>

      {open && (
        <div className="border-t border-slate-100 divide-y divide-slate-100">
          {traces.map((trace) => (
            <div key={trace.step_id} className="flex items-center gap-3 px-5 py-3">
              <span className="text-base w-5 text-center">{statusIcon(trace.status)}</span>
              <span
                className={`text-xs font-medium border px-2 py-0.5 rounded-full ${statusBg(
                  trace.status
                )}`}
              >
                {trace.status}
              </span>
              <span className="text-sm text-slate-700 flex-1">
                {STEP_LABELS[trace.step_id] ?? trace.step_id}
              </span>
              <span className="text-xs text-slate-400 tabular-nums">
                {trace.duration_ms > 0 ? `${trace.duration_ms.toFixed(0)}ms` : "—"}
              </span>
              {trace.error && (
                <span className="text-xs text-rose-500 max-w-xs truncate" title={trace.error}>
                  {trace.error}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
