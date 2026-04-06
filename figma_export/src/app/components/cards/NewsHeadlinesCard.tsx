import type { NewsHeadline } from "../../data/mockData";
import { TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";

interface NewsHeadlinesCardProps {
  headlines: NewsHeadline[];
  focalCompany: string;
}

const sentimentConfig = {
  positive: { icon: TrendingUp, color: "text-[#00994D]" },
  negative: { icon: TrendingDown, color: "text-[#990F3D]" },
  neutral:  { icon: Minus,       color: "text-[#A89E94]" },
};

export function NewsHeadlinesCard({ headlines, focalCompany }: NewsHeadlinesCardProps) {
  if (!headlines || headlines.length === 0) return null;

  return (
    <div className="divide-y divide-[#D9D0C7]">
      {headlines.map((h, i) => {
        const cfg = sentimentConfig[h.sentiment_hint] ?? sentimentConfig.neutral;
        const Icon = cfg.icon;
        return (
          <div key={i} className="py-3 flex items-start gap-3">
            <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${cfg.color}`} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-[#1A1816] leading-snug">{h.title}</p>
              {h.snippet && (
                <p className="text-xs text-[#66605A] mt-0.5 line-clamp-2">{h.snippet}</p>
              )}
              <div className="flex items-center gap-2 mt-1">
                {h.source && <span className="text-[11px] text-[#A89E94] uppercase tracking-wide">{h.source}</span>}
                {h.date && <span className="text-[11px] text-[#A89E94]">· {h.date}</span>}
              </div>
            </div>
            <ExternalLink className="w-3 h-3 text-[#A89E94] shrink-0 mt-0.5" />
          </div>
        );
      })}
    </div>
  );
}
