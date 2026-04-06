#!/usr/bin/env python3
"""
InsightEngine — Market Intelligence Pipeline
Phase 2 Prototype · CRM Software · HubSpot Focus

Pipeline: Reviews → Aspect-Based Sentiment → Dimension Scores → Strategic Insights → HTML

Usage:
    # Groq (recommended — fast + free tier):
    export GROQ_API_KEY=gsk_...
    python pipeline.py --data data/sample_reviews.json

    # OpenAI fallback:
    export OPENAI_API_KEY=sk-...
    python pipeline.py --data data/sample_reviews.json

    # No API key — pre-computed mock scores:
    python pipeline.py --mock

Models used with Groq:
    Aspect extraction : llama-3.1-8b-instant  (fast, cheap)
    Insight synthesis : llama-3.3-70b-versatile (high quality)
"""

import json
import os
import argparse
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Optional, Tuple

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

if not GROQ_AVAILABLE and not OPENAI_AVAILABLE:
    print("Warning: no LLM client installed. Run: pip install groq  (or: pip install openai)")

# ── Configuration ────────────────────────────────────────────────────────────

VERTICAL = "CRM Software"
FOCAL_COMPANY = "HubSpot"
COMPETITORS = ["Salesforce", "Pipedrive", "Zoho CRM"]
ALL_COMPANIES = [FOCAL_COMPANY] + COMPETITORS

DIMENSIONS = {
    "ease_of_use":          "Ease of Use",
    "feature_richness":     "Feature Richness",
    "customer_support":     "Customer Support",
    "integrations":         "Integrations",
    "value_for_money":      "Value for Money",
    "reporting_analytics":  "Reporting & Analytics",
}

# Evaluation rubric: what makes a good insight (Phase 1 deliverable)
INSIGHT_RUBRIC = {
    "obvious":   "Restates what you'd find in 10 minutes on Google. Fails.",
    "useful":    "Non-obvious, specific, actionable. Ties scores to strategic implications. Passes.",
    "wrong":     "Contradicted by data or factually incorrect. Fails — damages trust.",
}

# Pre-computed scores (from GPT-4o-mini analysis of 826 production reviews)
# Used when --mock flag is set or no API key is available
MOCK_SCORES = {
    "HubSpot":    {
        "ease_of_use": 78, "feature_richness": 72, "customer_support": 65,
        "integrations": 80, "value_for_money": 58, "reporting_analytics": 70,
    },
    "Salesforce": {
        "ease_of_use": 48, "feature_richness": 92, "customer_support": 62,
        "integrations": 95, "value_for_money": 38, "reporting_analytics": 88,
    },
    "Pipedrive":  {
        "ease_of_use": 88, "feature_richness": 65, "customer_support": 75,
        "integrations": 72, "value_for_money": 78, "reporting_analytics": 65,
    },
    "Zoho CRM":   {
        "ease_of_use": 62, "feature_richness": 82, "customer_support": 55,
        "integrations": 75, "value_for_money": 82, "reporting_analytics": 70,
    },
}

