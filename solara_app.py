"""
InsightEngine — Solara App  (Dark Fintech Edition)
Run:  python -m solara run solara_app.py
"""

import json
import os
import sys
import threading
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import solara
import solara.lab

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import (
    ALL_COMPANIES, COMPETITORS, DIMENSIONS, FOCAL_COMPANY,
    MOCK_INSIGHTS, MOCK_SCORES,
    build_client, compute_dimension_scores, generate_insights,
)

# ── Reactive state ────────────────────────────────────────────────────────────
scores_rv   = solara.reactive(dict(MOCK_SCORES))
insights_rv = solara.reactive(list(MOCK_INSIGHTS))

# ── Dark fintech palette ──────────────────────────────────────────────────────
BG        = "#08101E"
SURFACE   = "#0D1726"
SURFACE2  = "#112038"
BORDER    = "#1A2E4A"
BORDER2   = "#243D5E"
TEXT      = "#E2EAF8"
TEXT2     = "#8BA3C7"
TEXT3     = "#4E6A8C"
ACCENT    = "#4F8EF7"
GREEN     = "#00D68F"
AMBER     = "#FFB020"
RED       = "#FF4D6A"

COLORS = {
    "HubSpot":    "#FF7A59",
    "Salesforce": "#00BEFF",
    "Pipedrive":  "#00D68F",
    "Zoho CRM":   "#FF4D6A",
}
FILL = {
    "HubSpot":    "rgba(255,122,89,0.12)",
    "Salesforce": "rgba(0,190,255,0.12)",
    "Pipedrive":  "rgba(0,214,143,0.12)",
    "Zoho CRM":   "rgba(255,77,106,0.12)",
}

# ── Static data ───────────────────────────────────────────────────────────────
QUARTERS = ["Q1 24","Q2 24","Q3 24","Q4 24","Q1 25","Q2 25","Q3 25","Q4 25","Q1 26"]
SENTIMENT = {
    "HubSpot":    [73,74,75,74,73,72,71,70,68],
    "Salesforce": [68,70,71,72,71,70,71,70,70],
    "Pipedrive":  [70,71,72,73,74,74,75,74,74],
    "Zoho CRM":   [65,66,67,68,68,69,70,71,71],
}
VOLUME = {
    "HubSpot":    [4.2,4.8,5.1,5.5,5.8,6.0,6.3,6.4,6.5],
    "Salesforce": [8.1,8.3,8.6,8.9,9.1,9.2,9.4,9.5,9.6],
    "Pipedrive":  [1.8,2.0,2.2,2.5,2.7,3.0,3.2,3.4,3.5],
    "Zoho CRM":   [2.1,2.3,2.5,2.7,2.9,3.1,3.3,3.5,3.6],
}
VALUE_TREND = {
    "HubSpot":    [68,67,66,65,64,63,62,60,58],
    "Salesforce": [45,44,43,42,41,40,40,39,38],
    "Pipedrive":  [76,76,77,77,77,78,78,78,78],
    "Zoho CRM":   [80,80,81,81,82,82,82,82,82],
}
COMPLAINTS = {
    "Pricing / Value Concerns":        34,
    "Limited Reporting Customisation": 22,
    "Support Response Time":           18,
    "Complex Setup / Onboarding":      15,
    "Feature Gaps vs Salesforce":      11,
}
PRAISE = {
    "Ease of Use / Intuitive UI":  42,
    "All-in-One Platform":         28,
    "Strong Marketing Tools":      22,
    "Good Free Tier / Trial":      19,
    "Helpful Community & Docs":    15,
}
SIGNALS = [
    {"company":"Salesforce","icon":"📰","title":"Einstein AI Copilot now GA",
     "desc":"30+ AI job postings in London & Dublin.","time":"12 days ago"},
    {"company":"Salesforce","icon":"💸","title":"Enterprise tier +$25/seat",
     "desc":"Community mentions of price increase up 40% in 4 weeks.","time":"28 days ago"},
    {"company":"Pipedrive", "icon":"🚀","title":"New advanced reporting module",
     "desc":"Directly addresses #1 product gap. 15 reporting job posts.","time":"7 days ago"},
    {"company":"Pipedrive", "icon":"📣","title":"SEM +35% on 'HubSpot alternative'",
     "desc":"Explicitly targeting HubSpot's core SMB segment.","time":"21 days ago"},
    {"company":"Zoho CRM",  "icon":"💰","title":"Price-freeze commitment 2026",
     "desc":"Direct shot at HubSpot & Salesforce pricing narrative.","time":"14 days ago"},
    {"company":"Zoho CRM",  "icon":"🤝","title":"GTM partnership with Freshdesk",
     "desc":"Support+CRM bundle — targets the support whitespace.","time":"35 days ago"},
]

