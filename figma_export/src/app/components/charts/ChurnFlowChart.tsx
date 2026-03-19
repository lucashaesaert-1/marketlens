import { Sankey, ResponsiveContainer, Tooltip } from "recharts";
import type { ChurnFlow } from "../../data/mockData";
import type { Company } from "../../data/mockData";

interface ChurnFlowChartProps {
  data: ChurnFlow[];
  companies: Company[];
}

export function ChurnFlowChart({ data, companies }: ChurnFlowChartProps) {
  const nameToIndex = Object.fromEntries(companies.map((c, i) => [c.name, i]));
  const nodes = companies.map((c) => ({
    name: c.name,
    fill: c.color,
  }));

  const links = data
    .filter((d) => nameToIndex[d.source] !== undefined && nameToIndex[d.target] !== undefined)
    .map((d) => ({
      source: nameToIndex[d.source],
      target: nameToIndex[d.target],
      value: d.value,
    }));

  const sankeyData = { nodes, links };

  return (
    <div className="w-full h-[350px]">
      <ResponsiveContainer width="100%" height="100%">
        <Sankey
          data={sankeyData}
          node={{ stroke: "#fff", strokeWidth: 2 }}
          link={{ stroke: "#94a3b8", strokeOpacity: 0.5 }}
        >
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const p = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
                    <p className="font-semibold text-slate-900">
                      {p.source} → {p.target}
                    </p>
                    <p className="text-sm text-slate-600 mt-1">
                      Migration: {p.value}%
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
        </Sankey>
      </ResponsiveContainer>
    </div>
  );
}
