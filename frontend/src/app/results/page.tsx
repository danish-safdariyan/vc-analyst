"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { loadResult } from "@/lib/api";
import type { VCAnalysisResult } from "@/lib/types";
import StartupCard from "@/components/StartupCard";
import PipelineTrace from "@/components/PipelineTrace";

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<VCAnalysisResult | null>(null);

  useEffect(() => {
    const data = loadResult();
    if (!data) {
      router.replace("/");
      return;
    }
    setResult(data);
  }, [router]);

  if (!result) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const { thesis, candidates, best_startup, pipeline_trace } = result;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analysis Results</h1>
          <p className="mt-1 text-sm text-slate-500 max-w-2xl line-clamp-2">
            &ldquo;{thesis.raw}&rdquo;
          </p>
        </div>
        <button
          onClick={() => router.push("/")}
          className="shrink-0 text-sm text-slate-500 hover:text-slate-700 border border-slate-200 hover:border-slate-300 px-3 py-1.5 rounded-lg transition-colors"
        >
          ← New Analysis
        </button>
      </div>

      {/* Thesis criteria pills */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap gap-2">
        {thesis.sectors.map((s) => (
          <Pill key={s} label={s} color="indigo" />
        ))}
        {thesis.stages.map((s) => (
          <Pill key={s} label={s} color="violet" />
        ))}
        {thesis.market_type && <Pill label={thesis.market_type} color="sky" />}
        {thesis.founder_profile.map((s) => (
          <Pill key={s} label={s} color="emerald" />
        ))}
      </div>

      {/* Startup cards */}
      {candidates.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <p className="text-4xl mb-3">🔍</p>
          <p className="font-medium">No startups found</p>
          <p className="text-sm mt-1">Try broadening your thesis criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {candidates.map((startup, i) => (
            <StartupCard
              key={startup.id}
              startup={startup}
              rank={i + 1}
              isBest={startup.id === best_startup?.id}
              onViewMemo={startup.id === best_startup?.id ? () => router.push("/memo") : undefined}
            />
          ))}
        </div>
      )}

      {/* Quick links */}
      {best_startup && (
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => router.push("/memo")}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            View Investment Memo →
          </button>
          <button
            onClick={() => router.push("/drift")}
            className="bg-white border border-slate-200 hover:border-slate-300 text-slate-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Check Narrative Drift →
          </button>
        </div>
      )}

      {/* Pipeline trace */}
      {pipeline_trace.length > 0 && <PipelineTrace traces={pipeline_trace} />}
    </div>
  );
}

function Pill({ label, color }: { label: string; color: "indigo" | "violet" | "sky" | "emerald" }) {
  const colors = {
    indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
    violet: "bg-violet-50 text-violet-700 border-violet-200",
    sky: "bg-sky-50 text-sky-700 border-sky-200",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };
  return (
    <span className={`text-xs font-medium border px-2.5 py-1 rounded-full ${colors[color]}`}>
      {label}
    </span>
  );
}
