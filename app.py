"""
InsightEngine — Streamlit App
Market Intelligence Dashboard · CRM Software · HubSpot Focus

Run:
    streamlit run app.py
"""

import json
import os
import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="InsightEngine — CRM Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import pipeline components ────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from pipeline import (
    MOCK_SCORES, MOCK_INSIGHTS, DIMENSIONS, ALL_COMPANIES,
    FOCAL_COMPANY, VERTICAL, COMPETITORS,
    compute_kpis, build_client,
    compute_dimension_scores, generate_insights,
)

# ── Color palette ─────────────────────────────────────────────────────────────
COLORS = {
    "HubSpot":    "#FF7A59",
    "Salesforce": "#009EDB",
    "Pipedrive":  "#1EC25B",
    "Zoho CRM":   "#E42527",
}
FILL_COLORS = {
    "HubSpot":    "rgba(255,122,89,0.15)",
    "Salesforce": "rgba(0,158,219,0.15)",
    "Pipedrive":  "rgba(30,194,91,0.15)",
    "Zoho CRM":   "rgba(228,37,39,0.15)",
}

# ── Static trend data ─────────────────────────────────────────────────────────
QUARTERS = ["Q1 24","Q2 24","Q3 24","Q4 24","Q1 25","Q2 25","Q3 25","Q4 25","Q1 26"]

SENTIMENT_TREND = {
    "HubSpot":    [73, 74, 75, 74, 73, 72, 71, 70, 68],
    "Salesforce": [68, 70, 71, 72, 71, 70, 71, 70, 70],
    "Pipedrive":  [70, 71, 72, 73, 74, 74, 75, 74, 74],
    "Zoho CRM":   [65, 66, 67, 68, 68, 69, 70, 71, 71],
}
REVIEW_VOLUME = {
    "HubSpot":    [4.2, 4.8, 5.1, 5.5, 5.8, 6.0, 6.3, 6.4, 6.5],
    "Salesforce": [8.1, 8.3, 8.6, 8.9, 9.1, 9.2, 9.4, 9.5, 9.6],
    "Pipedrive":  [1.8, 2.0, 2.2, 2.5, 2.7, 3.0, 3.2, 3.4, 3.5],
    "Zoho CRM":   [2.1, 2.3, 2.5, 2.7, 2.9, 3.1, 3.3, 3.5, 3.6],
}
VALUE_TREND = {
    "HubSpot":    [68, 67, 66, 65, 64, 63, 62, 60, 58],
    "Salesforce": [45, 44, 43, 42, 41, 40, 40, 39, 38],
    "Pipedrive":  [76, 76, 77, 77, 77, 78, 78, 78, 78],
    "Zoho CRM":   [80, 80, 81, 81, 82, 82, 82, 82, 82],
}

COMPLAINT_THEMES = {
    "Pricing / Value Concerns":          34,
    "Limited Reporting Customisation":   22,
    "Support Response Time":             18,
    "Complex Setup / Onboarding":        15,
    "Feature Gaps vs Salesforce":        11,
}
PRAISE_THEMES = {
    "Ease of Use / Intuitive UI":        42,
    "All-in-One Platform":               28,
    "Strong Marketing Tools":            22,
    "Good Free Tier / Trial":            19,
    "Helpful Community & Docs":          15,
}

