import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from "recharts";
import { Company, SentimentTrend } from "../data/mockData";

type TimeWindow = "6M" | "1Y" | "2Y";
const TIME_WINDOWS: { key: TimeWindow; label: string; months: number }[] = [
  { key: "6M", label: "6M", months: 6 },
  { key: "1Y", label: "1Y", months: 12 },
  { key: "2Y", label: "2Y", months: 24 },
];

interface SentimentAnalysisProps {
  trends: SentimentTrend[];
  companies: Company[];
}

export function SentimentAnalysis({ trends, companies }: SentimentAnalysisProps) {
  const [timeWindow, setTimeWindow] = useState<TimeWindow>("1Y");

  // Slice to selected window (if data has fewer points than the window, show all)
  const windowMonths = TIME_WINDOWS.find((w) => w.key === timeWindow)?.months ?? 12;
  const sliced = trends.length > windowMonths ? trends.slice(-windowMonths) : trends;

  // Convert sentiment scale from -1 to 1 → 0 to 100 for better visualization
  const data = sliced.map((trend) => {
    const converted: any = { month: trend.month };
    companies.forEach((company) => {
      const value = trend[company.id] as number;
      // Convert -1 to 1 scale to 0 to 100 (where 50 is neutral)
      converted[company.id] = ((value + 1) / 2) * 100;
    });
    return converted;
  });

  return (
    <div className="w-full flex flex-col gap-2">
      {/* Time window toggle */}
      <div className="flex items-center gap-1 self-end">
        {TIME_WINDOWS.map((w) => (
          <button
            key={w.key}
            type="button"
            onClick={() => setTimeWindow(w.key)}
            className={`px-2.5 py-0.5 text-xs rounded border transition-colors ${
              timeWindow === w.key
                ? "border-[#990F3D] bg-[#990F3D] text-white"
                : "border-[#D9D0C7] text-[#66605A] hover:border-[#990F3D] hover:text-[#990F3D]"
            }`}
          >
            {w.label}
          </button>
        ))}
      </div>
      <div className="h-[320px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 16, bottom: 40, left: 0 }}
        >
          <CartesianGrid strokeDasharray="none" stroke="#ebe8e3" strokeWidth={0.8} />
          <XAxis
            dataKey="month"
            tick={{ fill: "#66605A", fontSize: 11 }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#66605A", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={32}
            tickFormatter={(v: number) => `${v}`}
          />
          <ReferenceLine y={50} stroke="#D9D0C7" strokeDasharray="4 2" label={{ value: "neutral", position: "insideTopRight", fontSize: 10, fill: "#A89E94" }} />
          <Tooltip
            contentStyle={{ border: "1px solid #D9D0C7", borderRadius: 4, fontSize: 12 }}
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-3 shadow-lg border border-[#D9D0C7]" style={{ borderRadius: 4 }}>
                    <p className="font-semibold text-[#1A1816] mb-2 text-xs">{label}</p>
                    {payload.map((entry, index) => {
                      const company = companies.find((c) => c.id === entry.dataKey);
                      return (
                        <div key={index} className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color as string }} />
                            <span className="text-xs text-[#66605A]">{company?.name}</span>
                          </div>
                          <span className="text-xs font-medium text-[#1A1816]">
                            {typeof entry.value === "number" ? entry.value.toFixed(1) : entry.value}
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
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 11, paddingTop: 8, paddingBottom: 4 }}
            formatter={(value: string) => companies.find((c) => c.id === value)?.name ?? value}
          />
          {companies.map((company) => (
            <Line
              key={company.id}
              type="monotone"
              dataKey={company.id}
              stroke={company.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
