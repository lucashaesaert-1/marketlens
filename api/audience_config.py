"""
Audience → Use Cases → Resources data model (Python)
Mirrors figma_export/src/app/data/audienceConfig.ts
"""

from typing import Literal

Audience = Literal["investors", "companies", "customers"]

AUDIENCE_CONFIG = {
    "investors": {
        "audience": "investors",
        "description": "Focus on defensible moats, competitive margins, and market dynamics",
        "use_cases": [
            {"id": "moat", "question": "Defensible moat?"},
            {"id": "margins", "question": "Comparable companies' margins?"},
            {"id": "growth", "question": "Who is growing fastest?"},
            {"id": "whitespace", "question": "What whitespace exists?"},
            {"id": "unit-economics", "question": "Unit economics vs peers?"},
            {"id": "churn-risk", "question": "Churn risk?"},
            {"id": "pricing-power", "question": "Pricing power vs category?"},
            {"id": "market-share", "question": "Market share trajectory?"},
        ],
        "resources": [
            {"id": "factset", "name": "FactSet", "type": "api", "status": "planned", "notes": "Financial data, comparables"},
        ],
    },
    "companies": {
        "audience": "companies",
        "description": "Identify customer pain points, competitive gaps, and strategic opportunities",
        "use_cases": [
            {"id": "complaints", "question": "Main customer complaints?"},
            {"id": "competitors", "question": "Competitor moves we're missing?"},
            {"id": "pricing", "question": "Pricing power?"},
            {"id": "social", "question": "Social presence vs competitors?"},
            {"id": "churn-reasons", "question": "Top churn reasons?"},
            {"id": "feature-gaps", "question": "Feature gaps vs leaders?"},
            {"id": "support-quality", "question": "Support quality vs peers?"},
            {"id": "integrations", "question": "Integration ecosystem strength?"},
            {"id": "review-volume", "question": "Review volume trend?"},
        ],
        "resources": [
            {"id": "g2", "name": "G2 / Capterra", "type": "api", "status": "integrated", "notes": "Product reviews"},
            {"id": "trustpilot", "name": "Trustpilot (via Apify)", "type": "api", "status": "planned", "notes": "Use APIFY_API_TOKEN"},
        ],
    },
    "customers": {
        "audience": "customers",
        "description": "Compare platforms, employer brand, and ethical/sustainability signals",
        "use_cases": [
            {"id": "supply-chain", "question": "Supply chain ethics?"},
            {"id": "carbon", "question": "CO2 footprint?"},
            {"id": "employees", "question": "Employee treatment and compensation?"},
            {"id": "best-value", "question": "Best value for money?"},
            {"id": "easiest-use", "question": "Easiest to use?"},
            {"id": "best-support", "question": "Best support?"},
            {"id": "best-segment", "question": "Best for my segment (SMB/enterprise)?"},
        ],
        "resources": [
            {"id": "glassdoor", "name": "Glassdoor API", "type": "api", "status": "planned", "notes": "Employee reviews, compensation"},
            {"id": "kaggle_apify", "name": "Kaggle / Apify", "type": "api", "status": "integrated", "notes": "Reviews from Kaggle datasets + Apify (G2, Capterra, Trustpilot)"},
        ],
    },
}
