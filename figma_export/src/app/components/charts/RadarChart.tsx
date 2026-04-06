import {
  RadarChart as RechartsRadar,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Company, Dimension } from "../../data/mockData";

interface RadarChartProps {
  dimensions: Dimension[];
  companies: Company[];
}

export function RadarChart({ dimensions, companies }: RadarChartProps) {
  const data = dimensions.map((dim) => {
    const point: Record<string, string | number> = { dimension: dim.name };
    companies.forEach((c) => {
      point[c.name] = dim.scores[c.id] ?? 0;
    });
    return point;
  });

  const colors = companies.map((c) => c.color);

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadar data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#ebe8e3" strokeWidth={0.8} />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: "#66605A", fontSize: 11 }}
          />
          <PolarRadiusAxis
            domain={[0, 100]}
            tick={{ fill: "#66605A", fontSize: 10 }}
          />
          {companies.map((c, i) => (
            <Radar
              key={c.id}
              name={c.name}
              dataKey={c.name}
              stroke={colors[i]}
              fill={colors[i]}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          ))}
          <Tooltip />
          <Legend />
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}
