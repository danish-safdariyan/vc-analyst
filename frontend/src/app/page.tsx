"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { runAnalysis, saveResult, clearResult, DEMO_MODE } from "@/lib/api";

const EXAMPLES = [
  "Pre-seed developer tools startups with strong technical founders.",
  "Seed-stage B2B SaaS in vertical markets targeting enterprise buyers.",
  "Series A AI infrastructure companies with product-led growth and high NPS.",
];

const PIPELINE_STEPS = [
  { id: "parse_thesis", label: "Parsing thesis…" },
  { id: "discover_startups", label: "Discovering startups…" },
  { id: "score_startups", label: "Scoring thesis matches…" },
  { id: "generate_memo", label: "Generating investment memo…" },
  { id: "check_drift", label: "Checking narrative drift…" },
];

export default function ThesisPage() {
  const router = useRouter();
  const [thesis, setThesis] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(-1);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!thesis.trim()) return;

    setLoading(true);
    setError(null);
    setStep(0);
    clearResult(); // wipe any stale cached result before the new run

    // Simulate step progress while the API call runs
    const stepInterval = setInterval(() => {
      setStep((s) => (s < PIPELINE_STEPS.length - 1 ? s + 1 : s));
    }, 1800);

    try {
      const result = await runAnalysis(thesis.trim());
      clearInterval(stepInterval);
      setStep(PIPELINE_STEPS.length);
      saveResult(result);
      router.push("/results");
    } catch (err) {
      clearInterval(stepInterval);
      setStep(-1);
      setError(err instanceof Error ? err.message : "Something went wrong. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-16">
      {/* Demo mode banner */}
      {DEMO_MODE && (
        <div className="mb-6 flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-2.5 rounded-xl">
          <span className="text-base">🎭</span>
          <span>
            <strong>Demo mode</strong> — running offline with pre-baked fixture data.
            Set <code className="bg-amber-100 px-1 rounded">NEXT_PUBLIC_DEMO_MODE=false</code> to use the live backend.
          </span>
        </div>
      )}

      {/* Hero */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-indigo-600 rounded-xl mb-4">
          <span className="text-white text-xl">◆</span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900">VC Analyst AI</h1>
        <p className="mt-2 text-slate-500">
          Enter your fund thesis. Get ranked startup matches, an investment memo,
          and narrative drift analysis — in seconds.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Fund Thesis
        </label>
        <textarea
          value={thesis}
          onChange={(e) => setThesis(e.target.value)}
          disabled={loading}
          rows={4}
          placeholder="Describe your investment thesis in plain English…"
          className="w-full resize-none rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 transition"
        />

        {/* Example chips */}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-slate-400">Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              disabled={loading}
              onClick={() => setThesis(ex)}
              className="text-xs text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-full transition-colors disabled:opacity-50"
            >
              {ex.slice(0, 40)}…
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
            {error}
          </div>
        )}

        {/* Loading steps */}
        {loading && (
          <div className="mt-5 space-y-2">
            {PIPELINE_STEPS.map((s, i) => {
              const done = i < step;
              const active = i === step;
              return (
                <div key={s.id} className="flex items-center gap-3 text-sm">
                  <span className="w-5 text-center">
                    {done ? (
                      <span className="text-emerald-500">✓</span>
                    ) : active ? (
                      <span className="inline-block w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <span className="text-slate-300">○</span>
                    )}
                  </span>
                  <span className={done ? "text-slate-400 line-through" : active ? "text-indigo-600 font-medium" : "text-slate-400"}>
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !thesis.trim()}
          className="mt-5 w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
        >
          {loading ? "Analyzing…" : "Run Analysis →"}
        </button>
      </form>

      {/* Info chips */}
      <div className="mt-6 flex justify-center gap-4 text-xs text-slate-400">
        <span>◆ Thesis parsing</span>
        <span>◆ Crustdata discovery</span>
        <span>◆ LLM scoring</span>
        <span>◆ Memo generation</span>
        <span>◆ Drift detection</span>
      </div>
    </div>
  );
}
