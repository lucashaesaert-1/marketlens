import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { DimensionDelta } from "../../data/mockData";
import type { Company } from "../../data/mockData";

interface DimensionDeltasChartProps {
  data: DimensionDelta[];
  companies: Company[];
}

export function DimensionDeltasChart({ data, companies }: DimensionDeltasChartProps) {
  // Transform to grouped format: [{ dimension, CompanyA: delta, CompanyB: delta, ... }]
  const dims = [...new Set(data.map((d) => d.dimension))];
  const chartData = dims.map((dim) => {
    const row: Record<string, string | number> = { dimension: dim };
    companies.forEach((c) => {
      const d = data.find((x) => x.dimension === dim && x.companyId === c.id);
      row[c.name] = d?.delta ?? 0;
    });
    return row;
  });

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="dimension"
            angle={-35}
            textAnchor="end"
            height={80}
            tick={{ fill: "#64748b", fontSize: 11 }}
          />
          <YAxis
            label={{ value: "Delta vs Benchmark", angle: -90, position: "insideLeft" }}
            tick={{ fill: "#64748b", fontSize: 12 }}
          />
          <Tooltip />
          <Legend />
          {companies.map((c) => (
            <Bar key={c.id} dataKey={c.name} name={c.name} fill={c.color}>
              {chartData.map((entry, i) => {
                const val = entry[c.name] as number;
                return (
                  <Cell
                    key={i}
                    fill={val >= 0 ? c.color : "#f43f5e"}
                    opacity={val >= 0 ? 1 : 0.8}
                  />
                );
              })}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
