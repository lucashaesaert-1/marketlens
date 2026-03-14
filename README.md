# InsightEngine — Market Intelligence Prototype

> **Assignment Deliverable · Phase 2 Complete**  
> Rapid topic exploration and insight generation tool — CRM Software vertical, HubSpot focus.

---

## What This Is

A working prototype that ingests customer reviews, runs aspect-based sentiment analysis via LLM, computes competitive dimension scores, and generates strategic insights — delivered as a static HTML report.

**Vertical:** CRM Software  
**Focal company:** HubSpot  
**Competitors:** Salesforce, Pipedrive, Zoho CRM  
**Dimensions:** Ease of Use · Feature Richness · Customer Support · Integrations · Value for Money · Reporting & Analytics

---

## Files

```
.
├── index.html                   ← Main deliverable — open this in a browser
├── pipeline.py                  ← Analysis pipeline (Python)
├── data/
│   └── sample_reviews.json      ← 30 representative reviews (demo dataset)
├── outputs/                     ← Generated JSON results land here
└── README.md                    ← This file
```

---

## Quickstart

### Option A — Streamlit app (recommended)

```powershell
python -m streamlit run app.py
```

Opens at **http://localhost:8501** with interactive Plotly charts, audience filters, and a live analysis mode sidebar.

### Option B — Static HTML report (no setup needed)

```
Open index.html in any browser
```

Fully self-contained pre-generated report.

### Option C — Pipeline only (terminal output + JSON)

```powershell
# Mock mode (no API key):
python pipeline.py --mock

# With Groq (recommended):
$env:GROQ_API_KEY = "gsk_..."
python pipeline.py --data data/sample_reviews.json

# With OpenAI:
$env:OPENAI_API_KEY = "sk-..."
python pipeline.py --data data/sample_reviews.json
```

> **Note (Windows):** Use `python -m pip` instead of `pip`, and `python -m streamlit` instead of `streamlit` if those commands aren't found.

---

## Architecture

```
Reviews (JSON)
      │
      ▼
[pipeline.py]
      │
      ├── GPT-4o-mini  →  Aspect-based sentiment per review (6 dimensions × N reviews)
      │                   Cost: ~$0.004 / 1,000 reviews
      │
      ├── Aggregation  →  Average dimension score per company
      │
      ├── GPT-4o       →  Synthesis layer — "so what" strategic insights
      │
      └── Output       →  JSON results + static HTML report
```

**No training from scratch.** The architecture is prompt engineering + RAG-ready. The LLM does three jobs:
1. `gpt-4o-mini` — aspect extraction (cheap, high-volume)
2. `gpt-4o` — insight synthesis (frontier quality, low-volume)
3. Template-driven HTML rendering — no server needed

---

## Dimensions & Scoring

| Dimension | What it measures |
|-----------|-----------------|
| Ease of Use | How intuitive / learnable the product is |
| Feature Richness | Breadth and completeness of functionality |
| Customer Support | Quality, speed, and helpfulness of support |
| Integrations | Ecosystem depth; connects to user's existing stack |
| Value for Money | Perceived price-to-value ratio |
| Reporting & Analytics | Quality of reporting, dashboards, forecasting |

Scores are 0–100. Each review is scored per dimension only if that dimension is explicitly discussed. Null scores are excluded from averages to avoid dilution.

---

## Evaluation Rubric (Phase 1)

Used to score each AI-generated insight in Phase 3 user sessions:

| Rating | Criteria |
|--------|----------|
| **Useful ✅** | Non-obvious, ties scores to strategic implications, something not findable in 10 min on Google |
| **Obvious ⚠️** | Restates what is already known; no new information or connection to implications |
| **Wrong ❌** | Contradicted by data or factually incorrect — **worst failure mode**, destroys trust |

Phase 3 questions for test users:
- Is anything here surprising to you?
- Would you act on any of these insights?
- What would you distrust or want to verify?

---

## KPIs Tracked

**Competitive position**
- Relative sentiment score vs category average
- Share of voice (review volume %)
- Price index vs category average
- Perceived value rank

**Customer signals**
- Aspect score per dimension (0–100)
- Sentiment trend over 9 quarters
- Top complaint themes (% of negative reviews)
- Top praise themes (% of positive reviews)

**Market dynamics**
- Competitor activity signals (news, job postings, pricing)
- Review volume growth (YoY %)
- Whitespace index (dimensions where all players score <75)
- Value-for-money trend across category

---

## Phase 4 — What Was Learned (Preliminary)

### What worked
- **Dimension scoring is tractable and compelling.** Structured quantitative output from reviews is the most defensible part of the pipeline. Users respond to it.
- **Aspect-based sentiment via prompted LLM is viable.** GPT-4o-mini reliably extracts dimension scores from review text. Cost is low (~$4/1k reviews).
- **Static HTML output is the right format for a prototype.** Zero setup friction for evaluators. Charts render immediately.

### What didn't work well
- **First-pass insights were too generic.** Without explicit rubric enforcement in the prompt, the synthesis model defaulted to restating scores. Solved by adding the "obvious/useful/wrong" rubric directly to the system prompt.
- **Data access is the real constraint.** The most valuable signals (SimilarWeb traffic, real-time pricing, LinkedIn job volume) are paywalled. The prototype uses indicative signals only.

### Key open question
**Do users trust the output enough to act on it?** This is the product question. Everything else is solvable with engineering. Trust requires: traceable sources, calibrated confidence scores, and at least one time the insight was verifiably correct in the user's context.

---

## Integration Priority (as specified)

1. **Reviews** ← Current prototype
2. News (NewsAPI) ← Simulated in competitor signals section
3. Pricing (scraped pricing pages)
4. Financials (Crunchbase, SEC filings)

---

## Audiences & What They Care About

| Audience | Primary questions |
|----------|------------------|
| **Investors** | Defensible moat? Comparable companies' margins? Who is growing fastest? What whitespace exists? |
| **Companies** | What are customers complaining about? What are competitors doing that we aren't? What is our pricing power? |
| **Customers** | How does this product compare to alternatives on the dimensions I care about? |

The current report is optimised for **Investors** and **Companies**. Each insight is tagged with its primary audience.

---

## Cost Estimate (Production Scale)

| Component | Cost per run |
|-----------|-------------|
| 1,000 reviews × GPT-4o-mini (aspect extraction) | ~$0.004 |
| 5 insights × GPT-4o (synthesis) | ~$0.05 |
| Total per company per run | **~$0.10** |
| 4 companies, weekly refresh | **~$0.40/week** |

Data acquisition (web scraping, NewsAPI, etc.) is the dominant cost — not model inference.