# ── Plotly dark base ──────────────────────────────────────────────────────────
BASE = dict(
    font_family="Inter, system-ui, sans-serif",
    font_size=13,
    font_color=TEXT2,
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    legend=dict(
        orientation="h", yanchor="bottom", y=-0.26, xanchor="center", x=0.5,
        bgcolor="rgba(0,0,0,0)", font_color=TEXT2, font_size=12,
    ),
)
DM = dict(t=32, b=80, l=12, r=12)   # default margin — generous bottom for legend

GRID = dict(gridcolor=BORDER, zerolinecolor=BORDER)

# ── Chart builders ────────────────────────────────────────────────────────────

def make_radar(sc):
    labels = list(DIMENSIONS.values())
    fig = go.Figure()
    for c in ALL_COMPANIES:
        v = [sc[c].get(d, 50) for d in DIMENSIONS]
        fig.add_trace(go.Scatterpolar(
            r=v+[v[0]], theta=labels+[labels[0]], fill="toself", name=c,
            line=dict(color=COLORS[c], width=2.5 if c==FOCAL_COMPANY else 1.5),
            fillcolor=FILL[c],
        ))
    fig.update_layout(**BASE, height=400, margin=DM,
        polar=dict(
            bgcolor=SURFACE,
            radialaxis=dict(range=[0,100], tickfont_size=11,
                            gridcolor=BORDER, tickfont_color=TEXT3),
            angularaxis=dict(gridcolor=BORDER, tickfont_color=TEXT2, tickfont_size=13),
        ),
    )
    return fig


def make_bar(sc):
    labels = list(DIMENSIONS.values())
    fig = go.Figure()
    for c in ALL_COMPANIES:
        fig.add_trace(go.Bar(
            name=c, x=labels,
            y=[sc[c].get(d,50) for d in DIMENSIONS],
            marker=dict(color=COLORS[c], opacity=0.85),
        ))
    fig.update_layout(**BASE, barmode="group", height=360,
        margin=dict(t=32, b=100, l=12, r=12),
        xaxis=dict(tickangle=-30, tickfont_size=12, **GRID),
        yaxis=dict(range=[0,105], title="Score", **GRID),
        bargap=0.2, bargroupgap=0.08,
    )
    return fig


def make_heatmap(sc):
    labels = list(DIMENSIONS.values())
    z    = [[sc[c].get(d,0) for c in ALL_COMPANIES] for d in DIMENSIONS]
    text = [[str(sc[c].get(d,"")) for c in ALL_COMPANIES] for d in DIMENSIONS]
    fig = go.Figure(go.Heatmap(
        z=z, x=ALL_COMPANIES, y=labels,
        text=text, texttemplate="<b>%{text}</b>", textfont=dict(color=TEXT),
        colorscale=[[0,"#3D0E1A"],[0.35,"#2D2500"],[0.65,"#0A2E1E"],[1,"#00D68F"]],
        zmin=30, zmax=100,
        colorbar=dict(title="Score", thickness=10, len=0.8,
                      tickfont_color=TEXT2, title_font_color=TEXT2),
    ))
    fig.update_layout(**BASE, height=320,
        xaxis=dict(side="top", tickfont_color=TEXT2, tickfont_size=13),
        yaxis=dict(autorange="reversed", tickfont_color=TEXT2, tickfont_size=13),
        margin=dict(t=60, b=16, l=16, r=60),
    )
    return fig


def make_line(data_dict, yrange=None, ytitle=""):
    fig = go.Figure()
    for c in ALL_COMPANIES:
        fig.add_trace(go.Scatter(
            x=QUARTERS, y=data_dict[c], name=c,
            mode="lines+markers",
            line=dict(color=COLORS[c], width=3 if c==FOCAL_COMPANY else 1.8),
            marker=dict(size=7 if c==FOCAL_COMPANY else 4, color=COLORS[c],
                        line=dict(width=1.5, color=SURFACE)),
        ))
    layout = dict(**BASE, height=320, hovermode="x unified", margin=DM,
                  xaxis=dict(tickfont_size=12, **GRID),
                  yaxis=dict(title=ytitle, tickfont_size=12, **GRID))
    if yrange:
        layout["yaxis"]["range"] = yrange
    fig.update_layout(**layout)
    return fig


