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
import type { PraiseComplaintTheme } from "../../data/mockData";
import type { Company } from "../../data/mockData";

interface PraiseComplaintChartProps {
  data: PraiseComplaintTheme[];
  companies: Company[];
}

export function PraiseComplaintChart({ data, companies }: PraiseComplaintChartProps) {
  const colorMap = Object.fromEntries(companies.map((c) => [c.id, c.color]));

  return (
    <div className="w-full h-[350px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 80, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" tick={{ fill: "#64748b", fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey="company"
            tick={{ fill: "#64748b", fontSize: 12 }}
            width={70}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const d = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
                    <p className="font-semibold text-slate-900">{d.company}</p>
                    <p className="text-sm text-emerald-600">Praise: {d.praise}</p>
                    <p className="text-sm text-rose-600">Complaint: {d.complaint}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar dataKey="praise" stackId="a" name="Praise themes" fill="#10b981">
            {data.map((entry, i) => (
              <Cell key={i} fill={colorMap[entry.companyId] || "#10b981"} />
            ))}
          </Bar>
          <Bar dataKey="complaint" stackId="a" name="Complaint themes" fill="#f43f5e">
            {data.map((entry, i) => (
              <Cell key={i} fill={colorMap[entry.companyId] || "#f43f5e"} opacity={0.7} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
