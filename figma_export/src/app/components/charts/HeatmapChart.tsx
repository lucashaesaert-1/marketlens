import type { Company, Dimension } from "../../data/mockData";

interface HeatmapChartProps {
  dimensions: Dimension[];
  companies: Company[];
}

function getHeatStyle(value: number): { backgroundColor: string; color: string } {
  if (value >= 80) return { backgroundColor: "#0d7680", color: "#fff" };
  if (value >= 70) return { backgroundColor: "#2e9e9e", color: "#fff" };
  if (value >= 60) return { backgroundColor: "#85c5c9", color: "#1a3a3f" };
  if (value >= 50) return { backgroundColor: "#f0c667", color: "#5d3e00" };
  if (value >= 40) return { backgroundColor: "#e8955a", color: "#5d1e00" };
  return { backgroundColor: "#c0392b", color: "#fff" };
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
                      className="inline-flex items-center justify-center min-w-[48px] h-8 rounded text-sm font-medium"
                      style={getHeatStyle(score)}
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
      <div className="mt-3 flex gap-3 justify-center items-center text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "#c0392b" }} />
          <span>0–40</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "#e8955a" }} />
          <span>40–50</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "#f0c667" }} />
          <span>50–60</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "#85c5c9" }} />
          <span>60–70</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: "#0d7680" }} />
          <span>80–100</span>
        </div>
      </div>
    </div>
  );
}