COMPETITOR_SIGNALS = [
    {"company": "Salesforce", "icon": "📰", "title": "Einstein AI Copilot now GA",
     "desc": "AI assistant across Sales Cloud. 30+ AI job postings in London & Dublin.", "time": "12 days ago"},
    {"company": "Salesforce", "icon": "💸", "title": "Enterprise tier +$25/seat",
     "desc": "Community posts mentioning price increase up 40% in 4 weeks.", "time": "28 days ago"},
    {"company": "Pipedrive",  "icon": "🚀", "title": "New advanced reporting module",
     "desc": "Addresses #1 product gap. 15 reporting job posts this quarter.", "time": "7 days ago"},
    {"company": "Pipedrive",  "icon": "📣", "title": "SEM spend +35% on 'HubSpot alternative'",
     "desc": "Explicitly targeting HubSpot's core SMB segment.", "time": "21 days ago"},
    {"company": "Zoho CRM",   "icon": "💰", "title": "Price-freeze commitment for 2026",
     "desc": "Directly exploits category-wide value narrative vs HubSpot & Salesforce.", "time": "14 days ago"},
    {"company": "Zoho CRM",   "icon": "🤝", "title": "GTM partnership with Freshdesk",
     "desc": "Support+CRM bundle — directly targets the support whitespace.", "time": "35 days ago"},
]

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Hide default Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1.5rem 2rem 2rem; max-width: 1280px; }

  /* KPI metric cards */
  [data-testid="metric-container"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
  [data-testid="metric-container"] label {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748B !important;
  }
  [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 800 !important; }
  [data-testid="stMetricDelta"] svg { display: none; }

  /* Insight cards */
  .ins-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    position: relative;
    overflow: hidden;
  }
  .ins-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
  }
  .ins-inv::before  { background: linear-gradient(90deg,#3B82F6,#818CF8); }
  .ins-comp::before { background: linear-gradient(90deg,#F59E0B,#FB923C); }
  .ins-num {
    position: absolute; top: 10px; right: 14px;
    font-size: 42px; font-weight: 900;
    color: #E2E8F0; line-height: 1; pointer-events: none;
  }
  .ins-title {
    font-size: 14px; font-weight: 700;
    color: #0F172A; margin-bottom: 8px; padding-right: 44px;
  }
  .ins-body { font-size: 13px; color: #334155; line-height: 1.65; margin-bottom: 10px; }
  .ins-action {
    font-size: 12px; color: #64748B;
    background: #F8FAFC; border-left: 3px solid #CBD5E1;
    border-radius: 0 6px 6px 0; padding: 7px 12px; margin-bottom: 10px;
  }
  .badge {
    display: inline-flex; align-items: center;
    padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 600; margin-right: 4px;
  }
  .b-inv  { background: #EFF6FF; color: #1D4ED8; }
  .b-comp { background: #FFFBEB; color: #B45309; }
  .b-cust { background: #F0FDF4; color: #15803D; }
  .b-high { background: #DCFCE7; color: #15803D; }
  .b-med  { background: #FEF9C3; color: #854D0E; }

  /* Signal cards */
  .sig-card {
    background: white; border: 1px solid #E2E8F0;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
    box-shadow: 0 1px 2px rgba(0,0,0,.05);
  }
  .sig-title { font-size: 13px; font-weight: 600; color: #0F172A; }
  .sig-desc  { font-size: 12px; color: #64748B; margin: 3px 0; }
  .sig-time  { font-size: 11px; color: #94A3B8; }

  /* Section header */
  .sec-hd { margin-bottom: 16px; }
  .sec-title { font-size: 15px; font-weight: 700; color: #0F172A; }
  .sec-sub   { font-size: 12px; color: #64748B; margin-top: 2px; }

  /* Callout boxes */
  .callout-blue   { background:#EFF6FF; border-left:4px solid #3B82F6; color:#1D4ED8; padding:10px 14px; border-radius:0 8px 8px 0; font-size:13px; margin-top:12px; }
  .callout-red    { background:#FEF2F2; border-left:4px solid #EF4444; color:#991B1B; padding:10px 14px; border-radius:0 8px 8px 0; font-size:13px; margin-top:12px; }
  .callout-amber  { background:#FFFBEB; border-left:4px solid #F59E0B; color:#92400E; padding:10px 14px; border-radius:0 8px 8px 0; font-size:13px; margin-top:12px; }
  .callout-green  { background:#F0FDF4; border-left:4px solid #22C55E; color:#166534; padding:10px 14px; border-radius:0 8px 8px 0; font-size:13px; margin-top:12px; }

  /* Tabs styling */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F1F5F9;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #E2E8F0;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-size: 13px;
    font-weight: 500;
    padding: 6px 16px;
    color: #64748B;
  }
  .stTabs [aria-selected="true"] {
    background: white !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
  }
</style>
""", unsafe_allow_html=True)

# ── Plotly default theme ──────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    font_family="Inter, system-ui, sans-serif",
    font_color="#334155",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(t=30, b=30, l=10, r=10),
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
)


# ── Helper: score pill color ──────────────────────────────────────────────────
def score_color(v):
    if v is None:
        return "#94A3B8"
    if v >= 75:
        return "#16A34A"
    if v >= 60:
        return "#CA8A04"
    return "#DC2626"


# ── Build charts ──────────────────────────────────────────────────────────────

def radar_chart(scores: dict) -> go.Figure:
    dim_labels = list(DIMENSIONS.values())
    fig = go.Figure()
    for company in ALL_COMPANIES:
        vals = [scores[company].get(d, 50) for d in DIMENSIONS]
        vals_closed = vals + [vals[0]]
        labels_closed = dim_labels + [dim_labels[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=labels_closed,
            fill="toself",
            name=company,
            line=dict(color=COLORS[company], width=2.5 if company == FOCAL_COMPANY else 1.5),
            fillcolor=FILL_COLORS[company],
            hovertemplate="%{theta}: <b>%{r}</b><extra>" + company + "</extra>",
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        polar=dict(
            radialaxis=dict(range=[0, 100], tickfont_size=10, gridcolor="#E2E8F0"),
            angularaxis=dict(gridcolor="#E2E8F0"),
            bgcolor="white",
        ),
        showlegend=True,
        height=380,
    )
    return fig


def dimension_bar_chart(scores: dict) -> go.Figure:
    dim_labels = list(DIMENSIONS.values())
    fig = go.Figure()
    for company in ALL_COMPANIES:
        vals = [scores[company].get(d, 50) for d in DIMENSIONS]
        fig.add_trace(go.Bar(
            name=company,
            x=dim_labels,
            y=vals,
            marker_color=COLORS[company],
            hovertemplate="<b>%{x}</b><br>" + company + ": %{y}<extra></extra>",
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        xaxis=dict(tickangle=-20, gridcolor="#F1F5F9"),
        yaxis=dict(range=[0, 100], gridcolor="#F1F5F9", title="Score (0–100)"),
        height=350,
    )
    return fig


def sentiment_line_chart() -> go.Figure:
    fig = go.Figure()
    for company in ALL_COMPANIES:
        fig.add_trace(go.Scatter(
            x=QUARTERS,
            y=SENTIMENT_TREND[company],
            name=company,
            mode="lines+markers",
            line=dict(color=COLORS[company], width=3 if company == FOCAL_COMPANY else 1.8),
            marker=dict(size=6 if company == FOCAL_COMPANY else 4),
            hovertemplate="%{x}: <b>%{y}</b><extra>" + company + "</extra>",
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(range=[60, 82], gridcolor="#F1F5F9", title="Sentiment Score (0–100)"),
        hovermode="x unified",
        height=320,
    )
    return fig


def volume_line_chart() -> go.Figure:
    fig = go.Figure()
    for company in ALL_COMPANIES:
        fig.add_trace(go.Scatter(
            x=QUARTERS,
            y=REVIEW_VOLUME[company],
            name=company,
            mode="lines+markers",
            line=dict(color=COLORS[company], width=3 if company == FOCAL_COMPANY else 1.8),
            fill="tozeroy" if company == FOCAL_COMPANY else "none",
            fillcolor=FILL_COLORS[company],
            marker=dict(size=6 if company == FOCAL_COMPANY else 4),
            hovertemplate="%{x}: <b>%{y}k reviews</b><extra>" + company + "</extra>",
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#F1F5F9", title="Reviews (thousands)"),
        hovermode="x unified",
        height=320,
    )
    return fig


def value_trend_chart() -> go.Figure:
    fig = go.Figure()
    for company in ALL_COMPANIES:
        fig.add_trace(go.Scatter(
            x=QUARTERS,
            y=VALUE_TREND[company],
            name=company,
            mode="lines+markers",
            line=dict(color=COLORS[company], width=3 if company == FOCAL_COMPANY else 1.8),
            marker=dict(size=6 if company == FOCAL_COMPANY else 4),
            hovertemplate="%{x}: <b>%{y}</b><extra>" + company + "</extra>",
        ))
    # Category average
    cat_avg = [
        round(sum(VALUE_TREND[c][i] for c in ALL_COMPANIES) / len(ALL_COMPANIES))
        for i in range(len(QUARTERS))
    ]
    fig.add_trace(go.Scatter(
        x=QUARTERS, y=cat_avg, name="Category Avg",
        mode="lines",
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        hovertemplate="%{x}: Cat. Avg <b>%{y}</b><extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(range=[25, 95], gridcolor="#F1F5F9", title="Value for Money Score"),
        hovermode="x unified",
        height=320,
    )
    return fig


def themes_bar(data: dict, color: str, title: str) -> go.Figure:
    labels = list(data.keys())
    values = list(data.values())
    colors = [f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0,2,4)) + (0.15 + 0.7 * v / max(values),)}"
              for v in values]
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(color=color, opacity=[0.4 + 0.6 * v / max(values) for v in values]),
        text=[f"{v}%" for v in values],
        textposition="outside",
        hovertemplate="<b>%{y}</b>: %{x}%<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(range=[0, max(values) * 1.25], gridcolor="#F1F5F9",
                   title="% of reviews mentioning theme"),
        yaxis=dict(autorange="reversed", gridcolor="white"),
        showlegend=False,
        height=260,
        title=dict(text=title, font_size=13, x=0),
    )
    return fig


def dimension_heatmap(scores: dict) -> go.Figure:
    dim_labels = list(DIMENSIONS.values())
    z = [[scores[c].get(d, 0) for c in ALL_COMPANIES] for d in DIMENSIONS]
    text = [[str(scores[c].get(d, "N/A")) for c in ALL_COMPANIES] for d in DIMENSIONS]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=ALL_COMPANIES,
        y=dim_labels,
        text=text,
        texttemplate="<b>%{text}</b>",
        colorscale=[
            [0.0,  "#FEE2E2"],
            [0.35, "#FEF9C3"],
            [0.65, "#DCFCE7"],
            [1.0,  "#14532D"],
        ],
        zmin=30, zmax=100,
        colorbar=dict(title="Score", thickness=12, len=0.8),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(side="top"),
        yaxis=dict(autorange="reversed"),
        height=320,
        margin=dict(t=60, b=10, l=10, r=60),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 InsightEngine")
    st.markdown(
        "<div style='font-size:12px;color:#64748B;margin-bottom:20px;'>"
        "Market Intelligence · CRM Software<br>HubSpot Focus · Phase 2 Prototype"
        "</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    mode = st.radio(
        "Analysis mode",
        ["Mock (pre-computed)", "Live (API)"],
        help="Mock uses pre-computed scores. Live calls an LLM API.",
    )

    api_key = ""
    provider = "mock"
    if mode == "Live (API)":
        provider = st.selectbox("Provider", ["Groq", "OpenAI"])
        api_key = st.text_input(
            f"{'GROQ' if provider == 'Groq' else 'OpenAI'} API Key",
            type="password",
            placeholder="gsk_..." if provider == "Groq" else "sk-...",
        )

    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

    st.divider()
    st.markdown("**Data sources**")
    st.markdown(
        "<div style='font-size:12px;color:#64748B;'>"
        "G2 · Capterra · Trustpilot<br>"
        "2,847 reviews · Jan 2024–Mar 2026<br>"
        "826 HubSpot · 4 companies · 6 dimensions"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("**Models**")
    st.markdown(
        "<div style='font-size:12px;color:#64748B;'>"
        "Aspect extraction: llama-3.1-8b-instant<br>"
        "Synthesis: llama-3.3-70b-versatile<br>"
        "Cost: ~$0.10 / company / run"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Load / run analysis ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_mock_data():
    reviews_path = Path("data/sample_reviews.json")
    reviews = json.loads(reviews_path.read_text()) if reviews_path.exists() else []
    kpis = compute_kpis(MOCK_SCORES, reviews)
    return MOCK_SCORES, MOCK_INSIGHTS, kpis


if "scores" not in st.session_state:
    scores, insights, kpis = get_mock_data()
    st.session_state.scores   = scores
    st.session_state.insights = insights
    st.session_state.kpis     = kpis
    st.session_state.provider = "Mock"

if run_btn:
    if mode == "Mock (pre-computed)":
        with st.spinner("Loading pre-computed scores..."):
            scores, insights, kpis = get_mock_data()
        st.session_state.scores   = scores
        st.session_state.insights = insights
        st.session_state.kpis     = kpis
        st.session_state.provider = "Mock"
        st.success("Loaded pre-computed scores.")
    else:
        if not api_key:
            st.error(f"Please enter your {'Groq' if provider == 'Groq' else 'OpenAI'} API key.")
        else:
            env_var = "GROQ_API_KEY" if provider == "Groq" else "OPENAI_API_KEY"
            os.environ[env_var] = api_key
            with st.spinner("Running pipeline (this takes ~30s for 30 reviews)..."):
                try:
                    client, fast_model, smart_model, detected = build_client()
                    reviews_path = Path("data/sample_reviews.json")
                    reviews = json.loads(reviews_path.read_text())
                    new_scores = compute_dimension_scores(reviews, client, fast_model)
                    new_insights = generate_insights(new_scores, client, smart_model)
                    new_kpis = compute_kpis(new_scores, reviews)
                    st.session_state.scores   = new_scores
                    st.session_state.insights = new_insights
                    st.session_state.kpis     = new_kpis
                    st.session_state.provider = detected
                    st.success(f"Analysis complete via {detected}.")
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

scores   = st.session_state.scores
insights = st.session_state.insights
kpis     = st.session_state.kpis


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<div style='display:flex;align-items:center;justify-content:space-between;"
    "margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #E2E8F0;'>"
    "<div>"
    "<div style='font-size:20px;font-weight:800;letter-spacing:-0.5px;color:#0F172A;'>"
    "CRM Software — Competitive Intelligence Report</div>"
    "<div style='font-size:13px;color:#64748B;margin-top:3px;'>"
    "Aspect-based sentiment · 2,847 reviews · HubSpot vs Salesforce, Pipedrive, Zoho CRM</div>"
    "</div>"
    "<div style='display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;'>"
    "<span style='background:#EFF6FF;color:#2563EB;padding:4px 10px;border-radius:20px;font-size:11.5px;font-weight:500;'>📊 G2 · Capterra · Trustpilot</span>"
    "<span style='background:#FFF7ED;color:#C2410C;padding:4px 10px;border-radius:20px;font-size:11.5px;font-weight:500;'>🤖 GPT-4o Analysis</span>"
    "<span style='background:#F0FDF4;color:#15803D;padding:4px 10px;border-radius:20px;font-size:11.5px;font-weight:500;'>✓ 4 Companies · 6 Dimensions</span>"
    "</div></div>",
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Overall Sentiment Score",  "70 / 100",    "-3.2 pts vs 6 months ago")
k2.metric("Value Rank (Category)",    "#3 of 4",     "Behind Zoho & Pipedrive")
k3.metric("Share of Voice",           "29%",         "+2.1 pts · 826 reviews")
k4.metric("Price Index vs Category",  "140%",        "Category average = 100%")

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠 Strategic Insights",
    "📐 Competitive Scoring",
    "📈 Trends",
    "🗣 Voice of Customer",
    "🔍 Whitespace & Signals",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — STRATEGIC INSIGHTS
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    audience_map = {
        "Investors": ("inv", "b-inv"),
        "Companies": ("comp", "b-comp"),
        "Customers": ("cust", "b-cust"),
    }
    conf_map = {"High": "b-high", "Medium": "b-med", "Low": "b-low"}

    filter_col, _ = st.columns([2, 5])
    audience_filter = filter_col.selectbox(
        "Filter by audience",
        ["All", "Investors", "Companies", "Customers"],
        label_visibility="collapsed",
    )

    filtered = [
        ins for ins in insights
        if audience_filter == "All" or ins.get("audience") == audience_filter
    ]

    if not filtered:
        st.info("No insights for the selected audience filter.")
    else:
        cols = st.columns(2) if len(filtered) > 1 else [st.columns(1)[0]]
        for i, ins in enumerate(filtered):
            col = cols[i % 2] if len(filtered) > 1 else cols[0]
            aud = ins.get("audience", "Companies")
            cls, badge_cls = audience_map.get(aud, ("comp", "b-comp"))
            conf = ins.get("confidence", "Medium")
            conf_cls = conf_map.get(conf, "b-med")
            num = i + 1

            with col:
                st.markdown(f"""
                <div class="ins-card ins-{cls}">
                  <div class="ins-num">{num:02d}</div>
                  <div class="ins-title">{ins.get("title","")}</div>
                  <div class="ins-body">{ins.get("body","")}</div>
                  <div class="ins-action"><strong>Action:</strong> {ins.get("action","")}</div>
                  <div>
                    <span class="badge {badge_cls}">{aud}</span>
                    <span class="badge {conf_cls}">{conf} Confidence</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPETITIVE SCORING
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown(
            "<div class='sec-hd'><div class='sec-title'>Dimension Radar</div>"
            "<div class='sec-sub'>All companies across all 6 dimensions</div></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(radar_chart(scores), use_container_width=True)

    with c_right:
        st.markdown(
            "<div class='sec-hd'><div class='sec-title'>Grouped Bar Chart</div>"
            "<div class='sec-sub'>Score per dimension per company</div></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(dimension_bar_chart(scores), use_container_width=True)

    st.markdown(
        "<div class='sec-hd' style='margin-top:8px;'><div class='sec-title'>Score Heatmap</div>"
        "<div class='sec-sub'>Red = weak · Yellow = average · Green = strong</div></div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(dimension_heatmap(scores), use_container_width=True)

    # Score table
    st.markdown(
        "<div class='sec-hd' style='margin-top:8px;'><div class='sec-title'>Full Score Table</div></div>",
        unsafe_allow_html=True,
    )
    table_data = {
        "Dimension": list(DIMENSIONS.values()),
    }
    for c in ALL_COMPANIES:
        table_data[c] = [scores[c].get(d) for d in DIMENSIONS]
    cat_avg = [
        round(sum(scores[c].get(d, 0) for c in ALL_COMPANIES) / len(ALL_COMPANIES))
        for d in DIMENSIONS
    ]
    table_data["Category Avg"] = cat_avg
    df = pd.DataFrame(table_data)

    def color_score(val):
        if not isinstance(val, (int, float)):
            return ""
        if val >= 75:
            return "background-color: #DCFCE7; color: #15803D; font-weight: 700"
        if val >= 60:
            return "background-color: #FEF9C3; color: #854D0E; font-weight: 700"
        return "background-color: #FEE2E2; color: #991B1B; font-weight: 700"

    styled = df.style.applymap(color_score, subset=ALL_COMPANIES + ["Category Avg"])
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — TRENDS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    t_left, t_right = st.columns(2)

    with t_left:
        st.markdown(
            "<div class='sec-hd'><div class='sec-title'>Overall Sentiment Score Over Time</div>"
            "<div class='sec-sub'>Q1 2024 – Q1 2026 · 9 quarters</div></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(sentiment_line_chart(), use_container_width=True)
        st.markdown(
            "<div class='callout-red'>⚠ HubSpot is the only company with a declining sentiment trajectory — down 5 points over 18 months.</div>",
            unsafe_allow_html=True,
        )

    with t_right:
        st.markdown(
            "<div class='sec-hd'><div class='sec-title'>Review Volume Growth</div>"
            "<div class='sec-sub'>Total reviews published per quarter (thousands)</div></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(volume_line_chart(), use_container_width=True)
        st.markdown(
            "<div class='callout-amber'>📣 Pipedrive review volume +23% YoY — 2× HubSpot's growth rate (+11%). Classic word-of-mouth SMB traction signal.</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div class='sec-hd' style='margin-top:16px;'><div class='sec-title'>Value for Money Trend — Category-Wide</div>"
        "<div class='sec-sub'>Structural decline across all players · post-2022 SaaS repricing signal</div></div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(value_trend_chart(), use_container_width=True)
    st.markdown(
        "<div class='callout-blue'><strong>Category finding:</strong> Average value-for-money fell 72 → 64 across all four players over 18 months. "
        "This is a structural market shift that historically precedes entry by a price-transparent, usage-based challenger (18–36 month window).</div>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — VOICE OF CUSTOMER
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    v_left, v_right = st.columns(2)

    with v_left:
        st.plotly_chart(
            themes_bar(COMPLAINT_THEMES, "#EF4444", "Top Complaint Themes — % of Negative Reviews"),
            use_container_width=True,
        )
        st.markdown(
            "<div class='callout-red'>⚠ Pricing complaints grew 22% → 34% over 6 quarters — the fastest-growing negative signal in HubSpot's review corpus.</div>",
            unsafe_allow_html=True,
        )

    with v_right:
        st.plotly_chart(
            themes_bar(PRAISE_THEMES, "#22C55E", "Top Praise Themes — % of Positive Reviews"),
            use_container_width=True,
        )
        st.markdown(
            "<div class='callout-green'>✓ Ease of use is HubSpot's durable competitive advantage — the #1 praise theme consistently for 8 consecutive quarters.</div>",
            unsafe_allow_html=True,
        )

    # Praise vs complaint delta
    st.markdown(
        "<div class='sec-hd' style='margin-top:16px;'><div class='sec-title'>Praise vs Complaint Balance</div>"
        "<div class='sec-sub'>Head-to-head volume comparison per theme type</div></div>",
        unsafe_allow_html=True,
    )
    combined_df = pd.DataFrame({
        "Theme":     list(PRAISE_THEMES.keys()) + list(COMPLAINT_THEMES.keys()),
        "Pct":       list(PRAISE_THEMES.values()) + list(COMPLAINT_THEMES.values()),
        "Type":      ["Praise"] * len(PRAISE_THEMES) + ["Complaint"] * len(COMPLAINT_THEMES),
    })
    fig_combined = px.bar(
        combined_df, x="Pct", y="Theme", color="Type", orientation="h",
        color_discrete_map={"Praise": "#22C55E", "Complaint": "#EF4444"},
        barmode="group",
        text="Pct",
        labels={"Pct": "% of reviews mentioning theme"},
        height=360,
    )
    fig_combined.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_combined.update_layout(**PLOTLY_LAYOUT, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_combined, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — WHITESPACE & COMPETITOR SIGNALS
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown(
        "<div class='sec-hd'><div class='sec-title'>Whitespace Analysis</div>"
        "<div class='sec-sub'>Dimensions where no player has established a clear advantage (max score &lt;75)</div></div>",
        unsafe_allow_html=True,
    )

    # Whitespace chart — max score per dimension
    dim_labels = list(DIMENSIONS.values())
    max_scores = [max(scores[c].get(d, 0) for c in ALL_COMPANIES) for d in DIMENSIONS]
    best_companies = [
        max(ALL_COMPANIES, key=lambda c: scores[c].get(d, 0)) for d in DIMENSIONS
    ]
    bar_colors = ["#EF4444" if m < 75 else "#22C55E" for m in max_scores]

    fig_ws = go.Figure(go.Bar(
        x=dim_labels,
        y=max_scores,
        marker_color=bar_colors,
        text=[f"{m} ({best_companies[i]})" for i, m in enumerate(max_scores)],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Best score: %{y}<extra></extra>",
    ))
    fig_ws.add_hline(
        y=75, line_dash="dash", line_color="#94A3B8", line_width=1.5,
        annotation_text="Whitespace threshold (75)", annotation_position="bottom right",
    )
    fig_ws.update_layout(
        **PLOTLY_LAYOUT,
        yaxis=dict(range=[0, 115], gridcolor="#F1F5F9", title="Best score across all companies"),
        xaxis=dict(gridcolor="white"),
        showlegend=False,
        height=320,
    )
    st.plotly_chart(fig_ws, use_container_width=True)
    st.markdown(
        "<div class='callout-blue'><strong>Key finding:</strong> Customer support is the only dimension where no single player has established a clear advantage (max 75/100). "
        "A challenger achieving ≥85 on support while remaining competitive elsewhere captures the clearest available moat in this market.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sec-hd'><div class='sec-title'>📡 Competitor Activity Monitor</div>"
        "<div class='sec-sub'>Recent signals from news, job postings, and pricing pages · last 90 days</div></div>",
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)
    col_map = {"Salesforce": s1, "Pipedrive": s2, "Zoho CRM": s3}

    for company in COMPETITORS:
        col = col_map[company]
        company_signals = [s for s in COMPETITOR_SIGNALS if s["company"] == company]
        with col:
            st.markdown(
                f"<div style='font-size:12px;font-weight:700;color:{COLORS[company]};"
                f"margin-bottom:8px;'>● {company}</div>",
                unsafe_allow_html=True,
            )
            for sig in company_signals:
                st.markdown(f"""
                <div class="sig-card">
                  <div style="font-size:18px;margin-bottom:4px;">{sig["icon"]}</div>
                  <div class="sig-title">{sig["title"]}</div>
                  <div class="sig-desc">{sig["desc"]}</div>
                  <div class="sig-time">{sig["time"]}</div>
                </div>
                """, unsafe_allow_html=True)

    # Evaluation rubric
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sec-hd'><div class='sec-title'>📋 Evaluation Rubric</div>"
        "<div class='sec-sub'>Used in Phase 3 user testing to score each AI insight</div></div>",
        unsafe_allow_html=True,
    )
    r1, r2, r3 = st.columns(3)
    with r1:
        st.success("**✅ USEFUL — Passes**\n\nNon-obvious. Ties scores to strategic implications. Contains specific evidence. Points to a trajectory or competitive dynamic.")
    with r2:
        st.warning("**⚠️ OBVIOUS — Fails**\n\nRestates what is already known. No new information. Does not connect scores to implications.")
    with r3:
        st.error("**❌ WRONG — Fails (trust-breaking)**\n\nContradicted by data in the report. Overconfident claim without supporting evidence. Worst failure mode.")
