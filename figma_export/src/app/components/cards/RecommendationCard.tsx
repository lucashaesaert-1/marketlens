import { Award } from "lucide-react";

interface Recommendation {
  company: string;
  label: string;
  reason: string;
}

interface RecommendationCardProps {
  recommendations: Recommendation[];
  colorMap?: Record<string, string>;
}

export function RecommendationCard({ recommendations, colorMap = {} }: RecommendationCardProps) {
  if (recommendations.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {recommendations.map((rec, i) => {
        const color = colorMap[rec.company] ?? "#0D7680";
        return (
          <div
            key={i}
            className="border border-[#D9D0C7] rounded-sm p-4 hover:border-[#A89E94] transition-colors"
            style={{ borderLeft: `3px solid ${color}` }}
          >
            <div className="flex items-start gap-2 mb-2">
              <Award className="w-3.5 h-3.5 mt-0.5 shrink-0" style={{ color }} />
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide" style={{ color }}>
                  {rec.label}
                </p>
                <p className="text-sm font-semibold text-[#1A1816] mt-0.5">{rec.company}</p>
              </div>
            </div>
            <p className="text-xs text-[#66605A] leading-relaxed">{rec.reason}</p>
          </div>
        );
      })}
    </div>
  );
}