def make_value_trend():
    fig = make_line(VALUE_TREND, yrange=[25,95], ytitle="Value for Money")
    cat_avg = [round(sum(VALUE_TREND[c][i] for c in ALL_COMPANIES)/len(ALL_COMPANIES))
               for i in range(len(QUARTERS))]
    fig.add_trace(go.Scatter(
        x=QUARTERS, y=cat_avg, name="Category Avg",
        mode="lines", line=dict(color=TEXT3, width=1.5, dash="dash"),
    ))
    return fig


def make_themes(data, color, title):
    labels, vals = list(data.keys()), list(data.values())
    fig = go.Figure(go.Bar(
        x=vals, y=labels, orientation="h",
        marker=dict(color=color,
                    opacity=[0.35 + 0.65*v/max(vals) for v in vals],
                    line=dict(width=0)),
        text=[f"{v}%" for v in vals], textposition="outside",
        textfont=dict(color=TEXT2),
    ))
    fig.update_layout(**BASE, height=290, showlegend=False,
        title=dict(text=title, font_size=14, font_color=TEXT, x=0),
        xaxis=dict(range=[0,max(vals)*1.35], tickfont_size=12, **GRID),
        yaxis=dict(autorange="reversed", tickfont_color=TEXT2, tickfont_size=12),
        margin=dict(t=40, b=16, l=12, r=60),
    )
    return fig


def make_whitespace(sc):
    labels = list(DIMENSIONS.values())
    maxes = [max(sc[c].get(d,0) for c in ALL_COMPANIES) for d in DIMENSIONS]
    best  = [max(ALL_COMPANIES, key=lambda c: sc[c].get(d,0)) for d in DIMENSIONS]
    fig = go.Figure(go.Bar(
        x=labels, y=maxes,
        marker=dict(
            color=[RED if m<75 else GREEN for m in maxes],
            opacity=0.85, line=dict(width=0),
        ),
        text=[f"<b>{m}</b>  {b}" for m,b in zip(maxes,best)],
        textposition="outside",
        textfont=dict(color=TEXT2, size=12),
    ))
    fig.add_hline(y=75, line_dash="dash", line_color=TEXT3, line_width=1.5,
                  annotation_text="Threshold (75)", annotation_font_color=TEXT3,
                  annotation_position="bottom right")
    fig.update_layout(**BASE, height=380, showlegend=False,
        margin=dict(t=32, b=40, l=12, r=12),
        yaxis=dict(range=[0,130], title="Best score", **GRID),
        xaxis=dict(tickfont_size=12, tickangle=0, **GRID),
    )
    return fig


# ── Style helpers ─────────────────────────────────────────────────────────────
CARD = {
    "background": SURFACE,
    "border": f"1px solid {BORDER}",
    "borderRadius": "12px",
    "padding": "18px 20px",
    "boxShadow": "0 4px 24px rgba(0,0,0,.35)",
}
CARD2 = {**CARD, "background": SURFACE2}

def callout(text, kind="blue"):
    cfg = {
        "blue":  (f"rgba(79,142,247,.10)",  ACCENT, "#93C5FD"),
        "red":   (f"rgba(255,77,106,.10)",  RED,    "#FCA5A5"),
        "amber": (f"rgba(255,176,32,.10)",  AMBER,  "#FCD34D"),
        "green": (f"rgba(0,214,143,.10)",   GREEN,  "#6EE7B7"),
    }
    bg, border, fg = cfg.get(kind, cfg["blue"])
    solara.Markdown(text, style={
        "background": bg,
        "borderLeft": f"3px solid {border}",
        "color": fg,
        "padding": "10px 14px",
        "borderRadius": "0 8px 8px 0",
        "fontSize": "13px",
        "marginTop": "10px",
        "fontFamily": "Inter, system-ui, sans-serif",
    })

