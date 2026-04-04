# InsightEngine — CLAUDE.md

> **For Claude instances working on this project:** This document is the definitive map of how InsightEngine works. Read it fully before touching any file. It documents every architectural decision, pattern, and known issue to prevent repeated mistakes.

---

## What This Project Is

InsightEngine is a **market intelligence prototype** built for a group project. It generates audience-specific competitive analysis dashboards for 12 industries. A user logs in, picks their audience (Investor / Company / Customer) and industry (CRM, Food Delivery, etc.), optionally chats with an AI assistant to personalise the view, then sees charts and AI-generated insights about that competitive landscape.

The core value proposition: **different audiences see different data**. An investor sees stock prices and news headlines. A company sees customer complaint themes and Glassdoor ratings. A customer sees value-for-money comparisons and support quality.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite 6 + TypeScript + Tailwind v4 + Recharts |
| Backend | Python FastAPI + uvicorn, Python 3.9 (venv) |
| Database | SQLite via SQLAlchemy (`data/insightengine.db`) |
| LLM | Groq (default) or OpenAI — configurable per request |
| Review data | Apify (G2/Capterra), Kaggle datasets, SerpAPI Google Maps |
| Market data | Alpha Vantage (stock quotes), SerpAPI (News, Trends, Glassdoor scrape) |
| Auth | JWT (python-jose), bcrypt passwords, rate limiting |

---

## Running Locally

**Prerequisites:** Python 3.9+, Node.js 18+. The `venv/` directory is committed — activate it.

```bash
# Terminal 1 — Backend (port 8001)
source venv/bin/activate
python -m uvicorn api.main:app --reload --port 8001

# Terminal 2 — Frontend (port 5173)
cd figma_export
npm run dev
```

- App: http://localhost:5173
- API docs (Swagger): http://localhost:8001/docs
- Demo account: `demo@marketlens.ai` / `demo12345`

> **Note:** Vite auto-increments the port (5174, 5175…) if 5173 is in use. Check the terminal output for the actual URL.

---

## Environment Variables (`.env` in project root)

All loaded via `python-dotenv` at startup in `api/main.py`.

| Variable | Purpose | Required? |
|---|---|---|
| `GROQ_API_KEY` | LLM for chat, scoring, and insights | Yes for live analysis |
| `APIFY_API_TOKEN` | Scrape G2/Capterra reviews via Apify | Optional — enables live reviews |
| `SER_API` | SerpAPI key for Google News, Trends, Glassdoor scraping | Optional — enables market enrichments |
| `Alpha_vantage` | Alpha Vantage API key for live stock quotes | Optional — enables finance card |
| `Openweb_ninja` | OpenWebNinja API key (Glassdoor) | **Not yet wired** — see Pending Work |
| `JWT_SECRET` | JWT signing secret | Optional (defaults to dev value) |
| `OPENAI_API_KEY` | OpenAI as alternative to Groq | Optional |

> **Important naming:** The env vars use mixed case exactly as shown above (`Alpha_vantage`, `Openweb_ninja`, `SER_API`). Do not normalise them — the adapters read them by exact name.

Tuning variables (all optional, have defaults):

| Variable | Default | Effect |
|---|---|---|
| `PIPELINE_MAX_REVIEWS` | 64 | Reviews scored per run |
| `PIPELINE_PARALLEL_WORKERS` | 8 | Concurrent Groq calls |
| `GROQ_FAST_MODEL` | `llama-3.1-8b-instant` | Per-review scoring model |
| `GROQ_INSIGHTS_MODEL` | `llama-3.3-70b-versatile` | Insight synthesis model |
| `APIFY_MAX_COMPANIES` | 6 | Companies fetched via Apify |
| `FETCH_REVIEW_LIMIT` | 150 | Max reviews fetched before scoring |

---

## Directory Structure

