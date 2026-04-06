import { Company, Dimension } from "../data/mockData";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

interface DimensionBenchmarkingProps {
  dimensions: Dimension[];
  companies: Company[];
}

export function DimensionBenchmarking({
  dimensions,
  companies,
}: DimensionBenchmarkingProps) {
  // Sort dimensions by importance
  const sortedDimensions = [...dimensions].sort(
    (a, b) => b.importance - a.importance
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-3 px-4 text-xs font-semibold text-[#66605A] uppercase tracking-wide bg-[#F2EDE8]">
              Dimension
            </th>
            <th className="text-center py-3 px-3 text-xs font-semibold text-[#66605A] uppercase tracking-wide bg-[#F2EDE8] min-w-[100px]">
              Importance
            </th>
            {companies.map((company) => (
              <th
                key={company.id}
                className="text-center py-3 px-3 text-xs font-semibold text-[#66605A] uppercase tracking-wide bg-[#F2EDE8] min-w-[120px]"
              >
                {company.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedDimensions.map((dimension, idx) => {
            const scores = companies.map((c) => dimension.scores[c.id]);
            const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
            const maxScore = Math.max(...scores);
            const minScore = Math.min(...scores);

            return (
              <tr
                key={dimension.name}
                className={idx % 2 === 0 ? "bg-white" : "bg-slate-50"}
              >
                <td className="py-3 px-4 text-sm text-slate-900">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{dimension.name}</span>
                  </div>
                </td>
                <td className="py-3 px-3 text-center">
                  <ImportanceBadge importance={dimension.importance} />
                </td>
                {companies.map((company) => {
                  const score = dimension.scores[company.id];
                  const isLeader = score === maxScore;
                  const isLaggard = score === minScore && scores.length > 2;
                  const isAboveAvg = score > avgScore;

                  return (
                    <td key={company.id} className="py-3 px-3 text-center">
                      <ScoreCell
                        score={score}
                        isLeader={isLeader}
                        isLaggard={isLaggard}
                        isAboveAvg={isAboveAvg}
                        companyColor={company.color}
                      />
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-5 text-xs text-[#66605A]">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 border border-[#0D7680] bg-[#E6F5F6]" />
          <span>Category leader</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 border border-[#0F5499] bg-[#EAF0F8]" />
          <span>Above average</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 border border-[#D9D0C7] bg-[#F2EDE8]" />
          <span>Below average</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 border border-[#990F3D] bg-[#FAE8ED]" />
          <span>Needs improvement</span>
        </div>
      </div>
    </div>
  );
}

function ImportanceBadge({ importance }: { importance: number }) {
  let colorClass = "bg-[#F2EDE8] text-[#66605A]";
  if (importance >= 90) {
    colorClass = "bg-[#FAE8ED] text-[#990F3D] font-semibold";
  } else if (importance >= 85) {
    colorClass = "bg-[#FEF0E6] text-[#C05A0B]";
  } else if (importance >= 80) {
    colorClass = "bg-[#FEF7E6] text-[#8A6300]";
  }

  return (
    <div
      className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${colorClass}`}
    >
      <span>{importance}</span>
      <ArrowUp className="w-3 h-3" />
    </div>
  );
}

function ScoreCell({
  score,
  isLeader,
  isLaggard,
  isAboveAvg,
  companyColor,
}: {
  score: number;
  isLeader: boolean;
  isLaggard: boolean;
  isAboveAvg: boolean;
  companyColor: string;
}) {
  let bgClass = "bg-[#F2EDE8] border-[#D9D0C7] text-[#66605A]";
  let icon = <Minus className="w-3 h-3" />;

  if (isLeader) {
    bgClass = "bg-[#E6F5F6] border-[#0D7680] text-[#0D7680] font-semibold";
    icon = <ArrowUp className="w-3 h-3" />;
  } else if (isLaggard) {
    bgClass = "bg-[#FAE8ED] border-[#990F3D] text-[#990F3D]";
    icon = <ArrowDown className="w-3 h-3" />;
  } else if (isAboveAvg) {
    bgClass = "bg-[#EAF0F8] border-[#0F5499] text-[#0F5499]";
    icon = <ArrowUp className="w-3 h-3" />;
  }

  return (
    <div className="flex items-center justify-center gap-2">
      <div
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded border ${bgClass}`}
      >
        {icon}
        <span className="text-sm">{score}</span>
      </div>
    </div>
  );
}