MOCK_INSIGHTS = [
    {
        "title": "Pricing Pressure Is HubSpot's Biggest Structural Risk",
        "body": (
            "Value for money scores declined from 68 → 58 over six quarters — a 15% drop that no "
            "other dimension approaches. Critically, 34% of HubSpot's negative reviews now explicitly "
            "mention pricing vs. 22% four quarters ago. This is concentrated in the $50–200/seat range "
            "where Pipedrive (78/100 on value) is a credible substitute."
        ),
        "audience": "Companies",
        "confidence": "High",
        "action": "Audit pricing tier structure for SMB buyers; launch a transparent comparison page before competitors define the narrative.",
    },
    {
        "title": "Customer Support Is the Category's Unclaimed Whitespace",
        "body": (
            "No player in this category scores above 75/100 on support, and the average has flatlined "
            "at 64 for six consecutive quarters — despite support being the #1 pain point across all "
            "four platforms. This points to a structural unit-economics constraint: incumbents can't fix "
            "this cheaply. It is a genuine moat opportunity for an AI-native challenger."
        ),
        "audience": "Investors",
        "confidence": "High",
        "action": "Support-first CRM challengers deserve a premium multiple; incumbents are structurally unlikely to close this gap without material margin dilution.",
    },
    {
        "title": "Pipedrive's Review Volume Signals Word-of-Mouth Inflection",
        "body": (
            "Pipedrive's review volume is up 23% YoY vs HubSpot's 11%, and it holds the only "
            "improving sentiment trajectory (+2.1 pts over 18 months). Highest ease-of-use (88/100) "
            "plus highest value-for-money (78/100) plus accelerating review growth is a classic "
            "organic SMB word-of-mouth signal. A reporting upgrade without sacrificing simplicity "
            "would position Pipedrive to compete directly for HubSpot's core segment."
        ),
        "audience": "Investors",
        "confidence": "Medium",
        "action": "Model a scenario where Pipedrive cannibalises 5–8% of HubSpot's SMB seat additions over the next 18 months.",
    },
    {
        "title": "Salesforce's Mid-Market Churn Signal Is Elevated",
        "body": (
            "Negative reviews mentioning 'moving to,' 'switching from,' or 'left because' grew 18% "
            "QoQ for Salesforce — the highest churn signal in the dataset. The cause is not product "
            "quality (feature score 92/100) but a complexity-to-value mismatch: 'too powerful for "
            "what we need' appears in 28% of negative reviews. This creates a predictable downward "
            "migration: Salesforce → HubSpot → Pipedrive, each step trading depth for simplicity."
        ),
        "audience": "Companies",
        "confidence": "Medium",
        "action": "Launch a 'Salesforce Simplifier' migration campaign targeting 20–200 seat companies; lead with setup speed and total cost of ownership.",
    },
    {
        "title": "Value Decline Is a Category Signal, Not Just HubSpot's Problem",
        "body": (
            "Average value-for-money across all four players fell from 72 → 64 over 18 months, "
            "coinciding with post-2022 SaaS repricing. This is a structural market shift, not "
            "company-specific noise. Historically this pattern — broad perceived-value decline "
            "in an established category — precedes successful entry by price-transparent, "
            "usage-based challengers. The window is roughly 18–36 months before incumbents adapt."
        ),
        "audience": "Investors",
        "confidence": "High",
        "action": "Watch for usage-based pricing CRM entrants; prioritise the one with the clearest pricing page and the shortest self-serve onboarding path.",
    },
]


# ── Core Analysis Functions ──────────────────────────────────────────────────

ASPECT_PROMPT_TEMPLATE = """Analyze this CRM software review and score each dimension from 0 to 100.

Scale: 0 = very negative experience, 50 = neutral / not mentioned well, 100 = very positive experience.
Rule: Only score a dimension if it is explicitly discussed. Return null if not mentioned.

Review:
{review_text}

Dimensions to score:
{dimensions}

Respond with valid JSON only — no explanation, no markdown fences:
{json_schema}"""


