"""
Revenue Comparisons — Recharges section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE
Side-by-side comparison across streams, with MoM and YoY delta.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2,
)
from utils.snowflake_conn import run_query

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Revenue Comparisons | Telco Retail", page_icon="📊", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Revenue Comparisons", badge="Recharges")

@st.cache_data(ttl=1800, show_spinner="Loading comparison data…")
def load_monthly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            SUM(COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0))             AS CELLC,
            SUM(COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)) AS VOUCHER,
            SUM(COALESCE(REVENUE_APP_PURCHASES_VALUE,0))              AS APP,
            SUM(COALESCE(REVENUE_MAY_BILLRUN_VALUE,0))                AS BILLRUN,
            SUM(COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0))      AS POSTPAID
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-14,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

df = load_monthly()
df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])

STREAMS = {
    "Cell C Recharge": "CELLC",
    "Retail Voucher":  "VOUCHER",
    "App Purchases":   "APP",
    "Billrun":         "BILLRUN",
    "Postpaid":        "POSTPAID",
}
COLOURS = [HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE, "#9b59b6"]

# ── KPI comparison strip: This Month vs Last Month vs Same Month Last Year ────
if not df.empty:
    this_m = df[df["MONTH_START"] == df["MONTH_START"].max()]
    prev_m = df[df["MONTH_START"] == df["MONTH_START"].max() - pd.DateOffset(months=1)]

    st.markdown(
        f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:8px;'>"
        f"This Month vs Last Month</h3>",
        unsafe_allow_html=True,
    )
    kpi_cols = st.columns(len(STREAMS))
    for col, (name, field) in zip(kpi_cols, STREAMS.items()):
        tm = float(this_m[field].iloc[0]) if not this_m.empty and field in this_m.columns else 0
        lm = float(prev_m[field].iloc[0]) if not prev_m.empty and field in prev_m.columns else 0
        col.metric(name, f"R{tm:,.0f}", delta=f"R{tm-lm:+,.0f}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

x = df["MONTH_START"].dt.strftime("%b '%y").tolist()

def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickprefix="R", tickformat=",.0f"),
        bargap=0.3,
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )

# ── Grouped bar: streams side by side ─────────────────────────────────────────
fig = go.Figure()
for i, (name, col) in enumerate(STREAMS.items()):
    if col in df.columns:
        fig.add_trace(go.Bar(
            x=x, y=df[col].tolist(),
            name=name, marker_color=COLOURS[i], marker_line_width=0,
        ))
fig.update_layout(**_base("Revenue by Stream — Side by Side (13 months)"))
fig.update_layout(barmode="group")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Line chart: share of total ─────────────────────────────────────────────────
c1, c2 = st.columns(2, gap="medium")
with c1:
    total = sum(df[c] for c in STREAMS.values() if c in df.columns)
    fig2 = go.Figure()
    for i, (name, col) in enumerate(STREAMS.items()):
        if col in df.columns and total.sum() > 0:
            pct = (df[col] / total * 100).round(1)
            fig2.add_trace(go.Scatter(
                x=x, y=pct.tolist(), name=name, mode="lines",
                line=dict(color=COLOURS[i], width=2),
                stackgroup="one",
            ))
    layout2 = _base("Revenue Share by Stream (%)")
    layout2["yaxis"] = dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", range=[0, 100])
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

with c2:
    # MoM delta waterfall for latest month
    if not df.empty and len(df) >= 2:
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        names = list(STREAMS.keys())
        deltas = [float(curr[STREAMS[n]]) - float(prev[STREAMS[n]]) for n in names if STREAMS[n] in df.columns]
        bar_colours = [HYPERMINT if d >= 0 else HIGHVOLT_ORANGE for d in deltas]
        fig3 = go.Figure(go.Bar(
            x=names[:len(deltas)], y=deltas,
            marker_color=bar_colours, marker_line_width=0,
            hovertemplate="%{x}<br><b>R%{y:+,.0f}</b><extra></extra>",
        ))
        layout3 = dict(
            title=dict(text=f"MoM Revenue Change — {df['MONTH_START'].iloc[-1].strftime('%b %Y')}",
                       font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
            yaxis=dict(showgrid=True, gridcolor=BORDER, tickprefix="R", tickformat="+,.0f"),
            bargap=0.3,
        )
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
