import type { Company, Dimension } from "../../data/mockData";

interface ComparisonTableCardProps {
  companies: Company[];
  dimensions: Dimension[];
}

export function ComparisonTableCard({ companies, dimensions }: ComparisonTableCardProps) {
  if (companies.length === 0 || dimensions.length === 0) return null;

  // For each dimension, find the winner (highest score)
  const winnerPerDim: Record<string, string> = {};
  for (const dim of dimensions) {
    let best = -1;
    let bestId = "";
    for (const [companyId, score] of Object.entries(dim.scores)) {
      if (score > best) {
        best = score;
        bestId = companyId;
      }
    }
    winnerPerDim[dim.name] = bestId;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-[#D9D0C7]">
            <th className="text-left py-2 pr-4 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide min-w-[140px]">
              Dimension
            </th>
            {companies.map((c) => (
              <th
                key={c.id}
                className="text-center py-2 px-3 text-[11px] font-semibold uppercase tracking-wide min-w-[90px]"
                style={{ color: c.color }}
              >
                {c.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#EBE8E3]">
          {dimensions.map((dim) => {
            const winnerId = winnerPerDim[dim.name];
            return (
              <tr key={dim.name} className="hover:bg-[#FFF9F5] transition-colors">
                <td className="py-2.5 pr-4 text-xs text-[#1A1816] font-medium">{dim.name}</td>
                {companies.map((c) => {
                  const score = dim.scores[c.id] ?? null;
                  const isWinner = c.id === winnerId;
                  return (
                    <td key={c.id} className="py-2.5 px-3 text-center">
                      <span
                        className={`inline-block text-xs font-semibold px-2 py-0.5 rounded ${
                          isWinner
                            ? "text-white"
                            : "text-[#66605A] bg-[#F2EDE8]"
                        }`}
                        style={isWinner ? { backgroundColor: c.color } : undefined}
                      >
                        {score != null ? score : "—"}
                      </span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-[11px] text-[#A89E94] mt-3">
        Winner per row highlighted. Scores 0–100 based on customer reviews.
      </p>
    </div>
  );
}
