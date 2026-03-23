import { useEffect, useRef, useState } from "react";
import { Send, Loader2 } from "lucide-react";
import { authHeaders } from "../auth";
import { cn } from "./ui/utils";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";

type Msg = { role: "user" | "assistant"; content: string };

const MAX_LEN = 1000;

async function streamChat(
  sessionId: number,
  content: string,
  industry: string | null,
  audience: string | null,
  onToken: (t: string) => void
): Promise<void> {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ session_id: sessionId, industry, audience, content }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Chat failed: ${res.status}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() || "";
    for (const block of parts) {
      const line = block.trim();
      if (!line.startsWith("data: ")) continue;
      const json = line.slice(6);
      try {
        const ev = JSON.parse(json) as { token?: string; error?: string };
        if (ev.error) throw new Error(ev.error);
        if (ev.token) onToken(ev.token);
      } catch (e) {
        if (e instanceof SyntaxError) continue;
        throw e;
      }
    }
  }
}

export function ChatPanel(props: {
  sessionId: number;
  industry: string | null;
  audience: string | null;
  guidedQuestions: string[];
  title?: string;
  disclaimer?: string;
  className?: string;
}) {
  const { sessionId, industry, audience, guidedQuestions, title = "Ask MarketLens", disclaimer, className } = props;
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    const t = text.slice(0, MAX_LEN).trim();
    if (!t || streaming) return;
    setMessages((m) => [...m, { role: "user", content: t }]);
    setInput("");
    setStreaming(true);
    let acc = "";
    setMessages((m) => [...m, { role: "assistant", content: "" }]);
    try {
      await streamChat(sessionId, t, industry, audience, (tok) => {
        acc += tok;
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { role: "assistant", content: acc };
          return copy;
        });
      });
    } catch (e) {
      setMessages((m) => {
        const copy = [...m];
        if (copy[copy.length - 1]?.role === "assistant" && !copy[copy.length - 1].content) copy.pop();
        return [
          ...copy,
          { role: "assistant", content: `Error: ${e instanceof Error ? e.message : String(e)}` },
        ];
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col min-h-[420px] lg:min-h-0 lg:h-full border border-slate-200 rounded-xl bg-white shadow-sm overflow-hidden",
        className
      )}
    >
      {(title || disclaimer) && (
        <div className="px-4 py-3 border-b border-slate-100 shrink-0">
          {title ? <h3 className="font-semibold text-slate-900 text-sm">{title}</h3> : null}
          {disclaimer && <p className="text-xs text-slate-500 mt-1 leading-snug">{disclaimer}</p>}
        </div>
      )}
      <ScrollArea className="flex-1 min-h-[200px] max-h-[min(42vh,380px)] lg:max-h-none lg:flex-1">
        <div className="flex flex-col gap-3 px-4 py-3 text-left">
          {messages.length === 0 && (
            <p className="text-sm text-slate-500 leading-relaxed">
              Ask about this market, or tap a suggested question below. Max {MAX_LEN} characters per message.
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={cn(
                "text-sm rounded-lg px-3 py-2.5",
                m.role === "user"
                  ? "self-end max-w-[88%] bg-indigo-50 text-slate-800 border border-indigo-100/80"
                  : "self-stretch w-full bg-slate-50 text-slate-800 border border-slate-100 text-left"
              )}
            >
              <span className="text-[10px] uppercase tracking-wide font-medium text-slate-400 block mb-1.5">
                {m.role === "user" ? "You" : "Assistant"}
              </span>
              <div className="whitespace-pre-wrap text-left leading-relaxed">{m.content}</div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
      <div className="px-3 py-2 border-t border-slate-100 flex flex-wrap gap-1.5 shrink-0 bg-slate-50/50">
        {guidedQuestions.slice(0, 8).map((q) => (
          <button
            key={q}
            type="button"
            disabled={streaming}
            className="text-xs px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 disabled:opacity-50 text-left"
            onClick={() => void send(q)}
          >
            {q}
          </button>
        ))}
      </div>
      <div className="p-3 flex gap-2 border-t border-slate-100 shrink-0">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, MAX_LEN))}
          placeholder="Type a question"
          className="min-h-[68px] resize-none text-sm border-slate-200"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send(input);
            }
          }}
        />
        <Button type="button" className="self-end shrink-0 h-10 w-10 p-0" disabled={streaming || !input.trim()} onClick={() => void send(input)}>
          {streaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </Button>
      </div>
      <p className="px-4 pb-2 text-xs text-slate-400 tabular-nums">{input.length}/{MAX_LEN}</p>
    </div>
  );
}