def sh(title, subtitle=""):
    """Section header."""
    solara.Text(title, style={
        "fontFamily": "Inter, system-ui, sans-serif",
        "fontWeight": "700", "fontSize": "14px", "color": TEXT,
        "marginBottom": "2px",
    })
    if subtitle:
        solara.Text(subtitle, style={
            "fontFamily": "Inter, system-ui, sans-serif",
            "fontSize": "12px", "color": TEXT3, "marginBottom": "12px",
        })

# ── KPI row ───────────────────────────────────────────────────────────────────
@solara.component
def KPIRow():
    kpis = [
        ("Overall Sentiment",  "70 / 100", "▼ 3.2 pts vs 6 months ago",   False, COLORS["HubSpot"]),
        ("Value Rank",         "#3 of 4",  "Behind Zoho & Pipedrive",      False, TEXT),
        ("Share of Voice",     "29%",      "▲ 2.1 pts · 826 reviews",      True,  TEXT),
        ("Price Index",        "140%",     "vs category average 100%",     False, TEXT),
    ]
    F = "Inter, system-ui, sans-serif"
    with solara.ColumnsResponsive(6, large=3):
        for label, value, delta, pos, val_color in kpis:
            border_col = GREEN if pos else RED
            delta_bg = "rgba(0,214,143,.12)" if pos else "rgba(255,77,106,.12)"
            with solara.Card(style={**CARD, "borderTop": f"3px solid {border_col}",
                                    "display":"flex","flexDirection":"column"}):
                solara.Text(label, style={"fontFamily":F,"fontSize":"11px","fontWeight":"600",
                    "textTransform":"uppercase","letterSpacing":"0.8px","color":TEXT3,
                    "display":"block","marginBottom":"6px"})
                solara.Text(value, style={"fontFamily":F,"fontSize":"30px","fontWeight":"800",
                    "color":val_color,"letterSpacing":"-0.5px","lineHeight":"1.15",
                    "display":"block","margin":"4px 0 8px"})
                solara.Text(delta, style={"fontFamily":F,"fontSize":"12px","fontWeight":"500",
                    "color":GREEN if pos else RED,
                    "background":delta_bg,
                    "padding":"3px 10px","borderRadius":"5px","display":"inline-block"})


# ── Insight card ──────────────────────────────────────────────────────────────
@solara.component
def InsightCard(ins, num):
    aud  = ins.get("audience","Companies")
    conf = ins.get("confidence","Medium")
    accent = {"Investors":ACCENT,"Companies":AMBER,"Customers":GREEN}.get(aud,TEXT3)
    abg    = {"Investors":"rgba(79,142,247,.15)","Companies":"rgba(255,176,32,.15)",
              "Customers":"rgba(0,214,143,.15)"}.get(aud,"rgba(255,255,255,.05)")
    afg    = {"Investors":"#93C5FD","Companies":"#FCD34D","Customers":"#6EE7B7"}.get(aud,TEXT2)
    cbg    = {"High":"rgba(0,214,143,.15)","Medium":"rgba(255,176,32,.15)",
              "Low":"rgba(255,77,106,.15)"}.get(conf,"rgba(255,255,255,.05)")
    cfg    = {"High":"#6EE7B7","Medium":"#FCD34D","Low":"#FCA5A5"}.get(conf,TEXT2)
    F = "Inter, system-ui, sans-serif"

    with solara.Card(style={**CARD, "borderTop":f"2px solid {accent}", "height":"100%",
                             "position":"relative", "overflow":"hidden"}):
        solara.Text(f"{num:02d}", style={"fontFamily":F,"fontSize":"56px","fontWeight":"900",
            "color":f"rgba(255,255,255,.04)","lineHeight":"1","position":"absolute",
            "top":"8px","right":"14px","pointerEvents":"none"})
        solara.Text(ins.get("title",""), style={"fontFamily":F,"fontSize":"14px",
            "fontWeight":"700","color":TEXT,"marginBottom":"8px","paddingRight":"48px"})
        solara.Text(ins.get("body",""), style={"fontFamily":F,"fontSize":"13px",
            "color":TEXT2,"lineHeight":"1.65","marginBottom":"12px"})
        with solara.Card(style={"background":f"rgba(255,255,255,.04)",
                                 "border":f"1px solid {BORDER}","borderRadius":"8px",
                                 "padding":"8px 12px","marginBottom":"12px"}):
            solara.Text(f"→  {ins.get('action','')}", style={"fontFamily":F,"fontSize":"12px","color":TEXT3})
        with solara.Row(gap="6px", style={"flexWrap":"wrap"}):
            for txt, bg, fg in [(aud,abg,afg),(f"{conf} Confidence",cbg,cfg)]:
                solara.Text(txt, style={"fontFamily":F,"background":bg,"color":fg,
                    "padding":"2px 9px","borderRadius":"4px","fontSize":"11px","fontWeight":"600"})


