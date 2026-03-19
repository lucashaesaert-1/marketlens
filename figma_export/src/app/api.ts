import type { IndustryData } from "./data/mockData";

const API_BASE = "/api";

export async function fetchIndustries(): Promise<{ id: string; name: string }[]> {
  const res = await fetch(`${API_BASE}/industries`);
  if (!res.ok) throw new Error("Failed to fetch industries");
  const data = await res.json();
  return data.industries;
}

export async function fetchIndustryData(industry: string): Promise<IndustryData> {
  const res = await fetch(`${API_BASE}/industry/${industry}`);
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
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/run-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      industry,
      api_key: apiKey || null,
      provider,
      resource_keys: resourceKeys || null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || `Analysis failed: ${res.status}`);
  }
  return res.json();
}
