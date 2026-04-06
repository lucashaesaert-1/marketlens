import { Insight } from "../data/mockData";
import { TrendingUp, AlertTriangle, Zap, ArrowUpRight } from "lucide-react";

interface InsightsPanelProps {
  insights: Insight[];
}

export function InsightsPanel({ insights }: InsightsPanelProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {insights.map((insight, idx) => (
        <InsightCard key={idx} insight={insight} />
      ))}
    </div>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  const typeConfig = {
    opportunity: {
      icon: TrendingUp,
      accentColor: "#0D7680",
      iconColor: "text-[#0D7680]",
      labelText: "Opportunity",
      labelClass: "text-[#0D7680] border border-[#0D7680]/30",
    },
    risk: {
      icon: AlertTriangle,
      accentColor: "#990F3D",
      iconColor: "text-[#990F3D]",
      labelText: "Risk",
      labelClass: "text-[#990F3D] border border-[#990F3D]/30",
    },
    trend: {
      icon: Zap,
      accentColor: "#593380",
      iconColor: "text-[#593380]",
      labelText: "Trend",
      labelClass: "text-[#593380] border border-[#593380]/30",
    },
  };

  const impactConfig = {
    high: { label: "High impact", class: "text-[#1A1816] border border-[#D9D0C7] font-medium" },
    medium: { label: "Medium impact", class: "text-[#66605A] border border-[#D9D0C7]" },
    low: { label: "Low impact", class: "text-[#A89E94] border border-[#D9D0C7]" },
  };

  const config = typeConfig[insight.type];
  const impact = impactConfig[insight.impact];
  const Icon = config.icon;

  return (
    <div
      className="bg-white border border-[#D9D0C7] p-5 hover:border-[#A89E94] transition-colors"
      style={{ borderLeft: `3px solid ${config.accentColor}` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <Icon className={`w-4 h-4 mt-0.5 ${config.iconColor} shrink-0`} />
        <div className="flex items-center gap-1.5 flex-wrap justify-end">
          {insight.source === "chat" && (
            <span className="text-xs px-2 py-0.5 rounded border border-violet-200 bg-violet-50 text-violet-700">
              Personalised
            </span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded ${config.labelClass}`}>
            {config.labelText}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-1.5">
        <h3 className="font-serif font-semibold text-slate-900 leading-snug">{insight.title}</h3>
        <p className="text-sm text-slate-600 leading-relaxed">{insight.description}</p>
      </div>

      {/* Metrics */}
      {insight.metrics && insight.metrics.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-100 space-y-1">
          {insight.metrics.map((metric, idx) => (
            <div key={idx} className="flex items-start gap-1.5">
              <ArrowUpRight className="w-3 h-3 text-slate-400 shrink-0 mt-0.5" />
              <span className="text-xs text-slate-500">{metric}</span>
            </div>
          ))}
        </div>
      )}

      {/* Impact */}
      <div className="mt-3">
        <span className={`inline-block text-xs px-2 py-0.5 rounded ${impact.class}`}>
          {impact.label}
        </span>
      </div>
    </div>
  );
}
