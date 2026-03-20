"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { loadResult } from "@/lib/api";
import type { DriftReport, DriftSignal } from "@/lib/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function statusConfig(status: DriftReport["status"]) {
  if (status === "Stable")
    return { bg: "bg-emerald-50", border: "border-emerald-200", badge: "bg-emerald-500 text-white", icon: "✓" };
  if (status === "Watch")
    return { bg: "bg-amber-50", border: "border-amber-200", badge: "bg-amber-400 text-white", icon: "!" };
  return { bg: "bg-rose-50", border: "border-rose-200", badge: "bg-rose-500 text-white", icon: "↑" };
}

function severityBadge(severity: DriftSignal["severity"]) {
  const map = {
    none: "bg-slate-100 text-slate-500",
    low: "bg-amber-50 text-amber-600 border border-amber-200",
    medium: "bg-orange-50 text-orange-600 border border-orange-200",
    high: "bg-rose-50 text-rose-600 border border-rose-200",
  };
  return map[severity];
}

function driftBarColor(score: number) {
  if (score < 30) return "bg-emerald-400";
  if (score < 60) return "bg-amber-400";
  return "bg-rose-500";
}

// ── Components ────────────────────────────────────────────────────────────────

function DriftSignalCard({ signal }: { signal: DriftSignal }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h4 className="font-semibold text-slate-800">{signal.dimension}</h4>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${severityBadge(signal.severity)}`}>
            {signal.severity}
          </span>
          <span className="text-sm font-bold text-slate-700">{Math.round(signal.drift_score)}</span>
        </div>
      </div>

      {/* Drift bar */}
      <div className="h-1.5 bg-slate-100 rounded-full">
        <div
          className={`h-1.5 rounded-full ${driftBarColor(signal.drift_score)}`}
          style={{ width: `${signal.drift_score}%` }}
        />
      </div>

      {/* Original vs Current */}
      {(signal.original || signal.current) && (
        <div className="grid grid-cols-2 gap-3">
          {signal.original && (
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Original</p>
              <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">{signal.original}</p>
            </div>
          )}
          {signal.current && (
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Current</p>
              <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">{signal.current}</p>
            </div>
          )}
        </div>
      )}

      {/* Evidence */}
      {signal.evidence.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-500 mb-1.5">Supporting Evidence</p>
          <ul className="space-y-1">
            {signal.evidence.map((e, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                <span className="text-slate-400 mt-0.5 shrink-0">•</span>
                {e}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Note */}
      {signal.note && (
        <p className="text-xs text-slate-400 italic border-t border-slate-100 pt-2">{signal.note}</p>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DriftPage() {
  const router = useRouter();
  const [report, setReport] = useState<DriftReport | null>(null);
  const [startupName, setStartupName] = useState("");

  useEffect(() => {
    const data = loadResult();
    if (!data || !data.drift_report) {
      router.replace("/");
      return;
    }
    setReport(data.drift_report);
    setStartupName(data.best_startup?.name ?? "");
  }, [router]);

  if (!report) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const cfg = statusConfig(report.status);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back */}
      <button
        onClick={() => router.push("/memo")}
        className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
      >
        ← Back to Memo
      </button>

      {/* Status hero */}
      <div className={`rounded-2xl border p-6 ${cfg.bg} ${cfg.border}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
              Narrative Drift Report
            </p>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">{startupName}</h1>
            <p className="text-sm text-slate-500 mt-1">
              Checked {new Date(report.checked_at).toLocaleDateString("en-US", {
                month: "short", day: "numeric", year: "numeric",
              })}
            </p>
          </div>

          <div className="shrink-0 flex flex-col items-end gap-3">
            <span className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-bold ${cfg.badge}`}>
              <span>{cfg.icon}</span>
              {report.status}
            </span>
            <div className="text-right">
              <span className="text-3xl font-bold text-slate-900">{Math.round(report.overall_drift)}</span>
              <span className="text-sm text-slate-400"> / 100</span>
              <p className="text-xs text-slate-400">drift score</p>
            </div>
          </div>
        </div>

        {/* Overall drift bar */}
        <div className="mt-4 space-y-1">
          <div className="flex justify-between text-xs text-slate-500">
            <span>No Drift</span>
            <span>Watch Zone</span>
            <span>Drift Risk</span>
          </div>
          <div className="relative h-3 bg-white/60 rounded-full overflow-hidden">
            {/* Zone markers */}
            <div className="absolute inset-0 flex">
              <div className="flex-1 bg-emerald-100" style={{ width: "30%" }} />
              <div className="flex-1 bg-amber-100" style={{ width: "30%" }} />
              <div className="flex-1 bg-rose-100" style={{ width: "40%" }} />
            </div>
            {/* Score indicator */}
            <div
              className={`absolute top-0 h-3 rounded-full transition-all ${driftBarColor(report.overall_drift)}`}
              style={{ width: `${report.overall_drift}%` }}
            />
          </div>
        </div>

        {/* Summary */}
        {report.summary && (
          <p className="mt-4 text-sm text-slate-700 leading-relaxed">{report.summary}</p>
        )}
      </div>

      {/* Dimension cards */}
      {report.signals.length > 0 ? (
        <>
          <h2 className="text-base font-semibold text-slate-800">Dimension Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.signals.map((signal, i) => (
              <DriftSignalCard key={i} signal={signal} />
            ))}
          </div>
        </>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400">
          <p className="text-4xl mb-3">📋</p>
          <p className="font-medium text-slate-600">No dimension data available</p>
          <p className="text-sm mt-1">
            Set an <code className="bg-slate-100 px-1 rounded">original_narrative</code> on the startup
            to enable dimension-level drift analysis.
          </p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <button
          onClick={() => router.push("/results")}
          className="text-sm text-slate-500 hover:text-slate-700 border border-slate-200 hover:border-slate-300 px-4 py-2 rounded-lg transition-colors"
        >
          ← All Results
        </button>
        <button
          onClick={() => router.push("/")}
          className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          New Analysis →
        </button>
      </div>
    </div>
  );
}