# ── Insights tab — audience sub-tabs ──────────────────────────────────────────
@solara.component
def InsightsTab():
    ins_list = insights_rv.value

    with solara.lab.Tabs(background_color=SURFACE):
        for audience, accent in [("Companies", AMBER), ("Investors", ACCENT), ("Customers", GREEN)]:
            filtered = [i for i in ins_list if i.get("audience") == audience]
            with solara.lab.Tab(audience):
                solara.Text("", style={"marginTop":"14px"})
                if not filtered:
                    solara.Text(f"No {audience} insights in current analysis.",
                                style={"color":TEXT3,"fontFamily":"Inter, system-ui, sans-serif"})
                    continue
                for row_start in range(0, len(filtered), 2):
                    pair = filtered[row_start:row_start+2]
                    with solara.ColumnsResponsive(12, large=6):
                        for i, item in enumerate(pair):
                            InsightCard(item, row_start+i+1)
                    solara.Text("", style={"marginBottom":"10px"})


# ── Competitive tab ───────────────────────────────────────────────────────────
@solara.component
def CompetitiveTab():
    sc = scores_rv.value
    with solara.ColumnsResponsive(12, large=6):
        with solara.Card(style=CARD):
            sh("Dimension Radar","All companies · 6 dimensions")
            solara.FigurePlotly(make_radar(sc))
        with solara.Card(style=CARD):
            sh("Grouped Bar","Score per dimension per company")
            solara.FigurePlotly(make_bar(sc))
    solara.Text("", style={"marginTop":"10px"})
    with solara.Card(style=CARD):
        sh("Score Heatmap","Dark red = weak · Yellow = average · Green = strong")
        solara.FigurePlotly(make_heatmap(sc))
    solara.Text("", style={"marginTop":"10px"})
    with solara.Card(style=CARD):
        sh("Full Score Table")
        df = pd.DataFrame({
            "Dimension": list(DIMENSIONS.values()),
            **{c:[sc[c].get(d) for d in DIMENSIONS] for c in ALL_COMPANIES},
            "Cat. Avg":[round(sum(sc[c].get(d,0) for c in ALL_COMPANIES)/len(ALL_COMPANIES))
                        for d in DIMENSIONS],
        })
        def colour(val):
            if not isinstance(val,(int,float)): return ""
            if val>=75: return f"background:{GREEN}22;color:{GREEN};font-weight:700"
            if val>=60: return f"background:{AMBER}22;color:{AMBER};font-weight:700"
            return f"background:{RED}22;color:{RED};font-weight:700"
        solara.display(df.style.map(colour, subset=ALL_COMPANIES+["Cat. Avg"]))


# ── Trends tab ────────────────────────────────────────────────────────────────
@solara.component
def TrendsTab():
    with solara.ColumnsResponsive(12, large=6):
        with solara.Card(style=CARD):
            sh("Sentiment Score Over Time","Q1 2024 – Q1 2026")
            solara.FigurePlotly(make_line(SENTIMENT, yrange=[60,82], ytitle="Score"))
            callout("⚠ HubSpot is the only company with a declining trajectory — down 5 points over 18 months.", "red")
        with solara.Card(style=CARD):
            sh("Review Volume Growth","Total reviews per quarter (thousands)")
            solara.FigurePlotly(make_line(VOLUME, ytitle="Reviews (k)"))
            callout("Pipedrive +23% YoY — 2× HubSpot's growth rate. Classic word-of-mouth SMB signal.", "green")
    solara.Text("", style={"marginTop":"10px"})
    with solara.Card(style=CARD):
        sh("Value for Money — Category-Wide Decline","Structural signal · post-2022 SaaS repricing")
        solara.FigurePlotly(make_value_trend())
        callout("Average value-for-money fell 72 → 64 across all four players over 18 months — structural opening for a price-transparent challenger.", "blue")


