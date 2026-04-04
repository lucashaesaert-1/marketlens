import type { FinanceQuote } from "../../data/mockData";
import { TrendingUp, TrendingDown } from "lucide-react";

interface FinanceDataCardProps {
  financeData: Record<string, FinanceQuote>;
}

function fmt(n: number | null, decimals = 2): string {
  if (n == null) return "—";
  return n.toFixed(decimals);
}

export function FinanceDataCard({ financeData }: FinanceDataCardProps) {
  const entries = Object.entries(financeData);
  if (entries.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="text-left pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">Company</th>
            <th className="text-right pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">Ticker</th>
            <th className="text-right pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">Price</th>
            <th className="text-right pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">Change</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {entries.map(([company, q]) => {
            const isUp = (q.change ?? 0) >= 0;
            const changeColor = isUp ? "text-emerald-600" : "text-rose-600";
            const sign = isUp ? "+" : "";
            return (
              <tr key={company} className="hover:bg-slate-50 transition-colors">
                <td className="py-2.5 font-medium text-slate-800">{company}</td>
                <td className="py-2.5 text-right font-mono text-xs text-slate-400">
                  {q.ticker.split(":")[0]}
                </td>
                <td className="py-2.5 text-right font-semibold text-slate-900">
                  {q.price != null ? (
                    <>
                      <span className="text-xs text-slate-400 mr-1">{q.currency}</span>
                      {fmt(q.price)}
                    </>
                  ) : "—"}
                </td>
                <td className={`py-2.5 text-right ${changeColor}`}>
                  <div className="flex items-center justify-end gap-1">
                    {q.change != null && (
                      isUp ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />
                    )}
                    {q.pct_change != null
                      ? `${sign}${fmt(q.pct_change, 1)}%`
                      : q.change != null
                      ? `${sign}${fmt(q.change)}`
                      : "—"}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-xs text-slate-400 mt-3">
        Live quotes via Google Finance · Prices may be delayed
      </p>
    </div>
  );
}
