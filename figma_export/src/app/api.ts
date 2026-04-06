import type { IndustryData } from "./data/mockData";
import { authHeaders } from "./auth";

const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : "/api";

export async function fetchIndustries(): Promise<{ id: string; name: string }[]> {
  const res = await fetch(`${API_BASE}/industries`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch industries");
  const data = await res.json();
  return data.industries;
}

export async function fetchIndustryData(industry: string): Promise<IndustryData> {
  const res = await fetch(`${API_BASE}/industry/${industry}`, { headers: authHeaders() });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/** @deprecated Use fetchIndustryData */
export async function fetchCrmData(): Promise<IndustryData> {
  return fetchIndustryData("crm");
}

export async function runAnalysis(
  industry: string = "crm",
  apiKey?: string,
  provider: "groq" | "openai" = "groq",
  resourceKeys?: Record<string, string>
): Promise<{ status: string; message?: string }> {
  const res = await fetch(`${API_BASE}/run-analysis`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      industry,
      api_key: apiKey || null,
      provider,
      resource_keys: resourceKeys || null,
      use_live_sources: true,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Analysis failed: ${res.status}`);
  }
  return res.json();
}

export type AnalysisStreamEvent = {
  stage: string;
  message?: string;
  elapsed_ms?: number;
  result?: { status: string; message?: string };
};

/** SSE progress: fetch → scoring → insights → complete. */
export async function runAnalysisStream(
  industry: string,
  opts: {
    provider?: "groq" | "openai";
    apiKey?: string;
    resourceKeys?: Record<string, string>;
    onEvent?: (e: AnalysisStreamEvent) => void;
  } = {}
): Promise<{ status: string; message?: string }> {
  const res = await fetch(`${API_BASE}/run-analysis/stream`, {
    method: "POST",
    headers: { ...authHeaders(), Accept: "text/event-stream" },
    body: JSON.stringify({
      industry,
      provider: opts.provider ?? "groq",
      api_key: opts.apiKey ?? null,
      resource_keys: opts.resourceKeys ?? null,
      use_live_sources: true,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Analysis failed: ${res.status}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const dec = new TextDecoder();
  let buf = "";
  let finalResult: { status: string; message?: string } | null = null;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const e = JSON.parse(line.slice(6)) as AnalysisStreamEvent;
        opts.onEvent?.(e);
        if (e.stage === "complete" && e.result) finalResult = e.result;
      } catch {
        /* ignore parse errors */
      }
    }
  }
  if (!finalResult) throw new Error("Stream ended without result");
  if (finalResult.status === "error") throw new Error(finalResult.message || "Analysis failed");
  return finalResult;
}

export type SavedViewRow = {
  id: number;
  name: string;
  industry: string;
  audience: string;
  created_at: string;
};

export async function fetchSavedViews(): Promise<SavedViewRow[]> {
  const res = await fetch(`${API_BASE}/saved-views`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Could not load saved views");
  const j = (await res.json()) as { views: SavedViewRow[] };
  return j.views || [];
}

export async function createSavedView(
  name: string,
  industry: string,
  audience: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/saved-views`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ name, industry, audience }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Could not save view");
  }
}

export async function deleteSavedView(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/saved-views/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Could not delete view");
}

export async function downloadScoresCsv(industry: string): Promise<void> {
  const res = await fetch(`${API_BASE}/industry/${industry}/export/scores.csv`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Export failed");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${industry}_scores.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function loginRequest(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Login failed");
  }
  return res.json() as Promise<{ access_token: string }>;
}

export async function registerRequest(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Register failed");
  }
  return res.json() as Promise<{ access_token: string }>;
}

export async function fetchLoginPanelMarkdown(): Promise<string> {
  const res = await fetch(`${API_BASE}/content/login-panel`);
  if (!res.ok) return "";
  const j = await res.json();
  return (j as { markdown?: string }).markdown || "";
}

/** Server-side: mark onboarding incomplete so /onboarding is shown again. */
export async function resetOnboarding(): Promise<void> {
  const res = await fetch(`${API_BASE}/profile/reset-onboarding`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Could not reset onboarding");
  }
}
