"""
charts.py — Edstellar LNA Platform
All Plotly chart generation functions.
Pure logic — no Streamlit imports.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
BLUE   = "#4472C4"
GOLD   = "#F4A024"
GREEN  = "#217346"
RED    = "#C0392B"
PURPLE = "#7B2D8B"
TEAL   = "#16A085"
ORANGE = "#E67E22"
COLORS = [NAVY, BLUE, GOLD, GREEN, TEAL, PURPLE, ORANGE, RED,
          "#2ECC71","#E74C3C","#9B59B6","#1ABC9C","#F39C12","#3498DB"]

CHART_W      = 900
CHART_H      = 380
CHART_H_TALL = 480

_BASE = dict(
    font=dict(family="'DM Sans', Arial, sans-serif", size=11, color="#2C2C2C"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=60, r=40, t=50, b=60),
)


def _layout(**kwargs):
    """Merge _BASE with kwargs cleanly."""
    d = dict(_BASE)
    d.update(kwargs)
    return d


def bar_chart(x, y, title, xlabel="", ylabel="Count", color=NAVY, orientation="v", height=CHART_H):
    if orientation == "h":
        fig = go.Figure(go.Bar(
            x=y, y=x, orientation="h", marker_color=color,
            text=[f"{v:,.0f}" for v in y], textposition="outside",
        ))
        fig.update_layout(**_layout(
            title=dict(text=title, font=dict(size=13, color=NAVY)),
            height=height, xaxis_title=ylabel, yaxis_title=xlabel,
            xaxis=dict(gridcolor="#F0F0F0", linecolor="#CCCCCC"),
            yaxis=dict(gridcolor="#F0F0F0", linecolor="#CCCCCC", autorange="reversed"),
        ))
    else:
        fig = go.Figure(go.Bar(
            x=x, y=y, marker_color=color,
            text=[f"{v:,.0f}" for v in y], textposition="outside",
        ))
        fig.update_layout(**_layout(
            title=dict(text=title, font=dict(size=13, color=NAVY)),
            height=height, xaxis_title=xlabel, yaxis_title=ylabel,
            xaxis=dict(gridcolor="#F0F0F0", linecolor="#CCCCCC"),
            yaxis=dict(gridcolor="#F0F0F0", linecolor="#CCCCCC"),
        ))
    return fig


def multi_bar_chart(categories, series_dict, title, xlabel="", ylabel="", height=CHART_H):
    fig = go.Figure()
    for i, (name, vals) in enumerate(series_dict.items()):
        fig.add_trace(go.Bar(name=name, x=categories, y=vals, marker_color=COLORS[i % len(COLORS)]))
    fig.update_layout(**_layout(
        barmode="group",
        title=dict(text=title, font=dict(size=13, color=NAVY)),
        height=height, xaxis_title=xlabel, yaxis_title=ylabel,
        xaxis=dict(gridcolor="#F0F0F0"), yaxis=dict(gridcolor="#F0F0F0"),
    ))
    return fig


def stacked_bar_chart(categories, series_dict, title, xlabel="", ylabel="", height=CHART_H):
    fig = go.Figure()
    for i, (name, vals) in enumerate(series_dict.items()):
        fig.add_trace(go.Bar(name=name, x=categories, y=vals, marker_color=COLORS[i % len(COLORS)]))
    fig.update_layout(**_layout(
        barmode="stack",
        title=dict(text=title, font=dict(size=13, color=NAVY)),
        height=height, xaxis_title=xlabel, yaxis_title=ylabel,
        xaxis=dict(gridcolor="#F0F0F0"), yaxis=dict(gridcolor="#F0F0F0"),
    ))
    return fig


def pie_chart(labels, values, title, height=CHART_H):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.38,
        marker_colors=COLORS[:len(labels)],
        textinfo="label+percent", textfont_size=11,
    ))
    fig.update_layout(**_layout(
        title=dict(text=title, font=dict(size=13, color=NAVY)),
        height=height, margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="v", x=1.0),
    ))
    return fig


def heatmap_chart(z, x_labels, y_labels, title, height=CHART_H_TALL):
    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=[[0,"#FFFFFF"],[0.25,"#BDD7EE"],[0.5,"#4472C4"],[0.75,"#1B3A6B"],[1.0,"#0A1F3D"]],
        showscale=True, text=z,
        texttemplate="%{text}", textfont={"size": 9},
    ))
    fig.update_layout(**_layout(
        title=dict(text=title, font=dict(size=13, color=NAVY)),
        height=height, margin=dict(l=120, r=40, t=50, b=100),
        xaxis=dict(tickangle=-35, side="bottom"),
        yaxis=dict(autorange="reversed"),
    ))
    return fig


def treemap_chart(labels, parents, values, title, height=CHART_H):
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values,
        marker=dict(colorscale="Blues"),
        textinfo="label+value+percent root",
    ))
    fig.update_layout(**_layout(
        title=dict(text=title, font=dict(size=13, color=NAVY)),
        height=height, margin=dict(l=10, r=10, t=50, b=10),
    ))
    return fig


def scatter_quadrant(skill_df, title, height=CHART_H_TALL):
    color_map = {
        "Q1 — High Impact / High Urgency":  RED,
        "Q2 — High Impact / Low Urgency":   ORANGE,
        "Q3 — Low Impact / High Urgency":   BLUE,
        "Q4 — Low Impact / Low Urgency":    "#AAAAAA",
    }
    fig = go.Figure()
    for q, grp in skill_df.groupby("Quadrant"):
        fig.add_trace(go.Scatter(
            x=grp["gap_pct"], y=grp["avg_gap"],
            mode="markers+text", name=q,
            text=grp.get("Skill Name", grp["Skill ID"]),
            textposition="top center", textfont=dict(size=8),
            marker=dict(
                size=grp["emp_with_gap"].clip(5, 40),
                color=color_map.get(q, BLUE),
                opacity=0.8, line=dict(width=1, color="white"),
            ),
        ))
    fig.add_hline(y=1.5,  line_dash="dash", line_color="#999999", annotation_text="Urgency threshold")
    fig.add_vline(x=40,   line_dash="dash", line_color="#999999", annotation_text="Impact threshold")
    fig.update_layout(**_layout(
        title=dict(text=title, font=dict(size=13, color=NAVY)),
        height=height, xaxis_title="% Employees with Gap", yaxis_title="Average Gap Score",
        xaxis=dict(gridcolor="#F0F0F0"), yaxis=dict(gridcolor="#F0F0F0"),
        legend=dict(orientation="v", x=1.0, y=1.0),
    ))
    return fig


def radar_chart(labels, org_values, target_values, height=420):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=org_values + [org_values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name="Organisation",
        line=dict(color=NAVY, width=2),
        fillcolor=f"rgba(27,58,107,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=target_values + [target_values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name="Target",
        line=dict(color=GOLD, width=2, dash="dash"),
        fillcolor=f"rgba(244,160,36,0.08)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=dict(text="Composite Indices — Org vs Target", font=dict(size=13, color=NAVY)),
        font=dict(family="'DM Sans', Arial, sans-serif"),
        paper_bgcolor="white",
        height=height,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
    )
    return fig


def gauge_chart(value, title, min_val=0, max_val=100, threshold=None, height=200):
    """Single value gauge for KPI display."""
    color = GREEN if (threshold and value >= threshold) else (ORANGE if (threshold and value >= threshold * 0.75) else RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 12, "color": NAVY}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickfont": {"size": 9}},
            "bar": {"color": color},
            "bgcolor": "white",
            "steps": [
                {"range": [0, max_val * 0.5], "color": "#FFEEEE"},
                {"range": [max_val * 0.5, max_val * 0.75], "color": "#FFF3E0"},
                {"range": [max_val * 0.75, max_val], "color": "#E8F5E9"},
            ],
            "threshold": {
                "line": {"color": GOLD, "width": 3},
                "thickness": 0.75,
                "value": threshold or max_val * 0.8,
            },
        },
    ))
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="white")
    return fig
