"""Groq chat: system prompts, streaming, guided context."""

import json
from typing import Iterator

from api.audience_config import AUDIENCE_CONFIG

DISCLAIMER = (
    "Disclaimer: This assistant provides research-style analytics only, not financial or investment advice. "
    "Verify figures with primary sources. Max message length: 1000 characters."
)


def build_system_prompt(
    *,
    industry_json: dict | None,
    audience: str | None,
    guided_questions: list[str],
) -> str:
    parts = [
        "You are MarketLens AI, a helpful market intelligence assistant.",
        DISCLAIMER,
        "Use the industry JSON when provided; cite companies and dimensions from it. Be concise.",
    ]
    if audience and audience in AUDIENCE_CONFIG:
        parts.append(f"User audience: {audience}. {AUDIENCE_CONFIG[audience]['description']}")
    parts.append("Suggested questions the user may tap (you may reference them): " + "; ".join(guided_questions[:12]))
    if industry_json:
        parts.append("Full industry data (JSON):\n" + json.dumps(industry_json, ensure_ascii=False)[:100000])
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