# ── VoC tab ───────────────────────────────────────────────────────────────────
@solara.component
def VoCTab():
    with solara.ColumnsResponsive(12, large=6):
        with solara.Card(style=CARD):
            solara.FigurePlotly(make_themes(COMPLAINTS, RED, "Top Complaint Themes (% of Negative Reviews)"))
            callout("⚠ Pricing complaints grew 22% → 34% over 6 quarters — fastest-growing negative signal.", "red")
        with solara.Card(style=CARD):
            solara.FigurePlotly(make_themes(PRAISE, GREEN, "Top Praise Themes (% of Positive Reviews)"))
            callout("Ease of use is HubSpot's durable #1 praise theme — consistent for 8 consecutive quarters.", "green")
    solara.Text("", style={"marginTop":"10px"})
    with solara.Card(style=CARD):
        sh("Praise vs Complaint Balance","Head-to-head by theme type")
        combined = pd.DataFrame({
            "Theme": list(PRAISE.keys()) + list(COMPLAINTS.keys()),
            "Pct":   list(PRAISE.values()) + list(COMPLAINTS.values()),
            "Type":  ["Praise"]*len(PRAISE) + ["Complaint"]*len(COMPLAINTS),
        })
        # Create bar chart with go.Figure instead of px to avoid template issues
        fig = go.Figure()
        praise_data = combined[combined["Type"] == "Praise"]
        complaint_data = combined[combined["Type"] == "Complaint"]
        
        fig.add_trace(go.Bar(
            name="Praise", x=praise_data["Pct"], y=praise_data["Theme"],
            orientation="h", text=praise_data["Pct"],
            marker=dict(color=GREEN, opacity=0.85),
            texttemplate="%{text}%", textposition="outside",
            textfont_color=TEXT2,
        ))
        fig.add_trace(go.Bar(
            name="Complaint", x=complaint_data["Pct"], y=complaint_data["Theme"],
            orientation="h", text=complaint_data["Pct"],
            marker=dict(color=RED, opacity=0.85),
            texttemplate="%{text}%", textposition="outside",
            textfont_color=TEXT2,
        ))
        fig.update_layout(**BASE, barmode="group", height=340, margin=DM,
                          yaxis=dict(autorange="reversed",**GRID),
                          xaxis=dict(title="% of reviews",**GRID))
        solara.FigurePlotly(fig)


# ── Whitespace & Signals tab ──────────────────────────────────────────────────
@solara.component
def WhitespaceTab():
    sc = scores_rv.value
    with solara.Card(style=CARD):
        sh("Whitespace Analysis","Dimensions where no player scores above 75")
        solara.FigurePlotly(make_whitespace(sc))
        callout("Customer support is the only dimension where no player has a clear advantage (max 75/100). A challenger at ≥85 captures the clearest moat in this market.", "blue")
    solara.Text("", style={"marginTop":"16px"})
    sh("Competitor Activity Monitor","Recent signals · last 90 days")
    solara.Text("", style={"marginBottom":"10px"})
    with solara.ColumnsResponsive(12, large=4):
        for company in COMPETITORS:
            sigs = [s for s in SIGNALS if s["company"]==company]
            with solara.Card(style=CARD):
                solara.Text(f"● {company}", style={
                    "fontFamily":"Inter, system-ui, sans-serif",
                    "fontSize":"12px","fontWeight":"700",
                    "color":COLORS[company],"marginBottom":"10px",
                })
                for sig in sigs:
                    with solara.Card(style={**CARD2,"padding":"10px 12px","marginBottom":"8px"}):
                        solara.Text(sig["icon"]+" "+sig["title"], style={
                            "fontFamily":"Inter, system-ui, sans-serif",
                            "fontWeight":"600","fontSize":"13px","color":TEXT})
                        solara.Text(sig["desc"], style={
                            "fontFamily":"Inter, system-ui, sans-serif",
                            "fontSize":"12px","color":TEXT2})
                        solara.Text(sig["time"], style={
                            "fontFamily":"Inter, system-ui, sans-serif",
                            "fontSize":"11px","color":TEXT3,"marginTop":"2px"})


