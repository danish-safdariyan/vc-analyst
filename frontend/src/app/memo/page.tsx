"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { loadResult } from "@/lib/api";
import type { InvestmentMemo, StartupWithScore } from "@/lib/types";

function recommendationStyle(rec: string) {
  if (rec === "Fast Track") return "bg-emerald-500 text-white";
  if (rec === "Take Meeting") return "bg-indigo-600 text-white";
  return "bg-slate-200 text-slate-600";
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 75 ? "bg-emerald-400" : value >= 45 ? "bg-amber-400" : "bg-rose-400";
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-32 text-slate-500 shrink-0 text-xs">{label}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="w-8 text-right text-slate-700 font-semibold text-xs">{Math.round(value)}</span>
    </div>
  );
}

export default function MemoPage() {
  const router = useRouter();
  const [memo, setMemo] = useState<InvestmentMemo | null>(null);
  const [startup, setStartup] = useState<StartupWithScore | null>(null);

  useEffect(() => {
    const data = loadResult();
    if (!data || !data.memo || !data.best_startup) {
      router.replace("/");
      return;
    }
    setMemo(data.memo);
    setStartup(data.best_startup);
  }, [router]);

  if (!memo || !startup) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const { sections } = memo;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back */}
      <button
        onClick={() => router.push("/results")}
        className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
      >
        ← Back to Results
      </button>

      {/* Memo header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              Investment Memo
            </p>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">{startup.name}</h1>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <span className="text-sm bg-slate-100 text-slate-600 px-2.5 py-0.5 rounded-full">
                {startup.stage}
              </span>
              <span className="text-sm bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full">
                {startup.sector}
              </span>
              <span className="text-sm text-slate-400">{startup.geography}</span>
            </div>
          </div>

          <div className="shrink-0 flex flex-col items-end gap-2">
            <span
              className={`px-4 py-1.5 rounded-full text-sm font-semibold ${recommendationStyle(
                sections.recommendation
              )}`}
            >
              {sections.recommendation}
            </span>
            <span className="text-2xl font-bold text-slate-900">
              {Math.round(startup.fit_score)}
              <span className="text-sm font-normal text-slate-400">/100</span>
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column — memo sections */}
        <div className="lg:col-span-2 space-y-4">
          <Section title="Startup Summary">
            <p className="text-sm text-slate-700 leading-relaxed">{sections.startup_summary}</p>
          </Section>

          <Section title="Why It Matches the Thesis">
            <p className="text-sm text-slate-700 leading-relaxed">{sections.why_it_matches}</p>
          </Section>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Section title="Bull Case">
              <div className="flex gap-2">
                <span className="text-emerald-500 text-lg mt-0.5">↑</span>
                <p className="text-sm text-slate-700 leading-relaxed">{sections.bull_case}</p>
              </div>
            </Section>

            <Section title="Bear Case">
              <div className="flex gap-2">
                <span className="text-rose-500 text-lg mt-0.5">↓</span>
                <p className="text-sm text-slate-700 leading-relaxed">{sections.bear_case}</p>
              </div>
            </Section>
          </div>

          <Section title="Key Signals">
            <ul className="space-y-2">
              {sections.key_signals.map((signal, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-indigo-400 mt-0.5 shrink-0">◆</span>
                  {signal}
                </li>
              ))}
            </ul>
          </Section>

          <Section title="Suggested Next Step">
            <div className="flex gap-3 items-start">
              <span className="text-indigo-600 text-xl shrink-0">→</span>
              <p className="text-sm font-medium text-slate-800">{sections.next_step}</p>
            </div>
          </Section>
        </div>

        {/* Right column — fit score breakdown */}
        <div className="space-y-4">
          <Section title="Fit Score Breakdown">
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <span className="text-3xl font-bold text-slate-900">{Math.round(startup.fit_score)}</span>
                <span className="text-sm text-slate-400">/ 100</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div
                  className={`h-2 rounded-full ${
                    startup.fit_score >= 75
                      ? "bg-emerald-400"
                      : startup.fit_score >= 45
                      ? "bg-amber-400"
                      : "bg-rose-400"
                  }`}
                  style={{ width: `${startup.fit_score}%` }}
                />
              </div>
              <div className="space-y-2 pt-1">
                <ScoreBar label="Sector fit" value={startup.fit_dimensions.sector_fit} />
                <ScoreBar label="Stage fit" value={startup.fit_dimensions.stage_fit} />
                <ScoreBar label="Team fit" value={startup.fit_dimensions.team_fit} />
                <ScoreBar label="Signal strength" value={startup.fit_dimensions.signal_strength} />
                <ScoreBar label="Market reasoning" value={startup.fit_dimensions.market_reasoning} />
              </div>
            </div>
          </Section>

          {/* Founders */}
          {startup.founders.length > 0 && (
            <Section title="Founding Team">
              <div className="space-y-3">
                {startup.founders.map((f) => (
                  <div key={f.name}>
                    <p className="text-sm font-medium text-slate-800">{f.name}</p>
                    <p className="text-xs text-slate-500">{f.background}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Metrics */}
          {(startup.metrics.arr || startup.metrics.growth || startup.metrics.customers || startup.metrics.team_size) && (
            <Section title="Metrics">
              <div className="space-y-1.5 text-sm">
                {startup.metrics.arr && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">ARR</span>
                    <span className="font-medium text-slate-800">{startup.metrics.arr}</span>
                  </div>
                )}
                {startup.metrics.growth && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Growth</span>
                    <span className="font-medium text-slate-800">{startup.metrics.growth}</span>
                  </div>
                )}
                {startup.metrics.customers && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Customers</span>
                    <span className="font-medium text-slate-800">{startup.metrics.customers}</span>
                  </div>
                )}
                {startup.metrics.team_size && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Team</span>
                    <span className="font-medium text-slate-800">{startup.metrics.team_size} people</span>
                  </div>
                )}
              </div>
            </Section>
          )}

          <button
            onClick={() => router.push("/drift")}
            className="w-full border border-slate-200 hover:border-slate-300 text-slate-700 hover:text-slate-900 text-sm font-medium py-2.5 rounded-xl transition-colors"
          >
            Check Narrative Drift →
          </button>
        </div>
      </div>
    </div>
  );
}
