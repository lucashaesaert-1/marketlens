"""Compute personalized metrics/charts from chat + industry JSON via Groq."""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

PERSONALIZATION_PROMPT = """You are a market intelligence assistant. Given:
1) The user's stated audience role (investor, company strategist, or end customer)
2) A transcript of their questions and your prior replies in the onboarding chat
3) The full industry JSON (companies, dimensions, scores, insights structure)

Produce personalization that will drive extra dashboard widgets. Respond with ONLY valid JSON (no markdown) matching this schema:
{
  "narrative_summary": "string, max 400 chars",
  "focus_dimensions": [ {"label": "string", "relevance": 0-100, "rationale": "short string"} ],
  "suggested_kpis": [ {"name": "string", "value": "string or number as string", "hint": "string" } ],
  "insights_from_chat": [ {"title": "string", "description": "string", "impact": "high"|"medium"|"low" } ],
  "chart_series": {
    "priority_scores": [ {"name": "string", "score": number } ]
  }
}

Rules:
- Tie focus_dimensions to dimensions that appear in the industry JSON and reflect the user's questions.
- suggested_kpis: 3-5 items derived from the data (e.g. share of voice, a dimension gap).
- insights_from_chat: 2-4 non-duplicate insights explicitly grounded in the user's interests (label these mentally as "from your questions").
- chart_series.priority_scores: 4-8 named bars 0-100 for a simple bar chart (themes or dimensions the user cares about).
- Do not invent companies; only use names from the JSON.
- Keep financial language non-advisory; this is analytics, not investment advice.
"""


class FocusDimension(BaseModel):
    label: str
    relevance: int = Field(ge=0, le=100)
    rationale: str = ""


class SuggestedKpi(BaseModel):
    name: str
    value: str
    hint: str = ""


class ChatInsight(BaseModel):
    title: str
    description: str
    impact: str = "medium"


class ChartSeries(BaseModel):
    priority_scores: list[dict[str, Any]] = Field(default_factory=list)


class PersonalizationPayload(BaseModel):
    narrative_summary: str = ""
    focus_dimensions: list[FocusDimension] = Field(default_factory=list)
    suggested_kpis: list[SuggestedKpi] = Field(default_factory=list)
    insights_from_chat: list[ChatInsight] = Field(default_factory=list)
    chart_series: ChartSeries = Field(default_factory=ChartSeries)


def compute_personalization(
    *,
    audience: str,
    industry_json: dict,
    chat_transcript: str,
    client: Any,
    model: str,
) -> dict:
    """Call Groq with JSON-mode style completion; parse into dict for API response."""
    user_content = json.dumps(
        {
            "audience": audience,
            "industry_json": industry_json,
            "chat_transcript": chat_transcript[:12000],
        },
        ensure_ascii=False,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PERSONALIZATION_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "narrative_summary": "Personalization could not be parsed; showing defaults.",
            "focus_dimensions": [],
            "suggested_kpis": [],
            "insights_from_chat": [],
            "chart_series": {"priority_scores": []},
        }
    try:
        validated = PersonalizationPayload.model_validate(data)
        return validated.model_dump()
    except Exception as exc:
        logger.warning("Personalization validation failed, using defaults: %s", exc)
        return PersonalizationPayload().model_dump()


def get_smart_model_from_env() -> str:
    return os.getenv(
        "GROQ_INSIGHTS_MODEL",
        os.getenv("GROQ_SMART_MODEL", "llama-3.3-70b-versatile"),
    )
