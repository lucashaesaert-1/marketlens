import { Outlet, useNavigate, useParams } from "react-router";
import { useState, useEffect } from "react";
import {
  Brain,
  TrendingUp,
  Users,
  Building2,
  Loader2,
  Play,
  LogOut,
  RotateCcw,
  ChevronDown,
  Key,
} from "lucide-react";
import { runAnalysis, fetchIndustries, resetOnboarding } from "../api";
import { clearToken } from "../auth";
import { Button } from "./ui/button";
import {
  audienceDescriptions,
  type Audience,
} from "../data/mockData";
import { AudiencePanel } from "./AudiencePanel";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";
export function Layout() {
  const navigate = useNavigate();
  const params = useParams();
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState<string | null>(null);
  const [trustpilotKey, setTrustpilotKey] = useState("");
  const [industries, setIndustries] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    fetchIndustries()
      .then(setIndustries)
      .catch(() => setIndustries([]));
  }, []);

  const currentIndustry = (params.industry as string) || "crm";
  const currentAudience = (params.audience as Audience) || "investors";

  const handleRunAnalysis = async () => {
    setAnalysisRunning(true);
    setAnalysisMessage(null);
    try {
        await runAnalysis(
          currentIndustry,
          undefined,
          "groq",
          trustpilotKey ? { trustpilot: trustpilotKey } : undefined
        );
      setAnalysisMessage("Analysis complete! Refreshing...");
      window.dispatchEvent(new CustomEvent("crm-data-updated"));
      setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
      setAnalysisMessage(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalysisRunning(false);
    }
  };

  const handleIndustryChange = (industry: string) => {
    navigate(`/${industry}/${currentAudience}`);
  };

  const handleAudienceChange = (audience: string) => {
    navigate(`/${currentIndustry}/${audience}`);
  };

  const audienceIcons = {
    investors: TrendingUp,
    companies: Building2,
    customers: Users,
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-indigo-600 rounded-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-slate-900">MarketLens AI</h1>
                <p className="text-xs text-slate-500">
                  AI-Powered Market Research Assistant
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Industry Selector */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">Industry</label>
                <Select value={currentIndustry} onValueChange={handleIndustryChange}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {industries.length > 0
                      ? industries.map(({ id, name }) => (
                          <SelectItem key={id} value={id}>
                            {name}
                          </SelectItem>
                        ))
                      : [
                          { id: "crm", name: "CRM Software" },
                          { id: "food-delivery", name: "Food Delivery" },
                          { id: "ride-sharing", name: "Ride-Sharing" },
                          { id: "saas", name: "SaaS Collaboration" },
                        ].map(({ id, name }) => (
                          <SelectItem key={id} value={id}>
                            {name}
                          </SelectItem>
                        ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Run Analysis */}
              <div className="flex flex-col gap-1">
                  <label className="text-xs text-slate-500">Live Analysis</label>
                  <button
                    onClick={handleRunAnalysis}
                    disabled={analysisRunning}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {analysisRunning ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    {analysisRunning ? "Running…" : "Run Analysis"}
                  </button>
                  {analysisMessage && (
                    <p className={`text-xs ${analysisMessage.startsWith("Analysis complete") ? "text-emerald-600" : "text-rose-600"}`}>
                      {analysisMessage}
                    </p>
                  )}
                  <Collapsible>
                    <CollapsibleTrigger className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 mt-1">
                      <Key className="w-3 h-3" />
                      <ChevronDown className="w-3 h-3" />
                      Data source keys
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <input
                        type="password"
                        placeholder="Trustpilot API key (optional)"
                        value={trustpilotKey}
                        onChange={(e) => setTrustpilotKey(e.target.value)}
                        className="mt-2 w-full px-2 py-1 text-xs border border-slate-200 rounded"
                      />
                    </CollapsibleContent>
                  </Collapsible>
                </div>

              {/* Audience Selector */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">Audience View</label>
                <Select value={currentAudience} onValueChange={handleAudienceChange}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(audienceDescriptions).map(([key, description]) => {
                      const Icon = audienceIcons[key as Audience];
                      return (
                        <SelectItem key={key} value={key}>
                          <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4" />
                            <span className="capitalize">{key}</span>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">Account</label>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="text-xs h-9"
                    title="Show setup wizard again (audience, industry, chat)"
                    onClick={() => {
                      void resetOnboarding()
                        .then(() => {
                          window.location.assign("/onboarding");
                        })
                        .catch((e: unknown) => {
                          alert(e instanceof Error ? e.message : "Could not reset onboarding");
                        });
                    }}
                  >
                    <RotateCcw className="w-3.5 h-3.5 mr-1" />
                    Setup again
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="text-xs h-9"
                    onClick={() => {
                      clearToken();
                      window.location.assign("/login");
                    }}
                  >
                    <LogOut className="w-3.5 h-3.5 mr-1" />
                    Log out
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Audience: use cases & resources */}
          <AudiencePanel audience={currentAudience} />
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
