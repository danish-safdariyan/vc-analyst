import type { StartupWithScore } from "@/lib/types";

function scoreBg(score: number) {
  if (score >= 75) return "bg-emerald-500";
  if (score >= 45) return "bg-amber-400";
  return "bg-rose-400";
}

function scoreText(score: number) {
  if (score >= 75) return "text-emerald-600 bg-emerald-50 border-emerald-200";
  if (score >= 45) return "text-amber-600 bg-amber-50 border-amber-200";
  return "text-rose-600 bg-rose-50 border-rose-200";
}

function DimBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-slate-500 shrink-0">{label}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${scoreBg(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="w-7 text-right text-slate-600 font-medium">{Math.round(value)}</span>
    </div>
  );
}

interface Props {
  startup: StartupWithScore;
  rank: number;
  isBest?: boolean;
  onViewMemo?: () => void;
}

export default function StartupCard({ startup, rank, isBest, onViewMemo }: Props) {
  const dims = startup.fit_dimensions;

  return (
    <div
      className={`bg-white rounded-xl border p-5 flex flex-col gap-4 transition-shadow hover:shadow-md ${
        isBest ? "border-indigo-300 ring-1 ring-indigo-200" : "border-slate-200"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {isBest && (
              <span className="text-xs font-semibold bg-indigo-600 text-white px-2 py-0.5 rounded-full">
                Best Match
              </span>
            )}
            <span className="text-xs text-slate-400">#{rank}</span>
          </div>
          <h3 className="font-semibold text-slate-900 text-lg mt-0.5 truncate">{startup.name}</h3>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
              {startup.stage}
            </span>
            <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">
              {startup.sector}
            </span>
            <span className="text-xs text-slate-400">{startup.geography}</span>
          </div>
        </div>

        {/* Score badge */}
        <div
          className={`shrink-0 w-14 h-14 rounded-xl border flex flex-col items-center justify-center ${scoreText(
            startup.fit_score
          )}`}
        >
          <span className="text-xl font-bold leading-none">{Math.round(startup.fit_score)}</span>
          <span className="text-[10px] mt-0.5 opacity-70">/ 100</span>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-slate-600 line-clamp-2">{startup.description}</p>

      {/* Dimension bars */}
      <div className="flex flex-col gap-1.5">
        <DimBar label="Sector fit" value={dims.sector_fit} />
        <DimBar label="Stage fit" value={dims.stage_fit} />
        <DimBar label="Team fit" value={dims.team_fit} />
        <DimBar label="Signal strength" value={dims.signal_strength} />
        <DimBar label="Market reasoning" value={dims.market_reasoning} />
      </div>

      {/* Signals */}
      {startup.signals.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {startup.signals.slice(0, 3).map((s, i) => (
            <span key={i} className="text-xs bg-slate-50 border border-slate-200 text-slate-600 px-2 py-0.5 rounded-full">
              {s}
            </span>
          ))}
        </div>
      )}

      {/* Explanation */}
      {startup.explanation && (
        <p className="text-xs text-slate-500 italic border-t border-slate-100 pt-3">
          {startup.explanation}
        </p>
      )}

      {/* Actions */}
      {isBest && onViewMemo && (
        <button
          onClick={onViewMemo}
          className="mt-auto w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium py-2 rounded-lg transition-colors"
        >
          View Investment Memo →
        </button>
      )}
    </div>
  );
}
