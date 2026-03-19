/**
 * Audience → Use Cases → Resources data model
 * Maps each audience to the questions they care about and the data sources that feed insights.
 */

import type { Audience } from "./mockData";

export interface UseCase {
  id: string;
  question: string;
  description?: string;
}

export interface Resource {
  id: string;
  name: string;
  type: "api" | "scrape" | "manual" | "partner";
  status: "planned" | "integrated" | "mock";
  notes?: string;
}

export interface AudienceConfig {
  audience: Audience;
  description: string;
  useCases: UseCase[];
  resources: Resource[];
}

export const audienceConfig: Record<Audience, AudienceConfig> = {
  investors: {
    audience: "investors",
    description: "Focus on defensible moats, competitive margins, and market dynamics",
    useCases: [
      { id: "moat", question: "Defensible moat?" },
      { id: "margins", question: "Comparable companies' margins?" },
      { id: "growth", question: "Who is growing fastest?" },
      { id: "whitespace", question: "What whitespace exists?" },
      { id: "unit-economics", question: "Unit economics vs peers?" },
      { id: "churn-risk", question: "Churn risk?" },
      { id: "pricing-power", question: "Pricing power vs category?" },
      { id: "market-share", question: "Market share trajectory?" },
    ],
    resources: [
      { id: "factset", name: "FactSet", type: "api", status: "planned", notes: "Financial data, comparables" },
    ],
  },
  companies: {
    audience: "companies",
    description: "Identify customer pain points, competitive gaps, and strategic opportunities",
    useCases: [
      { id: "complaints", question: "Main customer complaints?" },
      { id: "competitors", question: "Competitor moves we're missing?" },
      { id: "pricing", question: "Pricing power?" },
      { id: "social", question: "Social presence vs competitors?" },
      { id: "churn-reasons", question: "Top churn reasons?" },
      { id: "feature-gaps", question: "Feature gaps vs leaders?" },
      { id: "support-quality", question: "Support quality vs peers?" },
      { id: "integrations", question: "Integration ecosystem strength?" },
      { id: "review-volume", question: "Review volume trend?" },
    ],
    resources: [
      { id: "g2", name: "G2 / Capterra", type: "api", status: "integrated", notes: "Product reviews" },
      { id: "apify", name: "Apify (G2, Capterra)", type: "api", status: "integrated", notes: "Set APIFY_API_TOKEN" },
    ],
  },
  customers: {
    audience: "customers",
    description: "Compare platforms, employer brand, and ethical/sustainability signals",
    useCases: [
      { id: "supply-chain", question: "Supply chain ethics?" },
      { id: "carbon", question: "CO2 footprint?" },
      { id: "employees", question: "Employee treatment and compensation?" },
      { id: "best-value", question: "Best value for money?" },
      { id: "easiest-use", question: "Easiest to use?" },
      { id: "best-support", question: "Best support?" },
      { id: "best-segment", question: "Best for my segment (SMB/enterprise)?" },
    ],
    resources: [
      { id: "glassdoor", name: "Glassdoor API", type: "api", status: "planned", notes: "Employee reviews, compensation" },
      { id: "kaggle_apify", name: "Kaggle / Apify", type: "api", status: "integrated", notes: "Reviews from Kaggle + Apify (G2, Capterra, Trustpilot)" },
    ],
  },
};
