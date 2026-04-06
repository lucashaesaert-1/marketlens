import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ZAxis } from "recharts";
import { Company } from "../data/mockData";

interface PositioningMapProps {
  companies: Company[];
}

export function PositioningMap({ companies }: PositioningMapProps) {
  const data = companies.map((company) => ({
    x: company.price,
    y: company.perceivedValue,
    name: company.name,
    color: company.color,
    size: Math.log(company.reviewCount) * 100,
  }));

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 40, left: 40 }}
        >
          <CartesianGrid strokeDasharray="none" stroke="#ebe8e3" strokeWidth={0.8} />
          <XAxis
            type="number"
            dataKey="x"
            name="Price"
            domain={[0, 10]}
            label={{
              value: "Price Point (1-10)",
              position: "bottom",
              offset: 20,
              style: { fill: "#66605A", fontSize: 12 },
            }}
            tick={{ fill: "#66605A", fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Value"
            domain={[0, 10]}
            label={{
              value: "Perceived Customer Value (1-10)",
              angle: -90,
              position: "left",
              offset: 10,
              style: { fill: "#66605A", fontSize: 12 },
            }}
            tick={{ fill: "#66605A", fontSize: 12 }}
          />
          <ZAxis type="number" dataKey="size" range={[400, 1000]} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-[#D9D0C7]">
                    <p className="font-semibold text-[#1A1816]">{data.name}</p>
                    <p className="text-sm text-[#66605A] mt-1">
                      Price: {data.x.toFixed(1)}/10
                    </p>
                    <p className="text-sm text-[#66605A]">
                      Perceived Value: {data.y.toFixed(1)}/10
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter name="Companies" data={data}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 justify-center">
        {companies.map((company) => (
          <div key={company.id} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: company.color }}
            />
            <span className="text-sm text-[#66605A]">{company.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