```
prototypinggroup/
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry point, .env loading, route registration
│   ├── industry_service.py     # Cache, payload builder, enrichments
│   ├── run_analysis_core.py    # SSE pipeline: fetch → score → insights → enrich
│   ├── chat_service.py         # Groq/OpenAI streaming chat
│   ├── personalization.py      # Chat-derived insight merging
│   ├── audience_config.py      # Audience → use-cases mapping (Python side)
│   ├── auth_utils.py           # JWT creation/verification, bcrypt
│   ├── database.py             # SQLAlchemy engine, session factory, Base
│   ├── models.py               # ORM models: User, ChatMessage, SavedView
│   ├── deps.py                 # FastAPI dependency injection (DB session, current user)
│   └── user_routes.py          # Auth + saved-views routes
│
├── resources/                  # Data source adapters (all optional/graceful)
│   ├── adapters.py             # Unified adapter interface (import this, not sub-adapters)
│   ├── serpapi_adapter.py      # SerpAPI: Trends, Maps Reviews, News, Finance, Glassdoor
│   ├── alphavantage_adapter.py # Alpha Vantage: live stock quotes
│   ├── apify_adapter.py        # Apify: G2/Capterra/Trustpilot reviews
│   ├── kaggle_loader.py        # Kaggle datasets (ride-sharing, food-delivery, etc.)
│   └── scrapers/               # Direct HTML scrapers (fallback only)
│
├── figma_export/               # React + Vite frontend
│   └── src/app/
│       ├── App.tsx             # Root component, routing
│       ├── routes.tsx          # React Router routes
│       ├── api.ts              # All fetch calls to the backend
│       ├── auth.ts             # JWT storage, login/logout helpers
│       ├── data/
│       │   ├── mockData.ts     # All TypeScript interfaces for API responses
│       │   └── audienceConfig.ts # Audience → use-cases → resources config (UI side)
│       └── components/
│           ├── Dashboard.tsx   # Main dashboard, audience-gated chart rendering
│           ├── charts/         # Recharts wrappers (Radar, Heatmap, etc.)
│           ├── cards/          # Data-source cards (News, Finance, Glassdoor)
│           └── ui/             # shadcn/ui component library
│
├── industry_config.py          # 12 industries: companies, dimensions, mock scores, data files
├── pipeline.py                 # LLM scoring + insight generation (Groq/OpenAI)
├── data/                       # Sample review JSONs + SQLite DB
├── content/                    # Login panel markdown
├── CLAUDE.md                   # This file
├── architecture_report.html    # Visual architecture report (open in browser)
├── requirements.txt
└── .env                        # Secret keys — never commit
```

---

## Core Architecture

### Request Flow (normal page load)

```
Browser → GET /api/industry/{id}?audience={aud}
       → api/main.py: _industry_payload()
       → api/industry_service.py: get_industry_cache_entry()
            ├─ Cache HIT  → return cached scores/insights/enrichments
            └─ Cache MISS → load mock scores from industry_config.py
                          → _try_fetch_serpapi_enrichments() [eager, async-ish]
                          → return payload
       → build_industry_data() → JSON response
```

### Run Analysis Flow (user clicks "Run Analysis")

```
Browser → POST /api/run-analysis/stream (SSE)
       → run_analysis_core.py: iter_run_analysis_events()
            1. fetch     → adapters.fetch_reviews_for_industry()
                           Order: Kaggle → SerpAPI Maps → Apify → local JSON file
            2. scoring   → pipeline.compute_dimension_scores() [LLM per review]
            3. insights  → pipeline.generate_insights() [single LLM call]
            4. enriching → fetch news (SerpAPI), finance (Alpha Vantage),
                           Glassdoor (SerpAPI), trends (SerpAPI), SoV (SerpAPI)
            5. complete  → set_industry_cache_entry() [updates in-memory cache]
       → SSE stream: {stage, message, elapsed_ms} events
       → Frontend polls stage=complete then re-fetches /api/industry/{id}
```

### Auth Flow

```
POST /api/auth/register  → hash password → create User in SQLite
POST /api/auth/login     → verify password → return JWT (24h expiry)
Protected routes         → deps.get_current_user() → decode JWT → User ORM object
```

---

## Audience-Gated Data (Critical Pattern)

