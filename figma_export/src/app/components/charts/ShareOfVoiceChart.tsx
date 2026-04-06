import { Treemap, ResponsiveContainer, Tooltip } from "recharts";
import type { ShareOfVoiceItem } from "../../data/mockData";
import type { Company } from "../../data/mockData";

interface ShareOfVoiceChartProps {
  data: ShareOfVoiceItem[];
  companies: Company[];
}

export function ShareOfVoiceChart({ data, companies }: ShareOfVoiceChartProps) {
  const colorMap = Object.fromEntries(companies.map((c) => [c.name, c.color]));

  const treeData = {
    name: "root",
    children: data.map((d) => ({
      name: d.name,
      size: d.size,
      value: d.value,
      fill: colorMap[d.name] || "#64748b",
    })),
  };

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={[treeData]}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#fff"
          type="nest"
        >
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const p = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-[#D9D0C7]">
                    <p className="font-semibold text-[#1A1816]">{p.name}</p>
                    <p className="text-sm text-[#66605A] mt-1">
                      Reviews: {p.size?.toLocaleString()}
                    </p>
                    <p className="text-sm text-[#66605A]">
                      Share: {p.value}%
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}
