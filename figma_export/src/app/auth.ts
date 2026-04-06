import { API_BASE } from "./api";

const TOKEN_KEY = "insightengine_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function authHeaders(): HeadersInit {
  const t = getToken();
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

export type UserProfile = {
  audience: string | null;
  industry: string | null;
  onboarding_completed: boolean;
  personalization: Record<string, unknown> | null;
};

const API_TIMEOUT_MS = 12_000;

async function fetchWithTimeout(
  input: RequestInfo,
  init: RequestInit & { timeoutMs?: number } = {}
): Promise<Response> {
  const { timeoutMs = API_TIMEOUT_MS, ...rest } = init;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(input, { ...rest, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

export async function fetchProfile(): Promise<UserProfile> {
  const res = await fetchWithTimeout(`${API_BASE}/profile`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load profile");
  const raw = (await res.json()) as Record<string, unknown>;
  return {
    audience: typeof raw.audience === "string" ? raw.audience : null,
    industry: typeof raw.industry === "string" ? raw.industry : null,
    // Strict boolean — avoids skipping onboarding if the value is wrong type
    onboarding_completed: raw.onboarding_completed === true,
    personalization:
      raw.personalization && typeof raw.personalization === "object"
        ? (raw.personalization as Record<string, unknown>)
        : null,
  };
}