# ── Sidebar ───────────────────────────────────────────────────────────────────
@solara.component
def Sidebar():
    F = "Inter, system-ui, sans-serif"
    solara.Text("ANALYSIS MODE", style={"fontFamily":F,"fontSize":"10px","fontWeight":"700",
        "letterSpacing":"1px","color":TEXT3,"marginBottom":"10px"})

    mode, set_mode = solara.use_state("Mock (pre-computed)")
    solara.Select("", value=mode,
                  values=["Mock (pre-computed)","Live — Groq","Live — OpenAI"],
                  on_value=set_mode)

    api_key, set_api_key = solara.use_state("")
    loading, set_loading = solara.use_state(False)
    message, set_message = solara.use_state("")

    if mode != "Mock (pre-computed)":
        placeholder = "gsk_..." if "Groq" in mode else "sk-..."
        solara.InputText(f"API Key  ({placeholder})", value=api_key,
                         on_value=set_api_key, password=True)

    def run():
        set_loading(True); set_message("")
        try:
            if mode == "Mock (pre-computed)":
                scores_rv.set(dict(MOCK_SCORES))
                insights_rv.set(list(MOCK_INSIGHTS))
                set_message("✓ Loaded pre-computed data.")
            else:
                env_var = "GROQ_API_KEY" if "Groq" in mode else "OPENAI_API_KEY"
                os.environ[env_var] = api_key
                client, fast, smart, detected = build_client()
                if client is None:
                    set_message("✗ Key not recognised."); return
                reviews = json.loads(
                    Path("data/sample_reviews.json").read_text(encoding="utf-8"))
                scores_rv.set(compute_dimension_scores(reviews, client, fast))
                insights_rv.set(generate_insights(scores_rv.value, client, smart))
                set_message(f"✓ Complete via {detected}.")
        except Exception as e:
            set_message(f"✗ {e}")
        finally:
            set_loading(False)

    solara.Button(
        "⏳ Running…" if loading else "▶  Run Analysis",
        on_click=lambda: threading.Thread(target=run, daemon=True).start(),
        color="primary", disabled=loading,
        style={"width":"100%","marginTop":"10px"},
    )
    if message:
        solara.Text(message, style={"fontFamily":F,"fontSize":"12px","marginTop":"6px",
            "color":GREEN if message.startswith("✓") else RED})


