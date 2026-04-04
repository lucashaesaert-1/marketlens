import type { NewsHeadline } from "../../data/mockData";
import { TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";

interface NewsHeadlinesCardProps {
  headlines: NewsHeadline[];
  focalCompany: string;
}

const sentimentConfig = {
  positive: {
    icon: TrendingUp,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-100",
  },
  negative: {
    icon: TrendingDown,
    color: "text-rose-600",
    bg: "bg-rose-50",
    border: "border-rose-100",
  },
  neutral: {
    icon: Minus,
    color: "text-slate-400",
    bg: "bg-slate-50",
    border: "border-slate-100",
  },
};

export function NewsHeadlinesCard({ headlines, focalCompany }: NewsHeadlinesCardProps) {
  if (!headlines || headlines.length === 0) return null;

  return (
    <div className="space-y-2">
      {headlines.map((h, i) => {
        const cfg = sentimentConfig[h.sentiment_hint] ?? sentimentConfig.neutral;
        const Icon = cfg.icon;
        return (
          <div
            key={i}
            className={`flex items-start gap-3 p-3 rounded-lg border ${cfg.bg} ${cfg.border}`}
          >
            <div className={`mt-0.5 shrink-0 ${cfg.color}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900 leading-snug">{h.title}</p>
              {h.snippet && (
                <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{h.snippet}</p>
              )}
              <div className="flex items-center gap-2 mt-1">
                {h.source && (
                  <span className="text-xs text-slate-400">{h.source}</span>
                )}
                {h.date && (
                  <span className="text-xs text-slate-300">· {h.date}</span>
                )}
              </div>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-slate-300 shrink-0 mt-0.5" />
          </div>
        );
      })}
      <p className="text-xs text-slate-400 pt-1">
        Live headlines via Google News · {focalCompany}
      </p>
    </div>
  );
}
