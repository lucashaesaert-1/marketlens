import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Company, SentimentTrend } from "../data/mockData";

interface SentimentAnalysisProps {
  trends: SentimentTrend[];
  companies: Company[];
}

export function SentimentAnalysis({ trends, companies }: SentimentAnalysisProps) {
  // Convert sentiment scale from -1 to 1 → 0 to 100 for better visualization
  const data = trends.map((trend) => {
    const converted: any = { month: trend.month };
    companies.forEach((company) => {
      const value = trend[company.id] as number;
      // Convert -1 to 1 scale to 0 to 100 (where 50 is neutral)
      converted[company.id] = ((value + 1) / 2) * 100;
    });
    return converted;
  });

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 20, bottom: 40, left: 20 }}
        >
          <CartesianGrid strokeDasharray="none" stroke="#ebe8e3" strokeWidth={0.8} />
          <XAxis
            dataKey="month"
            tick={{ fill: "#66605A", fontSize: 12 }}
            label={{
              value: "Month",
              position: "bottom",
              offset: 20,
              style: { fill: "#66605A", fontSize: 12 },
            }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#66605A", fontSize: 12 }}
            label={{
              value: "Sentiment Score (0-100)",
              angle: -90,
              position: "left",
              style: { fill: "#66605A", fontSize: 12 },
            }}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-[#D9D0C7]">
                    <p className="font-semibold text-[#1A1816] mb-2">{label}</p>
                    {payload.map((entry, index) => {
                      const company = companies.find((c) => c.id === entry.dataKey);
                      return (
                        <div key={index} className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-sm text-[#66605A]">
                              {company?.name}
                            </span>
                          </div>
                          <span className="text-sm font-medium text-[#1A1816]">
                            {entry.value?.toFixed(1)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                );
              }
              return null;
            }}
          />
          {companies.map((company) => (
            <Line
              key={company.id}
              type="monotone"
              dataKey={company.id}
              stroke={company.color}
              strokeWidth={2}
              dot={{ fill: company.color, r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Reference Line */}
      <div className="mt-2 flex items-center justify-center gap-2 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <div className="w-8 h-px bg-slate-300" />
          <span>50 = Neutral sentiment</span>
        </div>
      </div>
    </div>
  );
}
