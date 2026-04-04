import { useParams } from "react-router";
import { useEffect, useState } from "react";
import { type Audience } from "../data/mockData";
import type { IndustryData } from "../data/mockData";
import { fetchIndustryData, downloadScoresCsv } from "../api";
import { PositioningMap } from "./PositioningMap";
import { SentimentAnalysis } from "./SentimentAnalysis";
import { DimensionBenchmarking } from "./DimensionBenchmarking";
import { InsightsPanel } from "./InsightsPanel";
import {
  RadarChart,
  HeatmapChart,
  PraiseComplaintChart,
  ShareOfVoiceChart,
  ChurnFlowChart,
  DimensionDeltasChart,
} from "./charts";
import { BarChart3, Target, TrendingUp, Lightbulb, Loader2, Copy, Download } from "lucide-react";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { PersonalizationSection } from "./PersonalizationSection";
import { DashboardChat } from "./DashboardChat";
import { NewsHeadlinesCard } from "./cards/NewsHeadlinesCard";
import { FinanceDataCard } from "./cards/FinanceDataCard";
import { GlassdoorCard } from "./cards/GlassdoorCard";

/** Which charts each audience sees. Investors: market share, churn, growth. Companies: praise/complaint, gaps, support. Customers: value, ease of use. */
const CHARTS_BY_AUDIENCE: Record<Audience, Set<string>> = {
  investors: new Set(["positioning", "sentiment", "shareOfVoice", "churnFlows", "dimensionBenchmarking", "newsHeadlines", "financeData"]),
  companies: new Set(["radar", "heatmap", "praiseComplaint", "dimensionDeltas", "dimensionBenchmarking", "glassdoorData"]),
  customers: new Set(["positioning", "radar", "praiseComplaint", "dimensionBenchmarking", "glassdoorData"]),
};

const BRIEF_INSIGHTS_KEY = "marketlens_brief_insights";

