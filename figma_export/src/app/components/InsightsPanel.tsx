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
      bgColor: "bg-emerald-50",
      borderColor: "border-emerald-200",
      iconColor: "text-emerald-600",
      iconBg: "bg-emerald-100",
      labelColor: "text-emerald-700",
      labelBg: "bg-emerald-100",
    },
    risk: {
      icon: AlertTriangle,
      bgColor: "bg-rose-50",
      borderColor: "border-rose-200",
      iconColor: "text-rose-600",
      iconBg: "bg-rose-100",
      labelColor: "text-rose-700",
      labelBg: "bg-rose-100",
    },
    trend: {
      icon: Zap,
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      iconColor: "text-blue-600",
      iconBg: "bg-blue-100",
      labelColor: "text-blue-700",
      labelBg: "bg-blue-100",
    },
  };

  const config = typeConfig[insight.type];
  const Icon = config.icon;

  const impactConfig = {
    high: {
      label: "High Impact",
      color: "bg-slate-900 text-white",
    },
    medium: {
      label: "Medium Impact",
      color: "bg-slate-600 text-white",
    },
    low: {
      label: "Low Impact",
      color: "bg-slate-400 text-white",
    },
  };

  const impact = impactConfig[insight.impact];

  return (
    <div
      className={`${config.bgColor} border ${config.borderColor} rounded-lg p-5 hover:shadow-md transition-shadow`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className={`${config.iconBg} p-2 rounded-lg`}>
          <Icon className={`w-5 h-5 ${config.iconColor}`} />
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-medium px-2 py-1 rounded ${config.labelBg} ${config.labelColor}`}
          >
            {insight.type.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-2">
        <h3 className="font-semibold text-slate-900">{insight.title}</h3>
        <p className="text-sm text-slate-600 leading-relaxed">
          {insight.description}
        </p>
      </div>

      {/* Metrics */}
      {insight.metrics && insight.metrics.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <div className="space-y-1.5">
            {insight.metrics.map((metric, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <ArrowUpRight className="w-3 h-3 text-slate-400 flex-shrink-0" />
                <span className="text-xs text-slate-600">{metric}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Impact Badge */}
      <div className="mt-4">
        <span
          className={`inline-block text-xs font-medium px-3 py-1 rounded-full ${impact.color}`}
        >
          {impact.label}
        </span>
      </div>
    </div>
  );
}
