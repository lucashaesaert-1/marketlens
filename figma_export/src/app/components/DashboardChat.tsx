import { useEffect, useState } from "react";
import { MessageCircle, X } from "lucide-react";
import { authHeaders } from "../auth";
import type { Audience } from "../data/mockData";
import { ChatPanel } from "./ChatPanel";
import { Button } from "./ui/button";

export function DashboardChat(props: { industry: string; audience: Audience }) {
  const { industry, audience } = props;
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);

  useEffect(() => {
    if (!open || sessionId !== null) return;
    (async () => {
      const res = await fetch("/api/chat/session", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ purpose: "dashboard", industry }),
      });
      if (res.ok) {
        const j = await res.json();
        setSessionId(j.session_id);
      }
    })();
  }, [open, industry, sessionId]);

  const guided =
    audience === "investors"
      ? ["Who is growing fastest?", "What whitespace exists?"]
      : audience === "companies"
        ? ["Main customer complaints?", "Feature gaps vs leaders?"]
        : ["Best value?", "Easiest to use?"];

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-[#990F3D] text-white shadow-lg hover:bg-[#7B0B31]"
        aria-label="Open assistant"
      >
        <MessageCircle className="w-5 h-5" />
        Ask MarketLens
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-[min(100vw-2rem,420px)] shadow-2xl overflow-hidden bg-white border border-[#D9D0C7]">
          <div className="flex items-center justify-between px-3 py-2 bg-[#F2EDE8] border-b border-[#D9D0C7]">
            <span className="text-sm font-medium text-[#1A1816]">Dashboard assistant</span>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setOpen(false)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          {sessionId !== null ? (
            <ChatPanel
              sessionId={sessionId}
              industry={industry}
              audience={audience}
              guidedQuestions={guided}
              title=""
              disclaimer="Not financial advice. Research only."
            />
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">Starting chat…</div>
          )}
        </div>
      )}
    </>
  );
}