export function Dashboard() {
  const params = useParams();
  const industry = (params.industry as string) || "crm";
  const audience = (params.audience as Audience) || "investors";

  const [data, setData] = useState<IndustryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [briefInsights, setBriefInsights] = useState(
    () => typeof sessionStorage !== "undefined" && sessionStorage.getItem(BRIEF_INSIGHTS_KEY) === "1"
  );

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchIndustryData(industry)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [industry]);

  useEffect(() => {
    sessionStorage.setItem(BRIEF_INSIGHTS_KEY, briefInsights ? "1" : "0");
  }, [briefInsights]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
          <p className="text-slate-600">Loading {industry} analysis…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-8 max-w-md text-center">
          <p className="font-semibold text-rose-900">Failed to load data</p>
          <p className="text-sm text-rose-700 mt-2">{error}</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => {
              setError(null);
              setLoading(true);
              fetchIndustryData(industry)
                .then(setData)
                .catch((err) => setError((err as Error).message))
                .finally(() => setLoading(false));
            }}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const allInsights = data.insights[audience];
  const displayInsights = briefInsights ? allInsights.slice(0, 4) : allInsights;

  const copyInsightsText = () => {
    const text = displayInsights
      .map((i) => `• ${i.title}\n${i.description}${i.metrics?.length ? `\n  ${i.metrics.join("; ")}` : ""}`)
      .join("\n\n");
    void navigator.clipboard.writeText(text).then(
      () => {},
      () => alert("Could not copy to clipboard")
    );
  };

  return (
    <div className="max-w-[1600px] mx-auto space-y-6">
      {/* Mock data warning */}
      {data._meta?.isMock && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm text-amber-800 flex items-center gap-2">
          <span className="font-semibold">Demo data</span>
          — scores are template estimates. Run an analysis to load real review data.
        </div>
      )}
      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          icon={Target}
          label="Companies Analyzed"
          value={data.companies.length.toString()}
          sublabel="Market leaders"
        />
        <MetricCard
          icon={BarChart3}
          label="Total Reviews"
          value={formatNumber(
            data.companies.reduce((sum, c) => sum + c.reviewCount, 0)
          )}
          sublabel="Customer data points"
        />
        <MetricCard
          icon={TrendingUp}
          label="Dimensions Tracked"
          value={data.dimensions.length.toString()}
          sublabel="Competitive factors"
        />
        <MetricCard
          icon={Lightbulb}
          label="AI Insights"
          value={allInsights.length.toString()}
          sublabel={briefInsights ? "Showing brief subset" : "Actionable recommendations"}
        />
      </div>

      {/* Main Dashboard Grid - audience-specific */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {CHARTS_BY_AUDIENCE[audience].has("positioning") && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="mb-4">
              <h2 className="font-semibold text-slate-900">Competitive Positioning</h2>
              <p className="text-sm text-slate-500 mt-1">Price vs. Perceived Customer Value Matrix</p>
            </div>
            <PositioningMap companies={data.companies} />
          </div>
        )}
        {CHARTS_BY_AUDIENCE[audience].has("sentiment") && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="mb-4">
              <h2 className="font-semibold text-slate-900">Sentiment Trends</h2>
              <p className="text-sm text-slate-500 mt-1">6-month customer sentiment analysis</p>
            </div>
            <SentimentAnalysis trends={data.sentimentTrends} companies={data.companies} />
          </div>
        )}
      </div>

      {/* Radar & Heatmap - companies only */}
      {(CHARTS_BY_AUDIENCE[audience].has("radar") || CHARTS_BY_AUDIENCE[audience].has("heatmap")) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {CHARTS_BY_AUDIENCE[audience].has("radar") && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Radar: Dimension Comparison</h2>
                <p className="text-sm text-slate-500 mt-1">Per-company scores across dimensions</p>
              </div>
              <RadarChart dimensions={data.dimensions} companies={data.companies} />
            </div>
          )}
          {CHARTS_BY_AUDIENCE[audience].has("heatmap") && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Heatmap: Dimension x Company</h2>
                <p className="text-sm text-slate-500 mt-1">Score matrix (0-100)</p>
              </div>
              <HeatmapChart dimensions={data.dimensions} companies={data.companies} />
            </div>
          )}
        </div>
      )}

      {/* Praise vs Complaint & Share of Voice */}
      {(CHARTS_BY_AUDIENCE[audience].has("praiseComplaint") || CHARTS_BY_AUDIENCE[audience].has("shareOfVoice")) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {CHARTS_BY_AUDIENCE[audience].has("praiseComplaint") && data.praiseComplaintThemes && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Praise vs Complaint Themes</h2>
                <p className="text-sm text-slate-500 mt-1">Sentiment themes by company</p>
              </div>
              <PraiseComplaintChart data={data.praiseComplaintThemes} companies={data.companies} />
            </div>
          )}
          {CHARTS_BY_AUDIENCE[audience].has("shareOfVoice") && data.shareOfVoice && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Share of Voice</h2>
                <p className="text-sm text-slate-500 mt-1">Review volume by company</p>
              </div>
              <ShareOfVoiceChart data={data.shareOfVoice} companies={data.companies} />
            </div>
          )}
        </div>
      )}

      {/* Churn Flows & Dimension Deltas - investors & companies */}
      {(CHARTS_BY_AUDIENCE[audience].has("churnFlows") || CHARTS_BY_AUDIENCE[audience].has("dimensionDeltas")) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {CHARTS_BY_AUDIENCE[audience].has("churnFlows") && data.churnFlows && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Churn / Migration Flows</h2>
                <p className="text-sm text-slate-500 mt-1">Customer migration between competitors</p>
              </div>
              <ChurnFlowChart data={data.churnFlows} companies={data.companies} />
            </div>
          )}
          {CHARTS_BY_AUDIENCE[audience].has("dimensionDeltas") && data.dimensionDeltas && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Score Deltas vs Benchmark</h2>
                <p className="text-sm text-slate-500 mt-1">Dimension performance vs category average</p>
              </div>
              <DimensionDeltasChart data={data.dimensionDeltas} companies={data.companies} />
            </div>
          )}
        </div>
      )}

      {/* Google Finance + News — investors only */}
      {(CHARTS_BY_AUDIENCE[audience].has("financeData") || CHARTS_BY_AUDIENCE[audience].has("newsHeadlines")) && (
        (data.financeData && Object.keys(data.financeData).length > 0) ||
        (data.newsHeadlines && data.newsHeadlines.length > 0)
      ) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {CHARTS_BY_AUDIENCE[audience].has("financeData") && data.financeData && Object.keys(data.financeData).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Market Data</h2>
                <p className="text-sm text-slate-500 mt-1">Live stock quotes for public companies</p>
              </div>
              <FinanceDataCard financeData={data.financeData} />
            </div>
          )}
          {CHARTS_BY_AUDIENCE[audience].has("newsHeadlines") && data.newsHeadlines && data.newsHeadlines.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-slate-900">Recent News</h2>
                <p className="text-sm text-slate-500 mt-1">Latest headlines for the focal company</p>
              </div>
              <NewsHeadlinesCard
                headlines={data.newsHeadlines}
                focalCompany={data.companies[0]?.name ?? ""}
              />
            </div>
          )}
        </div>
      )}

      {/* Glassdoor employee ratings — companies + customers */}
      {CHARTS_BY_AUDIENCE[audience].has("glassdoorData") && data.glassdoorData && Object.keys(data.glassdoorData).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="mb-4">
            <h2 className="font-semibold text-slate-900">Employee Sentiment (Glassdoor)</h2>
            <p className="text-sm text-slate-500 mt-1">Aggregate employee ratings by company</p>
          </div>
          <GlassdoorCard glassdoorData={data.glassdoorData} />
        </div>
      )}

      {data.personalization && (
        <PersonalizationSection data={data.personalization} />
      )}

      {/* Dimension Benchmarking - all audiences */}
      {CHARTS_BY_AUDIENCE[audience].has("dimensionBenchmarking") && (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="mb-4">
          <h2 className="font-semibold text-slate-900">
            Dimension-by-Dimension Benchmarking
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Performance scores across key customer dimensions (0-100 scale)
          </p>
        </div>
        <DimensionBenchmarking
          dimensions={data.dimensions}
          companies={data.companies}
        />
      </div>
      )}

      {/* AI-Synthesized Insights */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="font-semibold text-slate-900">
              AI-Synthesized Insights
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Strategic insights tailored for {audience}
              {briefInsights && allInsights.length > 4 ? ` — showing ${displayInsights.length} of ${allInsights.length}` : ""}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Switch
                id="brief-insights"
                checked={briefInsights}
                onCheckedChange={setBriefInsights}
              />
              <Label htmlFor="brief-insights" className="text-xs text-slate-600 cursor-pointer">
                Executive brief
              </Label>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="text-xs h-8"
              onClick={() => void copyInsightsText()}
            >
              <Copy className="w-3.5 h-3.5 mr-1" />
              Copy
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="text-xs h-8"
              onClick={() =>
                void downloadScoresCsv(industry).catch((e: unknown) =>
                  alert(e instanceof Error ? e.message : "Export failed")
                )
              }
            >
              <Download className="w-3.5 h-3.5 mr-1" />
              Scores CSV
            </Button>
          </div>
        </div>
        <InsightsPanel insights={displayInsights} />
      </div>

      <DashboardChat industry={industry} audience={audience} />
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  sublabel,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sublabel: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-500">{label}</p>
          <p className="text-2xl font-semibold text-slate-900 mt-2">{value}</p>
          <p className="text-xs text-slate-400 mt-1">{sublabel}</p>
        </div>
        <div className="flex items-center justify-center w-10 h-10 bg-indigo-50 rounded-lg">
          <Icon className="w-5 h-5 text-indigo-600" />
        </div>
      </div>
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(0) + "K";
  }
  return num.toString();
}
