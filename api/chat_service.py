"""Groq chat: system prompts, streaming, guided context."""

from typing import Iterator

from api.audience_config import AUDIENCE_CONFIG

DISCLAIMER = (
    "Disclaimer: This assistant provides research-style analytics only, not financial or investment advice. "
    "Verify figures with primary sources. Max message length: 1000 characters."
)


def _summarize_industry(industry_json: dict) -> str:
    """Build a compact text summary to keep token usage low (replaces raw JSON dump)."""
    meta = industry_json.get("_meta", {})
    companies = [c.get("name", "") for c in industry_json.get("companies", [])]
    lines = [
        f"Industry: {meta.get('industry', 'unknown')}",
        f"Data source: {meta.get('dataSource', 'unknown')}",
        f"Total reviews analysed: {meta.get('totalReviews', 0)}",
        f"Companies: {', '.join(companies)}",
    ]

    # Dimension scores: best/worst per dimension
    lines.append("Dimension scores (0-100, higher=better):")
    for d in industry_json.get("dimensions", []):
        name = d.get("name", "")
        scores = d.get("scores", {})
        if scores:
            best_id = max(scores, key=lambda k: scores[k])
            worst_id = min(scores, key=lambda k: scores[k])
            # Map company id back to name
            co_map = {c.get("id", ""): c.get("name", c.get("id", "")) for c in industry_json.get("companies", [])}
            lines.append(
                f"  {name}: best={co_map.get(best_id, best_id)}({scores[best_id]}), "
                f"worst={co_map.get(worst_id, worst_id)}({scores[worst_id]})"
            )

    # Top insights (up to 6)
    all_insights = []
    for aud_insights in industry_json.get("insights", {}).values():
        all_insights.extend(aud_insights)
    if all_insights:
        lines.append("Top insights:")
        for ins in all_insights[:6]:
            lines.append(f"  • {ins.get('title', '')}: {ins.get('description', '')[:120]}")

    return "\n".join(lines)


def build_system_prompt(
    *,
    industry_json: dict | None,
    audience: str | None,
    guided_questions: list[str],
) -> str:
    parts = [
        "You are MarketLens AI, a helpful market intelligence assistant.",
        DISCLAIMER,
        "Use the industry data when provided; cite companies and dimensions from it. Be concise.",
    ]
    if audience and audience in AUDIENCE_CONFIG:
        parts.append(f"User audience: {audience}. {AUDIENCE_CONFIG[audience]['description']}")
    parts.append("Suggested questions the user may tap (you may reference them): " + "; ".join(guided_questions[:12]))
    if industry_json:
        parts.append("Industry data summary:\n" + _summarize_industry(industry_json))
    return "\n\n".join(parts)


def stream_groq_reply(
    client,
    model: str,
    messages: list[dict],
) -> Iterator[str]:
    """Yield text deltas from Groq chat completions."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,
        max_tokens=2048,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def groq_chat_non_stream(client, model: str, messages: list[dict]) -> str:
    r = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,
        max_tokens=2048,
    )
    return (r.choices[0].message.content or "").strip()
