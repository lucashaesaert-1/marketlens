import { useParams, useNavigate } from "react-router";
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
import { BarChart3, Target, TrendingUp, Lightbulb, Loader2, Copy, Download, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "./ui/button";
import { PersonalizationSection } from "./PersonalizationSection";
import { DashboardChat } from "./DashboardChat";
import { NewsHeadlinesCard } from "./cards/NewsHeadlinesCard";
import { StockChartCard } from "./cards/StockChartCard";
import { GlassdoorCard } from "./cards/GlassdoorCard";

const CHARTS_BY_AUDIENCE: Record<Audience, Set<string>> = {
  investors: new Set(["positioning", "sentiment", "shareOfVoice", "churnFlows", "dimensionBenchmarking", "newsHeadlines", "financeData"]),
  companies: new Set(["radar", "heatmap", "praiseComplaint", "dimensionDeltas", "dimensionBenchmarking", "glassdoorData"]),
  customers: new Set(["positioning", "radar", "praiseComplaint", "dimensionBenchmarking", "glassdoorData"]),
};

const SHOW_INSIGHT_CARDS_KEY = "marketlens_show_insight_cards";

const AUDIENCE_TABS: { key: Audience; label: string }[] = [
  { key: "investors", label: "Investors" },
  { key: "companies", label: "Companies" },
  { key: "customers", label: "Customers" },
];

/** Thin rule separating chart sections — FT editorial style */
const RULE = "border-t border-[#D9D0C7]";
/** Source attribution line under every chart */
function Source({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-3 text-[11px] text-[#66605A] uppercase tracking-wide">
      {children}
    </p>
  );
}

export function Dashboard() {
  const params = useParams();
  const navigate = useNavigate();
  const industry = (params.industry as string) || "crm";
  const audience = (params.audience as Audience) || "investors";

  const [data, setData] = useState<IndustryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInsightCards, setShowInsightCards] = useState(
    () => typeof sessionStorage !== "undefined" ? sessionStorage.getItem(SHOW_INSIGHT_CARDS_KEY) !== "0" : true
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
    sessionStorage.setItem(SHOW_INSIGHT_CARDS_KEY, showInsightCards ? "1" : "0");
  }, [showInsightCards]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-[#990F3D] animate-spin" />
          <p className="text-[#66605A] text-sm">Loading {industry} analysis…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="border border-[#D9D0C7] border-l-4 border-l-[#990F3D] p-8 max-w-md">
          <p className="font-semibold text-[#1A1816]">Failed to load data</p>
          <p className="text-sm text-[#66605A] mt-2">{error}</p>
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

  if (!data) return null;

  const allInsights = data.insights[audience];

  const copyInsightsText = () => {
    const briefText = data?.executiveBrief ? `EXECUTIVE BRIEF\n${data.executiveBrief}\n\n` : "";
    const cardsText = allInsights
      .map((i) => `• ${i.title}\n${i.description}${i.metrics?.length ? `\n  ${i.metrics.join("; ")}` : ""}`)
      .join("\n\n");
    void navigator.clipboard.writeText(briefText + cardsText).then(() => {}, () => alert("Could not copy to clipboard"));
  };

  return (
    <div className="max-w-[1600px] mx-auto">

      {/* ── Audience tabs ── */}
      <div className="flex border-b border-[#D9D0C7]">
        {AUDIENCE_TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => navigate(`/${industry}/${key}`)}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              audience === key
                ? "border-b-2 border-[#990F3D] text-[#990F3D] -mb-px"
                : "text-[#66605A] hover:text-[#1A1816]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Demo data notice ── */}
      {data._meta?.isMock && (
        <div className="border-l-4 border-[#F2720C] bg-[#FFF9F5] px-4 py-2.5 mt-0 border-t border-[#D9D0C7]">
          <span className="text-sm text-[#1A1816]">
            <span className="font-semibold">Demo data</span> — scores are template estimates. Run an analysis to load real review data.
          </span>
        </div>
      )}

      {/* ── Key metrics ── */}
      <div className={`grid grid-cols-2 md:grid-cols-4 ${RULE} border-b border-[#D9D0C7] divide-x divide-[#D9D0C7]`}>
        <MetricCard icon={Target} label="Companies Analyzed" value={data.companies.length.toString()} sublabel="Market leaders" />
        <MetricCard icon={BarChart3} label="Total Reviews" value={formatNumber(data.companies.reduce((s, c) => s + c.reviewCount, 0))} sublabel="Customer data points" />
        <MetricCard icon={TrendingUp} label="Dimensions Tracked" value={data.dimensions.length.toString()} sublabel="Competitive factors" />
        <MetricCard icon={Lightbulb} label="AI Insights" value={allInsights.length.toString()} sublabel="Actionable recommendations" />
      </div>

      {/* ── Main chart grid ── */}
      <div className={`grid grid-cols-1 lg:grid-cols-2 ${RULE}
        [&>*]:border-b [&>*]:border-[#D9D0C7]
        [&>*:nth-child(odd)]:lg:border-r [&>*:nth-child(odd)]:lg:border-[#D9D0C7]
        [&>*:nth-child(odd)]:lg:pr-8
        [&>*:nth-child(even)]:lg:pl-8`}
      >
        {CHARTS_BY_AUDIENCE[audience].has("positioning") && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Competitive Positioning</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Price vs. perceived customer value</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <PositioningMap companies={data.companies} />
            </div>
            <Source>Source: Review scores · MarketLens AI analysis</Source>
          </div>
        )}

        {CHARTS_BY_AUDIENCE[audience].has("sentiment") && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Sentiment Trends</h2>
            <p className="text-sm text-[#66605A] mt-0.5">6-month customer sentiment index</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <SentimentAnalysis trends={data.sentimentTrends} companies={data.companies} />
            </div>
            <Source>Source: Google Trends · SerpAPI</Source>
          </div>
        )}

        {CHARTS_BY_AUDIENCE[audience].has("radar") && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Dimension Comparison</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Per-company scores across dimensions</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <RadarChart dimensions={data.dimensions} companies={data.companies} />
            </div>
            <Source>Source: Customer reviews · MarketLens AI scoring</Source>
          </div>
        )}

        {CHARTS_BY_AUDIENCE[audience].has("heatmap") && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Score Matrix</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Dimension × company heatmap (0–100)</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <HeatmapChart dimensions={data.dimensions} companies={data.companies} />
            </div>
            <Source>Source: Customer reviews · MarketLens AI scoring</Source>
          </div>
        )}

        {CHARTS_BY_AUDIENCE[audience].has("praiseComplaint") && data.praiseComplaintThemes && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Praise vs Complaint Themes</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Sentiment themes by company</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <PraiseComplaintChart data={data.praiseComplaintThemes} companies={data.companies} />
            </div>
            <Source>Source: Customer reviews · MarketLens AI NLP</Source>
          </div>
        )}

        {CHARTS_BY_AUDIENCE[audience].has("shareOfVoice") && data.shareOfVoice && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Share of Voice</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Review volume by company</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <ShareOfVoiceChart data={data.shareOfVoice} companies={data.companies} />
            </div>
            <Source>Source: Review volume · Google Trends · SerpAPI</Source>
          </div>
        )}

        {CHARTS_BY_AUDIENCE[audience].has("dimensionDeltas") && data.dimensionDeltas && (
          <div className="py-8 flex flex-col">
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">Score Deltas vs Benchmark</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Performance vs category average</p>
            <div className="flex-1 min-h-[300px] mt-5">
              <DimensionDeltasChart data={data.dimensionDeltas} companies={data.companies} />
            </div>
            <Source>Source: Customer reviews · MarketLens AI scoring</Source>
          </div>
        )}
      </div>

      {/* ── Finance + News (investors) ── */}
      {(CHARTS_BY_AUDIENCE[audience].has("financeData") || CHARTS_BY_AUDIENCE[audience].has("newsHeadlines")) &&
        ((data.financeData && Object.keys(data.financeData).length > 0) ||
          (data.newsHeadlines && data.newsHeadlines.length > 0)) && (
        <div className={`grid grid-cols-1 lg:grid-cols-2
          [&>*]:border-b [&>*]:border-[#D9D0C7]
          [&>*:nth-child(odd)]:lg:border-r [&>*:nth-child(odd)]:lg:border-[#D9D0C7]
          [&>*:nth-child(odd)]:lg:pr-8
          [&>*:nth-child(even)]:lg:pl-8`}
        >
          {CHARTS_BY_AUDIENCE[audience].has("financeData") && data.financeData && Object.keys(data.financeData).length > 0 && (
            <div className="py-8">
              <h2 className="text-base font-serif font-semibold text-[#1A1816]">Stock Performance</h2>
              <p className="text-sm text-[#66605A] mt-0.5">5-year price history · P/E and PEG ratios</p>
              <div className="mt-5">
                <StockChartCard
                  financeData={data.financeData}
                  colorMap={Object.fromEntries(data.companies.map(c => [c.name, c.color]))}
                />
              </div>
              <Source>Source: Alpha Vantage · Prices may be delayed 15 min</Source>
            </div>
          )}
          {CHARTS_BY_AUDIENCE[audience].has("newsHeadlines") && data.newsHeadlines && data.newsHeadlines.length > 0 && (
            <div className="py-8">
              <h2 className="text-base font-serif font-semibold text-[#1A1816]">Recent News</h2>
              <p className="text-sm text-[#66605A] mt-0.5">Latest headlines for the focal company</p>
              <div className="mt-5">
                <NewsHeadlinesCard headlines={data.newsHeadlines} focalCompany={data.companies[0]?.name ?? ""} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Glassdoor ── */}
      {CHARTS_BY_AUDIENCE[audience].has("glassdoorData") && data.glassdoorData && Object.keys(data.glassdoorData).length > 0 && (
        <div className={`${RULE} border-b border-[#D9D0C7] py-8`}>
          <h2 className="text-base font-serif font-semibold text-[#1A1816]">Employee Sentiment</h2>
          <p className="text-sm text-[#66605A] mt-0.5">Aggregate employee ratings by company</p>
          <div className="mt-5">
            <GlassdoorCard glassdoorData={data.glassdoorData} />
          </div>
          <Source>Source: Glassdoor · via Google Search · SerpAPI</Source>
        </div>
      )}

      {data.personalization && (
        <PersonalizationSection data={data.personalization} />
      )}

      {/* ── Dimension Benchmarking ── */}
      {CHARTS_BY_AUDIENCE[audience].has("dimensionBenchmarking") && (
        <div className={`${RULE} border-b border-[#D9D0C7] py-8`}>
          <h2 className="text-base font-serif font-semibold text-[#1A1816]">Dimension Benchmarking</h2>
          <p className="text-sm text-[#66605A] mt-0.5">Performance scores across key dimensions (0–100 scale)</p>
          <div className="mt-5">
            <DimensionBenchmarking dimensions={data.dimensions} companies={data.companies} />
          </div>
          <Source>Source: Customer reviews · MarketLens AI scoring</Source>
        </div>
      )}

      {/* ── AI Insights ── */}
      <div className={`${RULE} py-8`}>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-base font-serif font-semibold text-[#1A1816]">AI-Synthesised Insights</h2>
            <p className="text-sm text-[#66605A] mt-0.5">Strategic intelligence tailored for {audience}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <Button type="button" variant="outline" size="sm" className="text-xs h-7 border-[#D9D0C7] text-[#66605A] hover:text-[#1A1816]" onClick={() => void copyInsightsText()}>
              <Copy className="w-3 h-3 mr-1" />Copy
            </Button>
            <Button type="button" variant="outline" size="sm" className="text-xs h-7 border-[#D9D0C7] text-[#66605A] hover:text-[#1A1816]"
              onClick={() => void downloadScoresCsv(industry).catch((e: unknown) => alert(e instanceof Error ? e.message : "Export failed"))}>
              <Download className="w-3 h-3 mr-1" />Scores CSV
            </Button>
          </div>
        </div>

        {/* Executive Brief */}
        {data.executiveBrief && (
          <div className="mb-6 bg-[#F2EDE8] border border-[#D9D0C7] rounded-sm p-5">
            <p className="text-xs font-semibold text-[#66605A] uppercase tracking-wide mb-2">Executive Brief</p>
            <p className="text-sm text-[#1A1816] leading-relaxed">{data.executiveBrief}</p>
          </div>
        )}

        {/* Toggle insight cards */}
        <button
          type="button"
          onClick={() => setShowInsightCards(v => !v)}
          className="flex items-center gap-1.5 text-xs text-[#66605A] hover:text-[#1A1816] mb-5 transition-colors"
        >
          {showInsightCards
            ? <><ChevronUp className="w-3.5 h-3.5" />Hide detail cards</>
            : <><ChevronDown className="w-3.5 h-3.5" />Show {allInsights.length} detail insight cards</>
          }
        </button>

        {showInsightCards && <InsightsPanel insights={allInsights} />}
        <Source>Source: MarketLens AI · Groq LLaMA 3 · based on aggregated review data</Source>
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
    <div className="px-6 py-5">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-3.5 h-3.5 text-[#990F3D] shrink-0" />
        <p className="text-[11px] text-[#66605A] uppercase tracking-wide">{label}</p>
      </div>
      <p className="font-serif text-3xl font-semibold text-[#1A1816]">{value}</p>
      <p className="text-xs text-[#66605A] mt-0.5">{sublabel}</p>
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + "M";
  if (num >= 1_000) return (num / 1_000).toFixed(0) + "K";
  return num.toString();
}