# ── Root Page ─────────────────────────────────────────────────────────────────
@solara.component
def Page():
    solara.Title("InsightEngine")

    solara.Style(f"""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ── Global reset to Inter ── */
        html, body, #app {{
            font-family: 'Inter', system-ui, sans-serif !important;
            background-color: {BG} !important;
        }}
        *, *::before, *::after {{
            font-family: 'Inter', system-ui, sans-serif !important;
            box-sizing: border-box;
        }}

        /* ── Vuetify overrides ── */
        .v-application,
        .v-application .text-h1, .v-application .text-h2,
        .v-application .text-h3, .v-application .text-h4,
        .v-application .text-h5, .v-application .text-h6,
        .v-application .text-body-1, .v-application .text-body-2,
        .v-application .text-subtitle-1, .v-application .text-subtitle-2,
        .v-application .text-caption, .v-application .text-overline,
        .v-application .font-weight-thin,
        .v-application .font-weight-light,
        .v-application .font-weight-regular,
        .v-application .font-weight-medium,
        .v-application .font-weight-bold,
        .v-application .font-weight-black {{
            font-family: 'Inter', system-ui, sans-serif !important;
        }}
        .v-application {{ background: {BG} !important; color: {TEXT} !important; }}
        .v-main {{ background: {BG} !important; }}
        .v-card  {{ background: {SURFACE} !important; color: {TEXT} !important;
                    border: 1px solid {BORDER} !important; }}
        .v-sheet {{ background: {SURFACE} !important; }}
        .v-navigation-drawer {{ background: {SURFACE} !important; border-right: 1px solid {BORDER} !important; }}
        .v-app-bar {{ background: {SURFACE} !important; border-bottom: 1px solid {BORDER} !important;
                      box-shadow: none !important; }}
        .v-toolbar__title {{ color: {TEXT} !important; }}

        /* ── Tabs ── */
        .v-tabs {{ background: {SURFACE2} !important; border-radius: 10px;
                   border: 1px solid {BORDER} !important; }}
        .v-tab  {{ font-family: 'Inter', sans-serif !important; font-weight: 500 !important;
                   font-size: 13px !important; color: {TEXT3} !important;
                   text-transform: none !important; letter-spacing: 0 !important;
                   min-width: 100px !important; padding: 0 20px !important; }}
        .v-tab--selected {{ color: {TEXT} !important; font-weight: 700 !important;
                            background: rgba(79,142,247,0.12) !important;
                            border-radius: 8px !important; }}
        .v-tab__slider {{ background: {ACCENT} !important; height: 3px !important; }}
        .v-tab--selected .v-tab__slider {{ background: {ACCENT} !important; height: 3px !important; }}

        /* ── Inputs ── */
        .v-field, .v-field__input, .v-field__outline, .v-label,
        .v-input input, .v-select__selection, .v-list-item-title {{
            font-family: 'Inter', sans-serif !important;
            color: {TEXT2} !important;
        }}
        .v-field {{ background: {SURFACE2} !important;
                    border-color: {BORDER} !important; }}
        .v-list   {{ background: {SURFACE2} !important; }}
        .v-list-item:hover {{ background: {BORDER} !important; }}

        /* ── Buttons ── */
        .v-btn {{ font-family: 'Inter', sans-serif !important;
                  text-transform: none !important; letter-spacing: 0 !important;
                  font-weight: 600 !important; font-size: 13px !important; }}

        /* ── Scrollbar ── */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: {BG}; }}
        ::-webkit-scrollbar-thumb {{ background: {BORDER2}; border-radius: 3px; }}
    """)

    with solara.AppBar():
        solara.Text("InsightEngine", style={
            "fontFamily":"Inter, system-ui, sans-serif",
            "fontWeight":"800","fontSize":"16px",
            "letterSpacing":"-0.5px","color":TEXT,
        })
        solara.Text("CRM · HubSpot Focus", style={
            "fontFamily":"Inter, system-ui, sans-serif",
            "fontSize":"12px","color":TEXT3,"marginLeft":"12px",
        })

    with solara.Sidebar():
        Sidebar()

    # ── Main ──────────────────────────────────────────────────────────────────
    with solara.Column(style={"padding":"20px 28px","maxWidth":"1280px","margin":"0 auto"}):

        # Header bar
        with solara.Card(style={**CARD,"marginBottom":"20px","padding":"16px 20px"}):
            with solara.Row(style={"justifyContent":"space-between","flexWrap":"wrap","gap":"12px","alignItems":"center"}):
                with solara.Column():
                    solara.Text("CRM Software — Competitive Intelligence Report", style={
                        "fontFamily":"Inter, system-ui, sans-serif",
                        "fontSize":"18px","fontWeight":"800",
                        "letterSpacing":"-0.5px","color":TEXT,
                    })
                    solara.Text(
                        "Aspect-based sentiment · 2,847 reviews · HubSpot vs Salesforce, Pipedrive, Zoho CRM · Jan 2024–Mar 2026",
                        style={"fontFamily":"Inter, system-ui, sans-serif","fontSize":"12px","color":TEXT3},
                    )
                with solara.Row(gap="6px", style={"flexWrap":"wrap","alignItems":"center"}):
                    for lbl,bg,fg in [
                        ("G2 · Capterra · Trustpilot", f"rgba(79,142,247,.15)", "#93C5FD"),
                        ("GPT-4o Analysis",             f"rgba(255,176,32,.15)", "#FCD34D"),
                        ("4 Companies · 6 Dimensions",  f"rgba(0,214,143,.15)", "#6EE7B7"),
                    ]:
                        solara.Text(lbl, style={
                            "fontFamily":"Inter, system-ui, sans-serif",
                            "background":bg,"color":fg,
                            "padding":"3px 10px","borderRadius":"20px",
                            "fontSize":"11px","fontWeight":"500",
                        })

        KPIRow()
        solara.Text("", style={"marginTop":"16px"})

        with solara.lab.Tabs(background_color=SURFACE2):
            with solara.lab.Tab("🧠  Insights"):
                solara.Text("", style={"marginTop":"14px"})
                InsightsTab()
            with solara.lab.Tab("📐  Competitive"):
                solara.Text("", style={"marginTop":"14px"})
                CompetitiveTab()
            with solara.lab.Tab("📈  Trends"):
                solara.Text("", style={"marginTop":"14px"})
                TrendsTab()
            with solara.lab.Tab("🗣  Voice of Customer"):
                solara.Text("", style={"marginTop":"14px"})
                VoCTab()
            with solara.lab.Tab("🔍  Whitespace"):
                solara.Text("", style={"marginTop":"14px"})
                WhitespaceTab()
