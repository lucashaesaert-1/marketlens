import { Outlet, useNavigate, useParams } from "react-router";
import { useState, useEffect } from "react";
import {
  Brain,
  Loader2,
  Play,
  LogOut,
  RotateCcw,
  Key,
  Bookmark,
} from "lucide-react";
import {
  runAnalysisStream,
  fetchIndustries,
  resetOnboarding,
  fetchSavedViews,
  createSavedView,
  deleteSavedView,
  type SavedViewRow,
} from "../api";
import { clearToken } from "../auth";
import { Button } from "./ui/button";
import { type Audience } from "../data/mockData";
import { AudiencePanel } from "./AudiencePanel";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

export function Layout() {
  const navigate = useNavigate();
  const params = useParams();
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState<string | null>(null);
  const [analysisStage, setAnalysisStage] = useState<string | null>(null);
  const [trustpilotKey, setTrustpilotKey] = useState("");
  const [industries, setIndustries] = useState<{ id: string; name: string }[]>([]);
  const [llmProvider, setLlmProvider] = useState<"groq" | "openai">("groq");
  const [savedViews, setSavedViews] = useState<SavedViewRow[]>([]);

  const loadBookmarks = () => {
    void fetchSavedViews()
      .then(setSavedViews)
      .catch(() => setSavedViews([]));
  };

  useEffect(() => {
    fetchIndustries()
      .then(setIndustries)
      .catch(() => setIndustries([]));
  }, []);

  useEffect(() => {
    loadBookmarks();
  }, []);

  const currentIndustry = (params.industry as string) || "crm";
  const currentAudience = (params.audience as Audience) || "investors";

  const handleRunAnalysis = async () => {
    setAnalysisRunning(true);
    setAnalysisMessage(null);
    setAnalysisStage(null);
    // Pick up onboarding context saved during setup (persists for the browser tab session)
    const userContext = sessionStorage.getItem("onboarding_user_context") ?? undefined;
    try {
      await runAnalysisStream(currentIndustry, {
        provider: llmProvider,
        resourceKeys: trustpilotKey ? { trustpilot: trustpilotKey } : undefined,
        audience: currentAudience,
        userContext,
        onEvent: (e) => {
          if (e.message) setAnalysisStage(e.message);
        },
      });
      setAnalysisMessage("Analysis complete! Refreshing...");
      window.dispatchEvent(new CustomEvent("crm-data-updated"));
      setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
      setAnalysisMessage(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalysisRunning(false);
      setAnalysisStage(null);
    }
  };

  const handleIndustryChange = (industry: string) => {
    navigate(`/${industry}/${currentAudience}`);
  };

  return (
    <div className="min-h-screen bg-[#FFF9F5]">
      {/* FT-style thin crimson top bar */}
      <div className="h-[3px] bg-[#990F3D]" />
      {/* Header */}
      <header className="bg-white border-b border-[#D9D0C7] sticky top-0 z-50">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 bg-[#990F3D]">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-serif font-semibold text-[#1A1816] tracking-tight">MarketLens AI</h1>
                <p className="text-xs text-[#66605A]">
                  AI-Powered Market Intelligence
                </p>
              </div>
            </div>

            <div className="flex items-end gap-3">
              {/* Industry Selector */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">Industry</label>
                <Select value={currentIndustry} onValueChange={handleIndustryChange}>
                <SelectTrigger className="w-[180px] h-9 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {industries.length > 0
                    ? industries.map(({ id, name }) => (
                        <SelectItem key={id} value={id}>{name}</SelectItem>
                      ))
                    : [
                        { id: "crm", name: "CRM Software" },
                        { id: "food-delivery", name: "Food Delivery" },
                        { id: "ride-sharing", name: "Ride-Sharing" },
                        { id: "saas", name: "SaaS Collaboration" },
                      ].map(({ id, name }) => (
                        <SelectItem key={id} value={id}>{name}</SelectItem>
                      ))}
                </SelectContent>
              </Select>
              </div>

              <div className="w-px h-6 bg-slate-200" />

              {/* LLM Provider */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">LLM provider</label>
                <Select value={llmProvider} onValueChange={(v) => setLlmProvider(v as "groq" | "openai")}>
                  <SelectTrigger className="w-[110px] h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="groq">Groq</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                  </SelectContent>
                </Select>
              </div>


              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="h-9 text-xs">
                    <Key className="w-3.5 h-3.5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 p-3">
                  <p className="text-xs text-slate-500 mb-2">Data source keys</p>
                  <input
                    type="password"
                    placeholder="Trustpilot API key (optional)"
                    value={trustpilotKey}
                    onChange={(e) => setTrustpilotKey(e.target.value)}
                    className="w-full px-2 py-1 text-xs border border-slate-200 rounded"
                  />
                </DropdownMenuContent>
              </DropdownMenu>

              <button
                onClick={() => void handleRunAnalysis()}
                disabled={analysisRunning}
                className="flex items-center gap-2 px-4 h-9 bg-[#990F3D] text-white text-sm font-medium hover:bg-[#7B0B31] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {analysisRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {analysisRunning ? (analysisStage ?? "Running…") : "Run Analysis"}
              </button>
              {analysisMessage && (
                <p className={`text-xs ${analysisMessage.startsWith("Analysis complete") ? "text-emerald-600" : "text-rose-600"}`}>
                  {analysisMessage}
                </p>
              )}

              <div className="w-px h-6 bg-slate-200" />

              {/* Saved Views */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="h-9 text-sm">
                    <Bookmark className="w-3.5 h-3.5 mr-1.5" />
                    Saved views
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem
                    onClick={() => {
                      const name = window.prompt("Name for this view (industry + audience)");
                      if (!name?.trim()) return;
                      void createSavedView(name.trim(), currentIndustry, currentAudience)
                        .then(loadBookmarks)
                        .catch((e: unknown) => alert(e instanceof Error ? e.message : "Save failed"));
                    }}
                  >
                    Save current view…
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  {savedViews.length === 0 ? (
                    <DropdownMenuItem disabled>No saved views yet</DropdownMenuItem>
                  ) : (
                    savedViews.flatMap((v) => [
                      <DropdownMenuItem key={`open-${v.id}`} onClick={() => navigate(`/${v.industry}/${v.audience}`)}>
                        Open: {v.name}
                      </DropdownMenuItem>,
                      <DropdownMenuItem
                        key={`del-${v.id}`}
                        className="text-rose-600 focus:text-rose-700"
                        onClick={() =>
                          void deleteSavedView(v.id)
                            .then(loadBookmarks)
                            .catch((e: unknown) => alert(e instanceof Error ? e.message : "Delete failed"))
                        }
                      >
                        Delete "{v.name}"
                      </DropdownMenuItem>,
                    ])
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Account */}
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-9 text-sm"
                title="Show setup wizard again"
                onClick={() => {
                  void resetOnboarding()
                    .then(() => window.location.assign("/onboarding"))
                    .catch((e: unknown) => alert(e instanceof Error ? e.message : "Could not reset onboarding"));
                }}
              >
                <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
                Setup
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-9 text-sm"
                onClick={() => { clearToken(); window.location.assign("/login"); }}
              >
                <LogOut className="w-3.5 h-3.5 mr-1.5" />
                Log out
              </Button>
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
