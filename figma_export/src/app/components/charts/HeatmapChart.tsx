import type { Company, Dimension } from "../../data/mockData";

interface HeatmapChartProps {
  dimensions: Dimension[];
  companies: Company[];
}

function getHeatColor(value: number): string {
  if (value >= 80) return "bg-emerald-500";
  if (value >= 70) return "bg-emerald-400";
  if (value >= 60) return "bg-lime-400";
  if (value >= 50) return "bg-amber-400";
  if (value >= 40) return "bg-orange-400";
  return "bg-rose-400";
}

export function HeatmapChart({ dimensions, companies }: HeatmapChartProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left text-sm font-medium text-slate-600 bg-slate-50 border border-slate-200">
              Dimension
            </th>
            {companies.map((c) => (
              <th
                key={c.id}
                className="p-2 text-center text-sm font-medium text-slate-600 bg-slate-50 border border-slate-200 min-w-[80px]"
              >
                {c.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dimensions.map((dim, i) => (
            <tr key={dim.name} className={i % 2 === 0 ? "bg-white" : "bg-slate-50/50"}>
              <td className="p-2 text-sm text-slate-700 border border-slate-200">
                {dim.name}
              </td>
              {companies.map((c) => {
                const score = dim.scores[c.id] ?? 0;
                return (
                  <td
                    key={c.id}
                    className="p-2 text-center border border-slate-200"
                  >
                    <div
                      className={`inline-flex items-center justify-center min-w-[48px] h-8 rounded ${getHeatColor(score)} text-white text-sm font-medium`}
                    >
                      {score}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-3 flex gap-4 justify-center text-xs text-slate-500">
        <span>0–40</span>
        <span>40–60</span>
        <span>60–80</span>
        <span>80–100</span>
      </div>
    </div>
  );
}