**The most important architectural concept.** Each audience sees a different subset of charts and data cards. This is enforced in two places:

### Backend — `audienceConfig` Python dict
`api/audience_config.py` maps each audience to use-cases. The LLM generates insights tagged with audience names ("Investors", "Companies", "Customers") and `industry_service.py` routes them to the right bucket.

### Frontend — `CHARTS_BY_AUDIENCE` in `Dashboard.tsx`
```typescript
const CHARTS_BY_AUDIENCE: Record<Audience, Set<string>> = {
  investors: new Set(["positioning", "sentiment", "shareOfVoice", "churnFlows",
                      "dimensionBenchmarking", "newsHeadlines", "financeData"]),
  companies: new Set(["radar", "heatmap", "praiseComplaint", "dimensionDeltas",
                      "dimensionBenchmarking", "glassdoorData"]),
  customers: new Set(["positioning", "radar", "praiseComplaint",
                      "dimensionBenchmarking", "glassdoorData"]),
};
```

A card only renders if **both** conditions are met:
1. `CHARTS_BY_AUDIENCE[audience].has(key)` — the audience should see this card
2. The data field is non-null/non-empty in the API response — real data was fetched

If `SER_API` or `Alpha_vantage` are not set, the cards simply don't appear. No fake data is injected.

### `audienceConfig.ts` (Frontend)
Maps audience → use-case questions → data resources. The "Resources" panel on the dashboard reads from here. When a new API is integrated, update the `status` field from `"planned"` to `"integrated"`.

---

## Data Sources — What's Real vs Mock

### Always Real (no API key needed)
- Sample review JSONs in `data/` — structured realistic text, scores computed from these
- Mock scores in `industry_config.py` — fallback when no LLM key

### Real When Keys Are Set

| Data | Key Needed | Where Used | Audience |
|---|---|---|---|
| G2/Capterra reviews | `APIFY_API_TOKEN` | Scoring pipeline | All |
| Google Maps reviews | `SER_API` | Scoring (restaurants/hospitality/travel only) | All |
| Google Trends (sentiment timeline) | `SER_API` | `sentimentTrends` chart | All |
| Google Trends (share of voice) | `SER_API` | `shareOfVoice` chart | All |
| Google News headlines | `SER_API` | `NewsHeadlinesCard` | Investors only |
| Glassdoor ratings (via Google Search) | `SER_API` | `GlassdoorCard` | Companies + Customers |
| Stock quotes | `Alpha_vantage` | `FinanceDataCard` | Investors only |
| LLM scoring + insights | `GROQ_API_KEY` | All insights, dimension scores | All |

### Always Synthetic (no real source yet)
- `churnFlows` — hash-based fake flows between companies
- `reviewCount` — hash-based unless Kaggle/Apify/SerpAPI provides real counts
- `dimensionDeltas` — computed from scores, not benchmarked against real market data

---

## The In-Memory Cache (`_cache` in `industry_service.py`)

The backend holds one dict per industry in process memory. It is **reset on server restart**. There is no Redis or persistent cache.

```python
_cache: dict[str, dict[str, Any]] = {}
```

On first GET for an industry, the cache is populated with mock scores and any live enrichments that can be fetched without running the full pipeline. After "Run Analysis" completes, `set_industry_cache_entry()` overwrites the cache with real scores, insights, and enrichments.

**Key pattern:** `set_industry_cache_entry()` uses "keep existing" fallback for optional fields:
```python
final_news = news_headlines if news_headlines is not None else existing.get("news_headlines")
```
This means a partial enrichment run won't wipe previously fetched data.

---

## Adapter Pattern (`resources/adapters.py`)

**Always import from `adapters.py`, never directly from sub-adapters.** This file provides graceful try/except ImportError wrappers for every data source. If a package or key is missing, the function returns `None` and the caller falls back gracefully.

All adapter functions return `Optional[...]` — never raise, never return empty strings as errors.

```python
# Pattern used throughout:
try:
    from resources.alphavantage_adapter import fetch_finance_data_for_companies as _av_fetch
except ImportError:
    try:
        from .alphavantage_adapter import fetch_finance_data_for_companies as _av_fetch
    except ImportError:
        _av_fetch = None
if _av_fetch:
    return _av_fetch(companies)
```

