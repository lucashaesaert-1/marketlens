import type { GlassdoorSummary } from "../../data/mockData";

interface GlassdoorCardProps {
  glassdoorData: Record<string, GlassdoorSummary>;
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const frac = rating - full;
  return (
    <div className="flex items-center gap-0.5" title={`${rating} / 5`}>
      {[1, 2, 3, 4, 5].map((i) => {
        const fill =
          i <= full ? 1 : i === full + 1 && frac >= 0.5 ? 0.5 : 0;
        return (
          <span
            key={i}
            className={`text-sm ${
              fill === 1
                ? "text-[#F2720C]"
                : fill === 0.5
                ? "text-[#F2A86C]"
                : "text-[#D9D0C7]"
            }`}
          >
            ★
          </span>
        );
      })}
      <span className="ml-1 text-sm font-semibold text-slate-700">{rating.toFixed(1)}</span>
    </div>
  );
}

function RatingBar({ rating }: { rating: number | null }) {
  if (rating == null) return <span className="text-xs text-slate-400">No data</span>;
  const pct = Math.round((rating / 5) * 100);
  const barColor = pct >= 70 ? "#0D7680" : pct >= 50 ? "#F2720C" : "#990F3D";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-[#F2EDE8] overflow-hidden">
        <div className="h-full" style={{ width: `${pct}%`, backgroundColor: barColor }} />
      </div>
      <StarRating rating={rating} />
    </div>
  );
}

export function GlassdoorCard({ glassdoorData }: GlassdoorCardProps) {
  const entries = Object.entries(glassdoorData);
  if (entries.length === 0) return null;

  // Sort best → worst
  const sorted = [...entries].sort(
    (a, b) => (b[1].rating ?? 0) - (a[1].rating ?? 0)
  );

  return (
    <div className="space-y-4">
      {sorted.map(([company, gd]) => (
        <div key={company}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-slate-800">{company}</span>
          </div>
          <RatingBar rating={gd.rating} />
          {gd.snippet && (
            <p className="text-xs text-slate-500 mt-1.5 line-clamp-2 italic">
              "{gd.snippet}"
            </p>
          )}
        </div>
      ))}
      <p className="text-xs text-slate-400 pt-1">
        Employee ratings via Glassdoor · sourced from Google Search
      </p>
    </div>
  );
}