def analyze_review_aspects(review_text: str, client, fast_model: str, dimensions: Optional[dict] = None) -> dict:
    """Extract aspect-based sentiment scores for a single review."""
    dims = dimensions or DIMENSIONS
    dim_lines = "\n".join(f"  - {k}: {v}" for k, v in dims.items())
    schema = "{" + ", ".join(f'"{k}": <int 0-100 or null>' for k in dims) + "}"

    prompt = ASPECT_PROMPT_TEMPLATE.format(
        review_text=review_text,
        dimensions=dim_lines,
        json_schema=schema,
    )

    response = client.chat.completions.create(
        model=fast_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def stratified_subsample_reviews(reviews: list, comps: list, max_reviews: int) -> list:
    """
    Cap how many reviews we score (biggest latency win). Keeps a round-robin mix
    across companies so scores stay representative.
    """
    if max_reviews <= 0 or len(reviews) <= max_reviews:
        return reviews
    buckets = {c: [] for c in comps}
    for r in reviews:
        co = r.get("company")
        if co in buckets:
            buckets[co].append(r)
    for b in buckets.values():
        random.shuffle(b)
    out: list = []
    while len(out) < max_reviews and any(buckets.values()):
        for c in comps:
            if len(out) >= max_reviews:
                return out
            if buckets[c]:
                out.append(buckets[c].pop())
    return out


def _analyze_review_job(
    review: dict,
    client,
    fast_model: str,
    dim_keys: tuple,
) -> Tuple[Optional[str], Optional[dict]]:
    """Returns (company, aspect_scores) or (None, None) on skip/failure."""
    company = review.get("company")
    if not company:
        return None, None
    try:
        scores = analyze_review_aspects(review["text"], client, fast_model, dict(dim_keys))
        return company, scores
    except Exception as e:
        rid = review.get("id", "?")
        print(f"  Warning: failed review {rid}: {e}")
        return None, None


def compute_dimension_scores(reviews: list, client=None, fast_model: str = "", use_mock: bool = False,
                            companies: Optional[list] = None, dimensions: Optional[dict] = None,
                            mock_scores: Optional[dict] = None,
                            max_reviews: Optional[int] = None,
                            parallel_workers: Optional[int] = None) -> dict:
    """
    Compute average dimension scores per company across all reviews.
    Falls back to mock_scores (or MOCK_SCORES) if use_mock=True or no API client.
    """
    comps = companies or ALL_COMPANIES
    dims = dimensions or DIMENSIONS
    mock = mock_scores or MOCK_SCORES

    if use_mock or client is None:
        print("  -> Using pre-computed mock scores")
        return mock

    mr = max_reviews if max_reviews is not None else _env_int("PIPELINE_MAX_REVIEWS", 64)
    workers = parallel_workers if parallel_workers is not None else _env_int("PIPELINE_PARALLEL_WORKERS", 8)
    seq = os.getenv("PIPELINE_SEQUENTIAL", "").lower() in ("1", "true", "yes")
    if seq:
        workers = 1

    sampled = stratified_subsample_reviews(reviews, comps, mr)
    dim_keys = tuple(dims.items())
    print(
        f"  -> Analyzing {len(sampled)} reviews (of {len(reviews)}) with {fast_model} "
        f"({'sequential' if workers <= 1 else f'parallel workers={workers}'})..."
    )

    company_buckets: dict[str, dict[str, list]] = {
        c: {d: [] for d in dims} for c in comps
    }

    def _merge(company: str, scores: dict) -> None:
        for dim in dims:
            val = scores.get(dim)
            if isinstance(val, (int, float)):
                company_buckets[company][dim].append(float(val))

    if workers <= 1:
        for i, review in enumerate(sampled):
            company = review.get("company")
            if company not in comps:
                continue
            try:
                scores = analyze_review_aspects(review["text"], client, fast_model, dims)
                _merge(company, scores)
            except Exception as e:
                print(f"  Warning: failed review {review.get('id', i)}: {e}")
            if (i + 1) % 10 == 0:
                print(f"    {i + 1}/{len(sampled)} reviews processed...")
    else:
        done = 0
        total = len(sampled)
        with ThreadPoolExecutor(max_workers=min(workers, max(1, total))) as ex:
            futs = [
                ex.submit(_analyze_review_job, r, client, fast_model, dim_keys)
                for r in sampled
            ]
            for fut in as_completed(futs):
                company, scores = fut.result()
                done += 1
                if company and scores:
                    _merge(company, scores)
                if done % 10 == 0 or done == total:
                    print(f"    {done}/{total} reviews processed...")

    return {
        company: {
            dim: round(sum(vals) / len(vals), 1) if vals else None
            for dim, vals in bucket.items()
        }
        for company, bucket in company_buckets.items()
    }


SYNTHESIS_PROMPT = """You are a senior market intelligence analyst. Your job is to generate non-obvious strategic insights — not to restate scores.

Vertical: {vertical}
Focal company: {focal}
Competitors: {competitors}

Dimension scores (0–100 per company, higher = better customer sentiment):
{scores_json}

Evaluation rubric:
- USEFUL (pass): non-obvious, ties scores to strategic implications or competitive dynamics
- OBVIOUS (fail): restates what a user finds in 10 minutes on Google
- WRONG (fail): contradicted by the data

Generate 8–12 USEFUL insights total. Distribute across Investors (3–4), Companies (4–5), Customers (2–3).
Each insight must cite specific evidence from the scores. Prioritise insights that directly answer the audience questions below.
{use_cases_section}

Return JSON:
{{
  "insights": [
    {{
      "title": "<5-8 word punchy title>",
      "body": "<2-3 sentences: what the data shows + why it matters strategically>",
      "audience": "<Investors | Companies | Customers>",
      "confidence": "<High | Medium | Low>",
      "action": "<1-sentence recommended action>"
    }}
  ]
}}"""


def generate_insights(scores: dict, client, smart_model: str,
                     vertical: Optional[str] = None, focal: Optional[str] = None,
                     competitors: Optional[list] = None,
                     use_cases: Optional[list[str]] = None) -> list:
    """Synthesise 5 strategic insights using a frontier/smart model."""
    v = vertical or VERTICAL
    f = focal or FOCAL_COMPANY
    c = competitors or COMPETITORS
    uc_section = ""
    if use_cases:
        uc_section = "\nPrioritise insights that address these audience questions:\n" + "\n".join(f"  - {q}" for q in use_cases)
    prompt = SYNTHESIS_PROMPT.format(
        vertical=v,
        focal=f,
        competitors=", ".join(c),
        scores_json=json.dumps(scores, separators=(",", ":")),
        use_cases_section=uc_section,
    )
    insight_tokens = _env_int("GROQ_INSIGHT_MAX_TOKENS", 3072)
    response = client.chat.completions.create(
        model=smart_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=min(insight_tokens, 8192),
    )
    raw = response.choices[0].message.content
    # Sanitize Unicode that can cause charmap errors on Windows (e.g. ->, –)
    raw = raw.replace("\u2192", "->").replace("\u2013", "-").replace("\u2014", "-")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  Warning: failed to parse insights JSON: {e}")
        return []
    insights = parsed.get("insights")
    if not isinstance(insights, list):
        print("  Warning: LLM response missing 'insights' list — returning empty.")
        return []
    for ins in insights:
        for key in ("body", "title", "action"):
            if key in ins and isinstance(ins[key], str):
                ins[key] = ins[key].replace("\u2192", "->").replace("\u2013", "-").replace("\u2014", "-")
    return insights


EXECUTIVE_BRIEF_PROMPT = """You are a senior market intelligence analyst writing a concise executive brief.

Vertical: {vertical}
Focal company: {focal}
Competitors: {competitors}
Dimension scores (0-100): {scores_json}

Write a single flowing paragraph of 120-160 words that:
1. Opens with the single most important competitive dynamic in this market
2. Names specific companies and scores to support every claim
3. Identifies the clearest winner and loser, and why
4. Closes with the key strategic implication for decision-makers

Tone: direct, confident, no hedging. No bullet points. No headers. Plain paragraph only.
Return JSON: {{"brief": "<paragraph text>"}}"""


def generate_executive_brief(
    scores: dict,
    client: Any,
    smart_model: str,
    vertical: Optional[str] = None,
    focal: Optional[str] = None,
    competitors: Optional[list] = None,
) -> str:
    """Generate a single executive brief paragraph from dimension scores."""
    v = vertical or VERTICAL
    f = focal or FOCAL_COMPANY
    c = competitors or COMPETITORS
    prompt = EXECUTIVE_BRIEF_PROMPT.format(
        vertical=v,
        focal=f,
        competitors=", ".join(c),
        scores_json=json.dumps(scores, separators=(",", ":")),
    )
    try:
        response = client.chat.completions.create(
            model=smart_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.6,
            max_tokens=512,
        )
        raw = response.choices[0].message.content
        raw = raw.replace("\u2192", "->").replace("\u2013", "-").replace("\u2014", "-")
        parsed = json.loads(raw)
        brief = parsed.get("brief", "")
        return brief if isinstance(brief, str) else ""
    except Exception as e:
        print(f"  Warning: executive brief generation failed: {e}")
        return ""


# ── KPI Computation ──────────────────────────────────────────────────────────

def compute_kpis(scores: dict, reviews: list) -> dict:
    """Derive high-level KPIs from dimension scores and review metadata."""
    # Use the actual companies/dimensions present in scores, not hardcoded globals
    comps = list(scores.keys()) or ALL_COMPANIES
    dims = set()
    for sc in scores.values():
        dims.update(sc.keys())
    dims = dims or set(DIMENSIONS.keys())

    review_counts = defaultdict(int)
    for r in reviews:
        co = r.get("company")
        if co in comps:
            review_counts[co] += 1

    total_reviews = sum(review_counts.values()) or 1

    # Overall score: unweighted average of all dimensions
    overall = {}
    for company, dim_scores in scores.items():
        vals = [v for v in dim_scores.values() if isinstance(v, (int, float))]
        if vals:
            overall[company] = round(sum(vals) / len(vals), 1)

    # Category average per dimension
    cat_avg = {}
    for dim in dims:
        vals = [scores[c].get(dim, 0) for c in comps if isinstance(scores[c].get(dim), (int, float))]
        cat_avg[dim] = round(sum(vals) / len(vals), 1) if vals else 0

    # Share of voice (review volume %)
    sov = {
        c: round(100 * review_counts[c] / total_reviews, 1)
        for c in comps
    }

    # Whitespace: dimensions where max score < 75
    whitespace = [
        dim for dim in dims
        if all(scores[c].get(dim, 0) < 75 for c in comps)
    ]

    # Focal rank on value_for_money (gracefully handles missing key)
    value_key = "value_for_money"
    focal_rank = None
    if FOCAL_COMPANY in comps and value_key in dims:
        ranked = sorted(comps, key=lambda c: scores[c].get(value_key, 0), reverse=True)
        try:
            focal_rank = ranked.index(FOCAL_COMPANY) + 1
        except ValueError:
            focal_rank = None

    return {
        "overall": overall,
        "category_average": cat_avg,
        "share_of_voice": sov,
        "review_counts": dict(review_counts),
        "whitespace_dimensions": whitespace,
        "focal_rank_value": focal_rank,
    }


# ── CLI Entry Point ───────────────────────────────────────────────────────────

def print_results(scores: dict, kpis: dict, insights: list) -> None:
    """Pretty-print results to terminal."""
    print("\n" + "=" * 60)
    print("DIMENSION SCORES")
    print("=" * 60)
    header = f"{'Dimension':<28}" + "".join(f"{c[:12]:<14}" for c in ALL_COMPANIES)
    print(header)
    print("-" * len(header))
    for dim, label in DIMENSIONS.items():
        row = f"{label:<28}"
        for company in ALL_COMPANIES:
            score = scores.get(company, {}).get(dim)
            row += f"{str(score) if score is not None else 'N/A':<14}"
        print(row)

    print("\n" + "=" * 60)
    print("KEY KPIS")
    print("=" * 60)
    print(f"Overall scores:    {kpis['overall']}")
    print(f"Share of voice:    {kpis['share_of_voice']}")
    print(f"Value rank:        {FOCAL_COMPANY} is #{kpis['focal_rank_value']} of {len(ALL_COMPANIES)}")
    print(f"Whitespace dims:   {kpis['whitespace_dimensions'] or 'None found'}")

    print("\n" + "=" * 60)
    print(f"STRATEGIC INSIGHTS ({len(insights)} generated)")
    print("=" * 60)
    for i, ins in enumerate(insights, 1):
        print(f"\n{i}. [{ins['audience']}] [{ins['confidence']} confidence] {ins['title']}")
        print(f"   {ins['body'][:120]}...")
        print(f"   -> {ins['action']}")


def build_client():
    """
    Auto-detect available LLM provider.
    Priority: Groq (GROQ_API_KEY) → OpenAI (OPENAI_API_KEY) → None (mock mode)
    Returns (client, fast_model, smart_model, provider_name)
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and GROQ_AVAILABLE:
        client = Groq(api_key=groq_key)
        fast = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
        smart = os.getenv(
            "GROQ_INSIGHTS_MODEL",
            os.getenv("GROQ_SMART_MODEL", "llama-3.3-70b-versatile"),
        )
        return client, fast, smart, "Groq"

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and OPENAI_AVAILABLE:
        client = openai.OpenAI(api_key=openai_key)
        fast = os.getenv("OPENAI_FAST_MODEL", "gpt-4o-mini")
        smart = os.getenv("OPENAI_INSIGHTS_MODEL", os.getenv("OPENAI_SMART_MODEL", "gpt-4o"))
        return client, fast, smart, "OpenAI"

    return None, "", "", "none"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="InsightEngine: reviews → dimension scores → strategic insights"
    )
    parser.add_argument("--data", default="data/sample_reviews.json",
                        help="Path to reviews JSON file")
    parser.add_argument("--output", default="outputs/report.json",
                        help="Output path for JSON results (use index.html for the visual report)")
    parser.add_argument("--mock", action="store_true",
                        help="Use pre-computed scores and insights (no API key needed)")
    args = parser.parse_args()

    print("InsightEngine Pipeline — Phase 2 Prototype")
    print(f"Vertical: {VERTICAL} | Focal: {FOCAL_COMPANY}")
    print("-" * 50)

    # Step 1: Load reviews
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: reviews file not found at {data_path}")
        sys.exit(1)
    with open(data_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)
    print(f"[1/4] Loaded {len(reviews)} reviews from {data_path}")

    # Step 2: Init LLM client
    client, fast_model, smart_model, provider = build_client()
    if args.mock or client is None:
        if client is None and not args.mock:
            print("[2/4] No API key found (GROQ_API_KEY or OPENAI_API_KEY) → mock mode")
            print("      Install Groq: pip install groq  then set GROQ_API_KEY=gsk_...")
        else:
            print("[2/4] Mock mode enabled")
        client = None
    else:
        print(f"[2/4] {provider} client ready")
        print(f"      Aspect extraction : {fast_model}")
        print(f"      Insight synthesis : {smart_model}")

    # Step 3: Compute dimension scores
    print("[3/4] Computing dimension scores...")
    scores = compute_dimension_scores(reviews, client, fast_model, use_mock=args.mock or client is None)

    # Step 4: Generate insights
    print("[4/4] Generating strategic insights...")
    if client and not args.mock:
        insights = generate_insights(scores, client, smart_model)
        print(f"  -> {len(insights)} insights generated via {smart_model}")
    else:
        insights = MOCK_INSIGHTS
        print(f"  -> Using {len(insights)} pre-computed insights")

    # Compute KPIs
    kpis = compute_kpis(scores, reviews)

    # Print to terminal
    print_results(scores, kpis, insights)

    # Save JSON output
    output = {
        "generated_at": datetime.now().isoformat(),
        "vertical": VERTICAL,
        "focal_company": FOCAL_COMPANY,
        "dimension_scores": scores,
        "kpis": kpis,
        "insights": insights,
        "review_count": len(reviews),
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")
    print("Open index.html in your browser for the full visual report.")


if __name__ == "__main__":
    main()
