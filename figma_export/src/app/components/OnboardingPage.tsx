import { useEffect, useState } from "react";
import { Building2, Loader2, TrendingUp, Users } from "lucide-react";
import { authHeaders } from "../auth";
import { fetchIndustries } from "../api";
import type { Audience } from "../data/mockData";
import { audienceDescriptions } from "../data/mockData";
import { ChatPanel } from "./ChatPanel";
import { Button } from "./ui/button";
import { Label } from "./ui/label";
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

const icons = { investors: TrendingUp, companies: Building2, customers: Users };

function parseApiError(res: Response, fallback: string): Promise<string> {
  return res.json().then(
    (er: { detail?: unknown }) => {
      const d = er.detail;
      if (Array.isArray(d)) {
        return d.map((x: { msg?: string }) => x.msg || "").filter(Boolean).join(" ") || fallback;
      }
      if (typeof d === "string") return d;
      return fallback;
    },
    () => fallback
  );
}

export function OnboardingPage() {
  const [industries, setIndustries] = useState<{ id: string; name: string }[]>([]);
  const [audience, setAudience] = useState<Audience>("investors");
  const [industry, setIndustry] = useState("crm");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetchIndustries()
      .then((list) =>
        setIndustries(
          list.length
            ? list
            : [
                { id: "crm", name: "CRM Software" },
                { id: "food-delivery", name: "Food Delivery" },
                { id: "saas", name: "SaaS Collaboration" },
              ]
        )
      )
      .catch(() =>
        setIndustries([
          { id: "crm", name: "CRM Software" },
          { id: "food-delivery", name: "Food Delivery" },
        ])
      );
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/chat/session", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ purpose: "onboarding", industry: null }),
        });
        if (!res.ok) {
          const msg = await parseApiError(res, "Could not start chat session");
          throw new Error(msg);
        }
        const j = await res.json();
        setSessionId(j.session_id);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Session error");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const guided =
    audience === "investors"
      ? ["Who is growing fastest?", "What whitespace exists?", "Pricing power vs category?", "Churn risk?"]
      : audience === "companies"
        ? ["Main customer complaints?", "Competitor moves we're missing?", "Support quality vs peers?"]
        : ["Best value for money?", "Easiest to use?", "Best support?"];

  const complete = async () => {
    if (!sessionId) return;
    setSubmitting(true);
    setErr(null);
    try {
      const res = await fetch("/api/onboarding/complete", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          audience,
          industry,
          session_id: sessionId,
        }),
      });
      if (!res.ok) {
        const msg = await parseApiError(res, "Onboarding failed");
        throw new Error(msg);
      }
      // Full load so ProtectedLayout reads fresh profile (server has onboarding_completed=true)
      window.location.assign(`/${industry}/${audience}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (sessionId === null) {
    return (
      <div className="min-h-[calc(100dvh-0px)] bg-slate-100/90 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-xl border border-slate-200 shadow-sm p-6 text-center">
          <h1 className="text-lg font-semibold text-slate-900">Couldn&apos;t start setup</h1>
          <p className="text-sm text-slate-600 mt-2">
            {err || "Chat session could not be created. Is the API running (port 8001) and are you signed in?"}
          </p>
          <Button
            type="button"
            className="mt-5 w-full bg-indigo-600 hover:bg-indigo-700"
            onClick={() => {
              setErr(null);
              setLoading(true);
              void fetch("/api/chat/session", {
                method: "POST",
                headers: authHeaders(),
                body: JSON.stringify({ purpose: "onboarding", industry: null }),
              })
                .then(async (res) => {
                  if (!res.ok) {
                    const msg = await parseApiError(res, "Could not start chat session");
                    throw new Error(msg);
                  }
                  return res.json();
                })
                .then((j: { session_id?: number }) => {
                  if (j.session_id != null) setSessionId(j.session_id);
                  else setErr("Invalid response from server");
                })
                .catch((e: unknown) => setErr(e instanceof Error ? e.message : "Session error"))
                .finally(() => setLoading(false));
            }}
          >
            Try again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100dvh-0px)] bg-slate-100/90">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 lg:py-8">
        <header className="mb-5 lg:mb-6">
          <h1 className="text-xl sm:text-2xl font-semibold text-slate-900 tracking-tight">Set up your analysis</h1>
          <p className="text-slate-600 text-sm mt-1 max-w-2xl leading-snug">
            Pick your role and industry, chat with the assistant, then continue to the dashboard.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5 lg:items-stretch lg:min-h-[min(720px,calc(100dvh-10rem))]">
          {/* Left: controls — denser, tabbed audience */}
          <div className="flex flex-col gap-4 min-w-0 order-2 lg:order-1">
            <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Audience</Label>
              <Tabs
                value={audience}
                onValueChange={(v) => setAudience(v as Audience)}
                className="mt-3 w-full gap-3"
              >
                <TabsList className="grid w-full grid-cols-3 h-auto p-1 bg-slate-100 rounded-lg gap-0.5">
                  {(Object.keys(audienceDescriptions) as Audience[]).map((a) => {
                    const Icon = icons[a];
                    return (
                      <TabsTrigger
                        key={a}
                        value={a}
                        className="flex flex-col items-center gap-1 py-2.5 px-1 sm:px-2 text-[11px] sm:text-xs data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-indigo-700 rounded-md"
                      >
                        <Icon className="w-4 h-4 shrink-0" />
                        <span className="capitalize leading-tight text-center">{a}</span>
                      </TabsTrigger>
                    );
                  })}
                </TabsList>
              </Tabs>
              <p className="text-xs text-slate-600 mt-3 leading-relaxed border-t border-slate-100 pt-3">
                {audienceDescriptions[audience]}
              </p>
            </section>

            <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 flex-1 flex flex-col">
              <Label htmlFor="industry-select" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Industry
              </Label>
              <Select value={industry} onValueChange={setIndustry}>
                <SelectTrigger id="industry-select" className="w-full mt-2 h-11 bg-white border-slate-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {industries.map(({ id, name }) => (
                    <SelectItem key={id} value={id}>
                      {name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500 mt-2">Data and charts will match this sector.</p>

              {err && (
                <div className="mt-4 p-3 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">{err}</div>
              )}

              <div className="mt-auto pt-5">
                <Button
                  type="button"
                  size="lg"
                  className="w-full h-12 text-base font-medium bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
                  disabled={submitting}
                  onClick={() => void complete()}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2 inline" /> Saving…
                    </>
                  ) : (
                    "Continue to dashboard"
                  )}
                </Button>
                <p className="text-[11px] text-slate-400 text-center mt-2">
                  Saves your preferences and opens the dashboard for this industry.
                </p>
              </div>
            </section>
          </div>

          {/* Right: chat — same visual width as cards, aligned */}
          <div className="order-1 lg:order-2 flex flex-col min-h-[480px] lg:min-h-0 lg:h-full">
            <ChatPanel
              sessionId={sessionId}
              industry={industry}
              audience={audience}
              guidedQuestions={guided}
              title="Onboarding assistant"
              disclaimer="Not financial advice. For research only. Max 1000 characters per message."
              className="flex-1 lg:min-h-[560px]"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
