import { useState } from "react";
import type { FinanceQuote } from "../../data/mockData";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

interface StockChartCardProps {
  financeData: Record<string, FinanceQuote>;
  colorMap?: Record<string, string>;
}

type Mode = "actual" | "pct";

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function buildChartData(
  financeData: Record<string, FinanceQuote>,
  mode: Mode
): { date: string; [key: string]: number | string }[] {
  // Collect all dates across all companies
  const dateSet = new Set<string>();
  for (const q of Object.values(financeData)) {
    for (const pt of q.monthly_series ?? []) dateSet.add(pt.date);
  }
  const dates = Array.from(dateSet).sort();

  // Build a lookup: company → date → adjusted_close
  const lookup: Record<string, Record<string, number>> = {};
  const firstPrice: Record<string, number> = {};
  for (const [company, q] of Object.entries(financeData)) {
    lookup[company] = {};
    for (const pt of q.monthly_series ?? []) {
      lookup[company][pt.date] = pt.adjusted_close;
    }
    const prices = Object.values(lookup[company]);
    firstPrice[company] = prices.length > 0 ? prices[0] : 1;
  }

  return dates.map((date) => {
    const row: { date: string; [key: string]: number | string } = {
      date: formatDate(date),
    };
    for (const company of Object.keys(financeData)) {
      const price = lookup[company][date];
      if (price !== undefined) {
        row[company] =
          mode === "pct"
            ? parseFloat((((price - firstPrice[company]) / firstPrice[company]) * 100).toFixed(2))
            : parseFloat(price.toFixed(2));
      }
    }
    return row;
  });
}

const FALLBACK_COLORS = ["#0D7680", "#990F3D", "#593380", "#F2720C", "#00994D", "#0F5499"];

export function StockChartCard({ financeData, colorMap = {} }: StockChartCardProps) {
  const [mode, setMode] = useState<Mode>("pct");

  const companies = Object.keys(financeData);
  if (companies.length === 0) return null;

  const hasSeriesData = companies.some(
    (c) => (financeData[c].monthly_series ?? []).length > 0
  );

  const chartData = hasSeriesData ? buildChartData(financeData, mode) : [];

  // Collect PE/PEG for the table below the chart
  const fundamentals = companies
    .map((c) => ({
      company: c,
      ticker: financeData[c].ticker,
      price: financeData[c].price,
      pct_change: financeData[c].pct_change,
      pe: financeData[c].pe_ratio,
      peg: financeData[c].peg_ratio,
    }))
    .filter((r) => r.price != null);

  return (
    <div className="space-y-5">
      {/* Chart */}
      {hasSeriesData && (
        <>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#66605A]">View:</span>
            {(["pct", "actual"] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`text-xs px-3 py-1 rounded border transition-colors ${
                  mode === m
                    ? "border-[#0D7680] bg-[#E6F5F6] text-[#0D7680] font-medium"
                    : "border-[#D9D0C7] text-[#66605A] hover:text-[#1A1816]"
                }`}
              >
                {m === "pct" ? "% Change" : "Actual Price"}
              </button>
            ))}
          </div>

          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 16, left: 0 }}>
              <CartesianGrid strokeDasharray="none" stroke="#ebe8e3" strokeWidth={0.8} />
              <XAxis
                dataKey="date"
                tick={{ fill: "#66605A", fontSize: 10 }}
                interval={11}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#66605A", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => mode === "pct" ? `${v}%` : `$${v}`}
                width={mode === "pct" ? 44 : 52}
              />
              {mode === "pct" && <ReferenceLine y={0} stroke="#D9D0C7" strokeDasharray="4 2" />}
              <Tooltip
                contentStyle={{ border: "1px solid #D9D0C7", borderRadius: 4, fontSize: 12 }}
                formatter={(value: number, name: string) =>
                  [mode === "pct" ? `${value.toFixed(1)}%` : `$${value.toFixed(2)}`, name]
                }
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
              />
              {companies.map((company, i) => (
                <Line
                  key={company}
                  type="monotone"
                  dataKey={company}
                  stroke={colorMap[company] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length]}
                  strokeWidth={1.8}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <p className="text-[11px] text-[#A89E94]">
            5-year monthly adjusted close · Only publicly traded companies shown
          </p>
        </>
      )}

      {/* Fundamentals table */}
      {fundamentals.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#D9D0C7]">
              <th className="text-left pb-2 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide">Company</th>
              <th className="text-right pb-2 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide">Ticker</th>
              <th className="text-right pb-2 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide">Price</th>
              <th className="text-right pb-2 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide">1D %</th>
              <th className="text-right pb-2 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide">P/E</th>
              <th className="text-right pb-2 text-[11px] font-semibold text-[#66605A] uppercase tracking-wide">PEG</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D9D0C7]">
            {fundamentals.map(({ company, ticker, price, pct_change, pe, peg }) => {
              const isUp = (pct_change ?? 0) >= 0;
              return (
                <tr key={company} className="hover:bg-[#FFF9F5] transition-colors">
                  <td className="py-2 font-medium text-[#1A1816]">{company}</td>
                  <td className="py-2 text-right font-mono text-xs text-[#A89E94]">{ticker}</td>
                  <td className="py-2 text-right font-semibold text-[#1A1816]">
                    ${price?.toFixed(2) ?? "—"}
                  </td>
                  <td className={`py-2 text-right text-xs ${isUp ? "text-[#00994D]" : "text-[#990F3D]"}`}>
                    {pct_change != null ? `${isUp ? "+" : ""}${pct_change.toFixed(1)}%` : "—"}
                  </td>
                  <td className="py-2 text-right text-xs text-[#66605A]">
                    {pe != null ? pe.toFixed(1) : "—"}
                  </td>
                  <td className="py-2 text-right text-xs text-[#66605A]">
                    {peg != null ? peg.toFixed(2) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
