"""
Revenue Trends — Strategy & Book section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE
High-level revenue trends for Exco / strategy view.
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

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Revenue Trends | Telco Retail", page_icon="📈", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Revenue Trends", badge="Strategy")

@st.cache_data(ttl=1800, show_spinner="Loading revenue trends…")
def load_monthly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            -- REVENUE_WHATSAPP_PURCHASES_VALUE excluded: corrupted for every row of
            -- WALLET='Recharge Wallet - Customer WhatsApp purchases' (~1e18-1e19 magnitude,
            -- confirmed 2023-09 through 2026-07) - needs an upstream ETL fix first.
            SUM(
                COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
              + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
              + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
              + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
              + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
              + COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0)
            ) AS TOTAL_REVENUE,
            SUM(COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0))             AS CELLC,
            SUM(COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)) AS VOUCHER,
            SUM(COALESCE(REVENUE_APP_PURCHASES_VALUE,0))              AS APP,
            SUM(COALESCE(REVENUE_MAY_BILLRUN_VALUE,0))                AS BILLRUN,
            SUM(COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0))      AS POSTPAID
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_tenant_revenue():
    df = run_query(f"""
        SELECT
            COALESCE(MASTER_TENANT,'Unknown') AS TENANT,
            SUM(
                COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
              + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
              + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
              + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
              + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
            ) AS TOTAL_REVENUE
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-3,CURRENT_DATE())
          AND MASTER_TENANT IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC
        LIMIT 10
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

monthly = load_monthly()
tenant  = load_tenant_revenue()

monthly["MONTH_START"] = pd.to_datetime(monthly["MONTH_START"])
x = monthly["MONTH_START"].dt.strftime("%b '%y").tolist()

this_m = float(monthly.iloc[-1]["TOTAL_REVENUE"]) if not monthly.empty else 0
last_m = float(monthly.iloc[-2]["TOTAL_REVENUE"]) if len(monthly) >= 2 else 0
ytd    = float(monthly[monthly["MONTH_START"].dt.year == monthly["MONTH_START"].max().year]["TOTAL_REVENUE"].sum()) if not monthly.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue This Month", f"R{this_m:,.0f}")
k2.metric("Total Revenue Last Month", f"R{last_m:,.0f}", delta=f"R{this_m-last_m:+,.0f}")
k3.metric("YTD Revenue", f"R{ytd:,.0f}")
k4.metric("Avg Monthly (13M)", f"R{monthly['TOTAL_REVENUE'].mean():,.0f}" if not monthly.empty else "—")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

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

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=monthly["TOTAL_REVENUE"].tolist(),
        name="Total Revenue",
        marker_color=SONIC_BLUE, marker_line_width=0, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=x, y=monthly["TOTAL_REVENUE"].rolling(3, min_periods=1).mean().round(0).tolist(),
        name="3-Month Avg",
        mode="lines", line=dict(color=HYPERMINT, width=2),
    ))
    fig.update_layout(**_base("Total Monthly Revenue + 3-Month Rolling Avg"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    streams = [("Cell C", "CELLC", HYPERMINT), ("App", "APP", HIGHVOLT_ORANGE),
               ("Billrun", "BILLRUN", SONIC_BLUE), ("Postpaid", "POSTPAID", ULTRAVIOLET),
               ("Voucher", "VOUCHER", "#9b59b6")]
    fig2 = go.Figure()
    for name, col, colour in streams:
        if col in monthly.columns:
            fig2.add_trace(go.Scatter(
                x=x, y=monthly[col].tolist(),
                name=name, mode="lines",
                line=dict(color=colour, width=2),
            ))
    fig2.update_layout(**_base("Revenue by Stream — Trend Lines"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    if not tenant.empty:
        fig3 = go.Figure(go.Bar(
            y=tenant["TENANT"].tolist(),
            x=tenant["TOTAL_REVENUE"].tolist(),
            orientation="h",
            marker_color=ULTRAVIOLET, marker_line_width=0,
            hovertemplate="%{y}<br><b>R%{x:,.0f}</b><extra></extra>",
        ))
        layout3 = dict(
            title=dict(text="Revenue by Master Tenant (last 3 months)", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(showgrid=True, gridcolor=BORDER, tickprefix="R", tickformat=",.0f"),
            yaxis=dict(showgrid=False, autorange="reversed"),
            bargap=0.3,
        )
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    # Running cumulative for current year
    this_yr = monthly[monthly["MONTH_START"].dt.year == monthly["MONTH_START"].max().year].copy()
    if not this_yr.empty:
        this_yr["CUMULATIVE"] = this_yr["TOTAL_REVENUE"].cumsum()
        fig4 = go.Figure(go.Scatter(
            x=this_yr["MONTH_START"].dt.strftime("%b '%y").tolist(),
            y=this_yr["CUMULATIVE"].tolist(),
            mode="lines+markers",
            line=dict(color=HYPERMINT, width=2),
            fill="tozeroy",
            fillcolor="rgba(19,244,96,0.08)",
            marker=dict(color=HYPERMINT, size=6),
        ))
        layout4 = _base("Cumulative Revenue — Current Year")
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
