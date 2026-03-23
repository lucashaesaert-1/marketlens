import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PersonalizationData } from "../data/mockData";

export function PersonalizationSection({ data }: { data: PersonalizationData }) {
  const scores = data.chart_series?.priority_scores || [];
  const kpis = data.suggested_kpis || [];
  const focus = data.focus_dimensions || [];

  if (!data.narrative_summary && scores.length === 0 && kpis.length === 0 && focus.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6 border-t border-indigo-100 pt-6 mt-6">
      <div>
        <h2 className="font-semibold text-slate-900 text-lg">Personalized for you</h2>
        <p className="text-sm text-slate-500 mt-1">
          Based on your onboarding conversation (merged with your audience view — not financial advice).
        </p>
      </div>

      {data.narrative_summary && (
        <div className="bg-indigo-50/80 border border-indigo-100 rounded-xl p-4 text-sm text-slate-700">
          {data.narrative_summary}
        </div>
      )}

      {scores.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-medium text-slate-900 mb-4">Priority themes (0–100)</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scores} layout="vertical" margin={{ left: 24, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="score" fill="#4f46e5" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {focus.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {focus.map((f, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wide">Focus</p>
              <p className="font-semibold text-slate-900 mt-1">{f.label}</p>
              <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${f.relevance}%` }} />
              </div>
              {f.rationale && <p className="text-xs text-slate-600 mt-2">{f.rationale}</p>}
            </div>
          ))}
        </div>
      )}

      {kpis.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {kpis.map((k, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500">{k.name}</p>
              <p className="text-2xl font-semibold text-slate-900 mt-1">{k.value}</p>
              {k.hint && <p className="text-xs text-slate-500 mt-2">{k.hint}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
