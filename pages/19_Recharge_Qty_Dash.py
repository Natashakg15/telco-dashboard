"""
Recharge Qty Dash — Recharges section
Data: UCONNECT_DW.ANALYTICS.VW_CELLC_RECHARGES
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE,
)
from utils.snowflake_conn import run_query

RECHARGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_CELLC_RECHARGES"

st.set_page_config(page_title="Recharge Qty Dash | Telco Retail", page_icon="⚡", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Recharge Qty Dash", badge="Recharges")

@st.cache_data(ttl=1800, show_spinner="Loading recharge data…")
def load_monthly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            RECHARGE_DESCRIPTION AS TYPE,
            COUNT(*) AS QTY,
            SUM(VALUE) AS TOTAL_VALUE
        FROM {RECHARGE_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
          AND RECHARGE_DESCRIPTION IS NOT NULL
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_weekly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('week', TRANSACTION_DATE) AS WEEK_START,
            RECHARGE_DESCRIPTION AS TYPE,
            COUNT(*) AS QTY,
            SUM(VALUE) AS TOTAL_VALUE
        FROM {RECHARGE_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(week,-26,CURRENT_DATE())
          AND RECHARGE_DESCRIPTION IS NOT NULL
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_kpis():
    df = run_query(f"""
        SELECT
            SUM(CASE WHEN DATE_TRUNC('month',TRANSACTION_DATE)=DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS QTY_MTD,
            SUM(CASE WHEN DATE_TRUNC('month',TRANSACTION_DATE)=DATE_TRUNC('month',CURRENT_DATE()) THEN VALUE ELSE 0 END) AS VALUE_MTD,
            SUM(CASE WHEN DATE_TRUNC('month',TRANSACTION_DATE)=DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE())) THEN 1 ELSE 0 END) AS QTY_LM,
            SUM(CASE WHEN DATE_TRUNC('month',TRANSACTION_DATE)=DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE())) THEN VALUE ELSE 0 END) AS VALUE_LM
        FROM {RECHARGE_TABLE}
        WHERE TRANSACTION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
    """)
    df.columns = [c.upper() for c in df.columns]
    return df.iloc[0] if not df.empty else {}

kpis     = load_kpis()
monthly  = load_monthly()
weekly   = load_weekly()

monthly["MONTH_START"] = pd.to_datetime(monthly["MONTH_START"])
weekly["WEEK_START"]   = pd.to_datetime(weekly["WEEK_START"])

qty_mtd   = int(kpis.get("QTY_MTD") or 0)
val_mtd   = float(kpis.get("VALUE_MTD") or 0)
qty_lm    = int(kpis.get("QTY_LM") or 0)
val_lm    = float(kpis.get("VALUE_LM") or 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Recharges This Month (Qty)", f"{qty_mtd:,}")
k2.metric("Revenue This Month", f"R{val_mtd:,.0f}")
k3.metric("Recharges Last Month (Qty)", f"{qty_lm:,}", delta=f"{qty_mtd-qty_lm:+,}")
k4.metric("Revenue Last Month", f"R{val_lm:,.0f}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

def _base(title="", barmode="stack"):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        bargap=0.3, barmode=barmode,
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )

c1, c2 = st.columns(2, gap="medium")
COLOURS = {"PINLESS+ATM": HYPERMINT, "VOUCHER": SONIC_BLUE}

with c1:
    pivot = monthly.pivot_table(index="MONTH_START", columns="TYPE", values="QTY", fill_value=0)
    fig = go.Figure()
    for t in pivot.columns:
        fig.add_trace(go.Bar(
            x=pivot.index.strftime("%b '%y").tolist(),
            y=pivot[t].tolist(),
            name=t, marker_color=COLOURS.get(t, ULTRAVIOLET), marker_line_width=0,
        ))
    fig.update_layout(**_base("Monthly Recharge Qty by Type (13 months)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    pivot_v = monthly.pivot_table(index="MONTH_START", columns="TYPE", values="TOTAL_VALUE", fill_value=0)
    fig2 = go.Figure()
    for t in pivot_v.columns:
        fig2.add_trace(go.Bar(
            x=pivot_v.index.strftime("%b '%y").tolist(),
            y=pivot_v[t].tolist(),
            name=t, marker_color=COLOURS.get(t, ULTRAVIOLET), marker_line_width=0,
        ))
    fig2.update_layout(**_base("Monthly Recharge Revenue by Type (13 months)"))
    fig2.update_layout(yaxis=dict(tickprefix="R", tickformat=",.0f", showgrid=True, gridcolor=BORDER))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    pivot_w = weekly.pivot_table(index="WEEK_START", columns="TYPE", values="QTY", fill_value=0)
    fig3 = go.Figure()
    for t in pivot_w.columns:
        fig3.add_trace(go.Bar(
            x=pivot_w.index.strftime("Wk %d %b '%y").tolist(),
            y=pivot_w[t].tolist(),
            name=t, marker_color=COLOURS.get(t, ULTRAVIOLET), marker_line_width=0,
        ))
    fig3.update_layout(**_base("Weekly Recharge Qty (26 weeks)"))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    pivot_wv = weekly.pivot_table(index="WEEK_START", columns="TYPE", values="TOTAL_VALUE", fill_value=0)
    fig4 = go.Figure()
    for t in pivot_wv.columns:
        fig4.add_trace(go.Bar(
            x=pivot_wv.index.strftime("Wk %d %b '%y").tolist(),
            y=pivot_wv[t].tolist(),
            name=t, marker_color=COLOURS.get(t, ULTRAVIOLET), marker_line_width=0,
        ))
    fig4.update_layout(**_base("Weekly Recharge Revenue (26 weeks)"))
    fig4.update_layout(yaxis=dict(tickprefix="R", tickformat=",.0f", showgrid=True, gridcolor=BORDER))
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
