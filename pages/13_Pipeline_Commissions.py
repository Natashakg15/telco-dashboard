"""
Pipeline & Provisional Commissions — Sales section
Data: Pipeline.xlsx (SharePoint: Telco Retail new business evaluation model /
Excel Reports), a weekly full-snapshot BDM tracker - snapshotted 2026-07-28,
one-time pull via Chrome, not a live connection (see data/pipeline_latest_snapshot.csv).
No commission/Rand-value column exists anywhere in this workbook, so
"Provisional Commissions" isn't shown here - only the pipeline funnel is real.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, CHART_PALETTE,
)

st.set_page_config(page_title="Pipeline & Provisional Commissions | Telco Retail", page_icon="💼", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Pipeline & Provisional Commissions", badge="Sales")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Source: hand-maintained BDM pipeline tracker on SharePoint, weekly snapshot dated "
    f"2026-02-23 (latest available when pulled 2026-07-28) — a one-time pull, not a live "
    f"connection, and already ~5 months stale. No decision-maker contact details are shown "
    f"here — counts only. "
    f"<span style='color:{HIGHVOLT_ORANGE};'>\"Provisional Commissions\" isn't available</span> — "
    f"this workbook has no Rand-value or commission column, only pipeline stage tracking.</p>",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_pipeline():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "pipeline_latest_snapshot.csv")
    return pd.read_csv(path)


df = load_pipeline()
snapshot_date = df["snapshot_date"].iloc[0] if not df.empty else "—"

stage_totals = df.groupby(["stage", "sort"])["count"].sum().reset_index().sort_values("sort")
total_pipeline = int(df["count"].sum())
won = int(stage_totals.loc[stage_totals["stage"] == "Live and Trading", "count"].sum())
lost = int(stage_totals.loc[stage_totals["stage"] == "Not interested or deal lost", "count"].sum())
active = total_pipeline - won - lost
win_rate = (won / (won + lost) * 100) if (won + lost) else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Pipeline (this snapshot)", f"{total_pipeline:,}")
k2.metric("Active (in progress)", f"{active:,}")
k3.metric("Live and Trading (won)", f"{won:,}")
k4.metric("Win Rate (won / won+lost)", f"{win_rate:.1f}%")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)


def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        bargap=0.3,
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )


c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure(go.Funnel(
        y=stage_totals["stage"].tolist(),
        x=stage_totals["count"].tolist(),
        textinfo="value+percent initial",
        marker=dict(color=CHART_PALETTE[: len(stage_totals)] * (len(stage_totals) // len(CHART_PALETTE) + 1)),
    ))
    fig.update_layout(
        title=dict(text="Pipeline Funnel by Stage", font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    cat_totals = df.groupby("category")["count"].sum().sort_values(ascending=False)
    fig2 = go.Figure(go.Bar(
        x=cat_totals.index.tolist(), y=cat_totals.values.tolist(),
        marker_color=CHART_PALETTE[: len(cat_totals)], marker_line_width=0,
        hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
    ))
    fig2.update_layout(**_base("Pipeline by Category (all stages)"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    pivot = df.pivot_table(index="stage", columns="category", values="count", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(stage_totals.sort_values("sort", ascending=False)["stage"])
    fig3 = go.Figure()
    for i, cat in enumerate(pivot.columns):
        fig3.add_trace(go.Bar(
            y=pivot.index.tolist(), x=pivot[cat].tolist(), name=cat, orientation="h",
            marker_color=CHART_PALETTE[i % len(CHART_PALETTE)], marker_line_width=0,
        ))
    layout3 = _base("Stage by Category (Stacked)")
    layout3["barmode"] = "stack"
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    win_by_cat = df[df["stage"].isin(["Live and Trading", "Not interested or deal lost"])]
    wc = win_by_cat.pivot_table(index="category", columns="stage", values="count", aggfunc="sum", fill_value=0)
    if "Live and Trading" in wc.columns and "Not interested or deal lost" in wc.columns:
        wc["Win Rate %"] = (
            wc["Live and Trading"] / (wc["Live and Trading"] + wc["Not interested or deal lost"]).replace(0, float("nan")) * 100
        ).round(1)
        fig4 = go.Figure(go.Bar(
            x=wc.index.tolist(), y=wc["Win Rate %"].tolist(),
            marker_color=HYPERMINT, marker_line_width=0,
            hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>",
        ))
        layout4 = _base("Win Rate by Category (won ÷ won+lost)")
        layout4["yaxis"] = dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", range=[0, 100])
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
