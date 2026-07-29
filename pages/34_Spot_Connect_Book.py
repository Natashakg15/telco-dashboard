"""
Spot Connect Book — Strategy section
Data: UCONNECT_MAY_MERGE + UCONNECT_MAY_MERGE_REVENUE
Business-of-record snapshot: SIM base, revenue, channel & product mix.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, CHART_PALETTE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Spot Connect Book | Telco Retail", page_icon="📖", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Spot Connect Book", badge="Strategy")


@st.cache_data(ttl=1800, show_spinner="Loading business overview…")
def load_total_sims():
    df = run_query(f"SELECT COUNT(*) AS TOTAL_SIMS_SOLD FROM {MERGE_TABLE}")
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_active_sims():
    df = run_query(f"""
        SELECT COUNT(*) AS ACTIVE_SIM_COUNT FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NULL
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_ltm_revenue():
    df = run_query(f"""
        -- REVENUE_WHATSAPP_PURCHASES_VALUE excluded: corrupted for every row of
        -- WALLET='Recharge Wallet - Customer WhatsApp purchases' (~1e18-1e19 magnitude,
        -- confirmed 2023-09 through 2026-07) - needs an upstream ETL fix first.
        SELECT SUM(
            COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
          + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
          + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
          + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
          + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
          + COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0)
        ) AS REV_MTD
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-12,CURRENT_DATE())
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_monthly():
    act = run_query(f"""
        SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    act.columns = [c.upper() for c in act.columns]
    rev = run_query(f"""
        SELECT DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
               SUM(
                   COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
                 + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
                 + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
                 + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
                 + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
                 + COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0)
               ) AS TOTAL_REVENUE
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    rev.columns = [c.upper() for c in rev.columns]
    return act, rev


@st.cache_data(ttl=1800, show_spinner=False)
def load_grouping_mix():
    df = run_query(f"""
        SELECT COALESCE(GROUPING,'Unknown') AS SIM_GROUPING, COUNT(*) AS SIMS
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NULL
        GROUP BY 1 ORDER BY 2 DESC
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_channel_mix():
    df = run_query(f"""
        SELECT COALESCE(SALES_CHANNEL,'Unknown') AS CHANNEL, COUNT(*) AS SIMS
        FROM {MERGE_TABLE}
        GROUP BY 1 ORDER BY 2 DESC
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


total_df   = load_total_sims()
active_df  = load_active_sims()
ltm_df     = load_ltm_revenue()
monthly_act, monthly_rev = load_monthly()
grouping_df = load_grouping_mix()
channel_df  = load_channel_mix()

total_sims  = int(total_df.iloc[0, 0])   if not total_df.empty  else 0
active_sims = int(active_df.iloc[0, 0])  if not active_df.empty else 0
ltm_rev     = float(ltm_df.iloc[0, 0])   if not ltm_df.empty    else 0.0
monthly_act["MONTH_START"] = pd.to_datetime(monthly_act["MONTH_START"])
avg_monthly = int(monthly_act["ACTIVATIONS"].mean()) if not monthly_act.empty else 0
churn_count = total_sims - active_sims

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total SIMs Sold (All Time)", f"{total_sims:,}")
k2.metric("Active SIM Base", f"{active_sims:,}", delta=f"{churn_count:,} churned")
k3.metric("Revenue — Last 12 Months", f"R{ltm_rev:,.0f}")
k4.metric("Avg Monthly Activations (13M)", f"{avg_monthly:,}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

monthly_rev["MONTH_START"] = pd.to_datetime(monthly_rev["MONTH_START"])
x = monthly_act["MONTH_START"].dt.strftime("%b '%y").tolist()


def _pie(labels, values, title):
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.45,
        marker=dict(colors=CHART_PALETTE),
        textfont=dict(size=11),
        hovertemplate="%{label}<br><b>%{value:,} SIMs (%{percent})</b><extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        legend=dict(orientation="h", y=-0.1, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )
    return fig


c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=monthly_act["ACTIVATIONS"].tolist(),
        name="Activations", marker_color=HYPERMINT, marker_line_width=0,
        yaxis="y", hovertemplate="%{x}<br><b>%{y:,} activations</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=monthly_rev["TOTAL_REVENUE"].tolist(),
        name="Revenue", mode="lines+markers",
        line=dict(color=HIGHVOLT_ORANGE, width=2), marker=dict(size=4),
        yaxis="y2",
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Monthly Activations & Revenue — 13 Months", font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=",", title=dict(text="Activations", font=dict(color=HYPERMINT, size=11))),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, tickprefix="R", tickformat=",.0f",
                    title=dict(text="Revenue", font=dict(color=HIGHVOLT_ORANGE, size=11))),
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    # Cumulative active SIM base over time (month-end snapshot approximation)
    cum = monthly_act.copy().sort_values("MONTH_START")
    cum["CUM_ACTIVATIONS"] = cum["ACTIVATIONS"].cumsum()
    fig2 = go.Figure(go.Scatter(
        x=cum["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=cum["CUM_ACTIVATIONS"].tolist(),
        mode="lines+markers",
        line=dict(color=SONIC_BLUE, width=2),
        fill="tozeroy", fillcolor="rgba(45,64,233,0.10)",
        marker=dict(color=SONIC_BLUE, size=5),
        hovertemplate="%{x}<br><b>%{y:,} cumulative activations</b><extra></extra>",
    ))
    fig2.update_layout(
        title=dict(text="Cumulative Activations — 13 Month Rollup", font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    if not grouping_df.empty and "SIM_GROUPING" in grouping_df.columns:
        st.plotly_chart(
            _pie(grouping_df["SIM_GROUPING"].tolist(), grouping_df["SIMS"].tolist(),
                 "Active SIMs by Grouping (Prepay / Postpaid / FLTE)"),
            use_container_width=True, config={"displayModeBar": False},
        )

with c4:
    if not channel_df.empty and "CHANNEL" in channel_df.columns:
        st.plotly_chart(
            _pie(channel_df["CHANNEL"].tolist(), channel_df["SIMS"].tolist(),
                 "SIM Acquisition by Sales Channel (All Time)"),
            use_container_width=True, config={"displayModeBar": False},
        )
