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
            <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 bg-slate-50">
              Dimension
            </th>
            <th className="text-center py-3 px-3 text-sm font-semibold text-slate-900 bg-slate-50 min-w-[100px]">
              Importance
            </th>
            {companies.map((company) => (
              <th
                key={company.id}
                className="text-center py-3 px-3 text-sm font-semibold text-slate-900 bg-slate-50 min-w-[120px]"
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
      <div className="mt-6 flex flex-wrap gap-6 justify-center text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300" />
          <span>Category Leader</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-100 border border-blue-300" />
          <span>Above Average</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-slate-100 border border-slate-300" />
          <span>Below Average</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-rose-100 border border-rose-300" />
          <span>Needs Improvement</span>
        </div>
      </div>
    </div>
  );
}

function ImportanceBadge({ importance }: { importance: number }) {
  let colorClass = "bg-slate-100 text-slate-700";
  if (importance >= 90) {
    colorClass = "bg-rose-100 text-rose-700 font-semibold";
  } else if (importance >= 85) {
    colorClass = "bg-orange-100 text-orange-700";
  } else if (importance >= 80) {
    colorClass = "bg-amber-100 text-amber-700";
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
  let bgClass = "bg-slate-100 border-slate-300 text-slate-700";
  let icon = <Minus className="w-3 h-3" />;

  if (isLeader) {
    bgClass = "bg-emerald-100 border-emerald-300 text-emerald-800 font-semibold";
    icon = <ArrowUp className="w-3 h-3" />;
  } else if (isLaggard) {
    bgClass = "bg-rose-100 border-rose-300 text-rose-800";
    icon = <ArrowDown className="w-3 h-3" />;
  } else if (isAboveAvg) {
    bgClass = "bg-blue-100 border-blue-300 text-blue-800";
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