> **IDE linter note:** Every adapter shows "missing-module-attribute" errors in the IDE. This is a **false positive** — the linter doesn't have the project root in its Python search path. The code runs correctly at runtime. Do not "fix" these by restructuring imports.

---

## Adding a New Industry

1. Add entry to `INDUSTRY_CONFIG` in `industry_config.py`:
   - `name`, `focal`, `companies` (list), `dimensions` (dict key→label), `colors`, `mock_scores`, `data_file`
2. Add mock insights to `MOCK_INSIGHTS_BY_INDUSTRY` in `industry_config.py`
3. Create a `data/sample_reviews_{slug}.json` file with review objects
4. Add tickers to `COMPANY_TICKERS` in `resources/alphavantage_adapter.py` if companies are publicly traded

No frontend changes needed — the industry selector is dynamic.

---

## Adding a New API/Data Source

1. Create `resources/{source}_adapter.py` with fetch functions returning `Optional[...]`
2. Add wrapper function to `resources/adapters.py` following the try/except ImportError pattern
3. Call it in `run_analysis_core.py` in the `# enriching` section (steps 5–7 pattern)
4. Add the field to `set_industry_cache_entry()` and `get_industry_cache_entry()` in `industry_service.py`
5. Add to `build_industry_data()` payload (conditional: only include if not None)
6. Add TypeScript interface to `figma_export/src/app/data/mockData.ts`
7. Create a card component in `figma_export/src/app/components/cards/`
8. Add to `CHARTS_BY_AUDIENCE` in `Dashboard.tsx` for the relevant audience(s)
9. Update `audienceConfig.ts` resource status to `"integrated"`

---

## Frontend Data Flow

```
routes.tsx  →  Dashboard.tsx
                  useEffect → fetchIndustryData(industry)  [api.ts]
                           → GET /api/industry/{id}?audience={aud}
                  data: IndustryData | null
                  audience: "investors" | "companies" | "customers"  (from URL params)

Dashboard.tsx renders:
  - Charts gated by CHARTS_BY_AUDIENCE[audience]
  - Real-data cards (News, Finance, Glassdoor) only when data field is non-null
  - PersonalizationSection (from onboarding chat)
  - DashboardChat (floating, streaming)
  - isMock banner when data._meta.isMock === true
```

All API calls are in `figma_export/src/app/api.ts`. Auth token is stored in `localStorage` and attached as `Authorization: Bearer {token}` header.

---

## Key Components

| Component | File | Purpose |
|---|---|---|
| `Dashboard` | `components/Dashboard.tsx` | Main view, routes audience → charts |
| `PositioningMap` | `components/PositioningMap.tsx` | Price vs Value scatter |
| `SentimentAnalysis` | `components/SentimentAnalysis.tsx` | Trend line chart |
| `InsightsPanel` | `components/InsightsPanel.tsx` | AI insight cards |
| `DimensionBenchmarking` | `components/DimensionBenchmarking.tsx` | Bar chart vs category avg |
| `NewsHeadlinesCard` | `components/cards/NewsHeadlinesCard.tsx` | SerpAPI news (investors) |
| `FinanceDataCard` | `components/cards/FinanceDataCard.tsx` | Alpha Vantage stock quotes (investors) |
| `GlassdoorCard` | `components/cards/GlassdoorCard.tsx` | Glassdoor ratings (companies + customers) |
| `DashboardChat` | `components/DashboardChat.tsx` | Floating AI assistant |
| `PersonalizationSection` | `components/PersonalizationSection.tsx` | Onboarding chat results |

---

## API Endpoints

