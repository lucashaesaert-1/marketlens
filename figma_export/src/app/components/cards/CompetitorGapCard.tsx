import { AlertTriangle, TrendingUp } from "lucide-react";

interface GapItem {
  theme: string;
  competitor_mentions: string[];
  focal_status: string;
  impact: string;
  suggestion: string;
}

interface CompetitorGapCardProps {
  gaps: GapItem[];
  focalCompany: string;
}

const impactColors: Record<string, { bg: string; text: string; border: string }> = {
  high:   { bg: "#FAE8ED", text: "#990F3D", border: "#990F3D" },
  medium: { bg: "#FEF0E6", text: "#C05A0B", border: "#F2720C" },
  low:    { bg: "#F2EDE8", text: "#66605A", border: "#D9D0C7" },
};

export function CompetitorGapCard({ gaps, focalCompany }: CompetitorGapCardProps) {
  if (gaps.length === 0) return null;

  return (
    <div className="space-y-3">
      {gaps.map((gap, i) => {
        const colors = impactColors[gap.impact] ?? impactColors.low;
        return (
          <div
            key={i}
            className="border border-[#D9D0C7] rounded-sm p-4 hover:border-[#A89E94] transition-colors"
            style={{ borderLeft: `3px solid ${colors.border}` }}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" style={{ color: colors.text }} />
                <span className="text-sm font-semibold text-[#1A1816]">{gap.theme}</span>
              </div>
              <span
                className="text-[11px] font-semibold px-2 py-0.5 rounded shrink-0"
                style={{ backgroundColor: colors.bg, color: colors.text }}
              >
                {gap.impact.charAt(0).toUpperCase() + gap.impact.slice(1)} impact
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5 mb-2">
              <span className="text-[11px] text-[#66605A]">Competitors praised for this:</span>
              {gap.competitor_mentions.map((c) => (
                <span key={c} className="text-[11px] bg-[#E6F5F6] text-[#0D7680] px-2 py-0.5 rounded">
                  {c}
                </span>
              ))}
              <span className="text-[11px] bg-[#FAE8ED] text-[#990F3D] px-2 py-0.5 rounded">
                {focalCompany}: {gap.focal_status}
              </span>
            </div>

            <div className="flex items-start gap-1.5">
              <TrendingUp className="w-3 h-3 text-[#0D7680] shrink-0 mt-0.5" />
              <p className="text-xs text-[#66605A] leading-relaxed">{gap.suggestion}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
