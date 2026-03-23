import type { IndustryData } from "./data/mockData";
import { authHeaders } from "./auth";

const API_BASE = "/api";

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
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/run-analysis`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      industry,
      api_key: apiKey || null,
      provider,
      resource_keys: resourceKeys || null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Analysis failed: ${res.status}`);
  }
  return res.json();
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