All backend routes are prefixed at `http://localhost:8001`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/industry/{id}` | Optional | Industry data payload (scores, charts, insights) |
| GET | `/api/industry/{id}?audience={aud}` | Optional | Same with audience context |
| GET | `/api/industry/{id}/export/scores.csv` | No | Download dimension scores as CSV |
| POST | `/api/run-analysis/stream` | No | SSE: full pipeline run for an industry |
| POST | `/api/chat/stream` | Optional | SSE: streaming chat with AI assistant |
| POST | `/api/chat/onboarding/stream` | Optional | SSE: onboarding chat (pre-login) |
| POST | `/api/personalization` | Optional | Extract insights from onboarding chat |
| POST | `/api/auth/register` | No | Create account |
| POST | `/api/auth/login` | No | Login → JWT |
| GET | `/api/auth/me` | Yes | Current user profile |
| GET | `/api/saved-views` | Yes | List saved bookmarks |
| POST | `/api/saved-views` | Yes | Save a bookmark |
| DELETE | `/api/saved-views/{id}` | Yes | Delete a bookmark |
| GET | `/docs` | No | Swagger UI |

---

## Pending Work / Known Issues

### Not Yet Implemented
- **OpenWebNinja Glassdoor API** (`Openweb_ninja` key is in `.env` but not wired). The key is from [app.openwebninja.com](https://app.openwebninja.com). The correct endpoint path is unknown — the `/glassdoor/company-overview` path returns "Missing Authentication Token" (AWS API Gateway 404-equivalent). Once the correct path is found, create `resources/openwebninja_adapter.py` and wire it into `fetch_glassdoor_for_industry()` in `adapters.py` as a primary source before the SerpAPI fallback.
- **SerpAPI App Store / Play Store** — planned for mobile-first industries, not started.
- **FactSet financial data** — placeholder in `adapters.py`, no implementation.

### Always Synthetic (no real equivalent yet)
- `churnFlows` — fake hash-based flows. Real data would come from cohort analysis or survey data.
- `reviewCount` — hash-based unless Kaggle/Apify/SerpAPI provides real counts (SerpAPI SoV is used as a proxy when available).

### Known Constraints
- **Cache resets on server restart** — all "Run Analysis" results are lost. No persistence layer for computed results.
- **Rate limits** — Alpha Vantage free tier: 25 requests/day, 5/minute. With 6 companies per industry this is tight. The adapter makes one request per company serially.
- **Alpha Vantage note** — free tier returns empty `Global Quote` for some tickers (e.g. LSE-listed `ROO` for Deliveroo). The adapter handles this gracefully (skips missing companies).
- **Glassdoor via SerpAPI** — uses Google Search `site:glassdoor.com` scraping, not a dedicated endpoint. Rating extraction uses regex on search snippets — not always reliable. Can return None for less-known companies.
- **Python 3.9** — the venv is Python 3.9. Use `Optional[X]` not `X | None`, `Dict[...]` not `dict[...]` in annotations when writing new code, or use `from __future__ import annotations`.

### Branch State
- Current branch: `_lucasbranch`
- Main branch: `fabrizio`
- PRs should target `fabrizio`

---

## Git Workflow

```bash
# Before starting work
git pull origin fabrizio
git checkout _lucasbranch
git merge fabrizio  # keep your branch up to date

# After making changes
git add <specific files>  # never git add -A blindly — .env must never be committed
git commit -m "feat: description"
git push origin _lucasbranch
# Open PR targeting fabrizio
```

**Never commit `.env`** — it contains live API keys. It is gitignored.

---

## Demo Walkthrough (for testing)

1. Open http://localhost:5173
2. Login: `demo@marketlens.ai` / `demo12345`
3. Onboarding: pick **Investors** + **CRM** → chat a question → click Continue
4. Dashboard loads with mock data and an amber "demo data" banner
5. Click **Run Analysis** → watch SSE progress → dashboard refreshes with real data
6. Switch audience (top-right selector) → charts change, real-data cards appear/disappear
7. Switch industry (top-left dropdown) → full reload for that industry
8. Try **Export CSV** and **Copy Insights** buttons
9. Use the floating chat (bottom-right) to ask follow-up questions

---

## File You Should Never Modify
- `venv/` — the entire virtual environment directory
- `data/insightengine.db` — live SQLite database
- `.env` — secret keys
- `figma_export/node_modules/` — npm packages
