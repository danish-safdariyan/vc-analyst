"use client";

import { useState } from "react";
import ChatMarkdown from "@/components/ChatMarkdown";
import { askAssistant, DEMO_MODE } from "@/lib/api";

type Turn = { question: string; answer: string; usedMock: boolean };

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;

    setLoading(true);
    setError(null);
    setInput("");

    try {
      const { reply, used_mock } = await askAssistant(q);
      setTurns((t) => [...t, { question: q, answer: reply, usedMock: used_mock }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-12">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Ask the analyst</h1>
        <p className="mt-2 text-slate-500 text-sm">
          Open-ended questions about markets, diligence, thesis, or startups — answered by the same
          model stack as the rest of VC Analyst AI.
        </p>
      </div>

      {DEMO_MODE && (
        <div className="mb-6 text-sm bg-amber-50 border border-amber-200 text-amber-800 px-4 py-2.5 rounded-xl">
          Demo mode is on: replies are placeholders unless you disable{" "}
          <code className="bg-amber-100 px-1 rounded">NEXT_PUBLIC_DEMO_MODE</code>.
        </div>
      )}

      <div className="space-y-6 mb-8 max-h-[50vh] overflow-y-auto pr-1">
        {turns.length === 0 && (
          <p className="text-center text-sm text-slate-400 py-8">
            Try: “What should I diligence first for a seed B2B SaaS?” or “How do I think about TAM for
            vertical software?”
          </p>
        )}
        {turns.map((t, i) => (
          <div key={i} className="space-y-3">
            <div className="bg-slate-100 rounded-xl px-4 py-3 text-sm text-slate-800">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">You</span>
              <p className="mt-1 whitespace-pre-wrap">{t.question}</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 shadow-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">
                  Assistant
                </span>
                {t.usedMock && (
                  <span className="text-[10px] uppercase tracking-wide text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                    Mock / offline
                  </span>
                )}
              </div>
              <ChatMarkdown>{t.answer}</ChatMarkdown>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
        <label className="block text-xs font-medium text-slate-600 mb-2">Your question</label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          rows={3}
          placeholder="Ask anything…"
          className="w-full resize-none rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
        />
        {error && (
          <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
            {error}
          </div>
        )}
        <div className="mt-4 flex gap-3">
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold py-2.5 rounded-xl transition-colors text-sm"
          >
            {loading ? "Thinking…" : "Send"}
          </button>
          {turns.length > 0 && (
            <button
              type="button"
              disabled={loading}
              onClick={() => setTurns([])}
              className="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 border border-slate-200 hover:bg-slate-50 disabled:opacity-50"
            >
              Clear
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
