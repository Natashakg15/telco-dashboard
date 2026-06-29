"""
Exco Scorecard — Strategy section
Data: UCONNECT_MAY_MERGE + UCONNECT_MAY_MERGE_REVENUE
High-level KPIs for Exco / board view.
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

st.set_page_config(page_title="Exco Scorecard | Telco Retail", page_icon="🎯", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Exco Scorecard", badge="Strategy")


@st.cache_data(ttl=1800, show_spinner="Loading Exco metrics…")
def load_active_sims():
    df = run_query(f"""
        SELECT COUNT(*) AS ACTIVE_SIM_COUNT
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NULL
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_act_mtd():
    df = run_query(f"""
        SELECT COUNT(*) AS ACT_MTD
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATE_TRUNC('month', CURRENT_DATE())
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_act_last_month():
    df = run_query(f"""
        SELECT COUNT(*) AS ACT_MTD
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
          AND ACTIVATION_DATE <  DATE_TRUNC('month', CURRENT_DATE())
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_rev_mtd():
    df = run_query(f"""
        SELECT SUM(
            COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
          + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
          + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
          + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
          + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
          + COALESCE(REVENUE_WHATSAPP_PURCHASES_VALUE,0)
          + COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0)
        ) AS REV_MTD
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATE_TRUNC('month', CURRENT_DATE())
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_monthly_activations():
    df = run_query(f"""
        SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_monthly_revenue():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            SUM(
                COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
              + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
              + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
              + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
              + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
              + COALESCE(REVENUE_WHATSAPP_PURCHASES_VALUE,0)
              + COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0)
            ) AS TOTAL_REVENUE
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
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


@st.cache_data(ttl=1800, show_spinner=False)
def load_churn_reasons():
    df = run_query(f"""
        SELECT COALESCE(CHURN_REASON,'Unknown') AS CHURN_REASON, COUNT(*) AS CHURN_COUNT
        FROM {MERGE_TABLE}
        WHERE TERMINATION_DATE IS NOT NULL
          AND TERMINATION_DATE >= DATEADD(month,-3,CURRENT_DATE())
        GROUP BY 1 ORDER BY 2 DESC
        LIMIT 8
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


active_df   = load_active_sims()
act_mtd_df  = load_act_mtd()
act_lm_df   = load_act_last_month()
rev_mtd_df  = load_rev_mtd()
monthly_act = load_monthly_activations()
monthly_rev = load_monthly_revenue()
channel_df  = load_channel_mix()
churn_df    = load_churn_reasons()

active_sims = int(active_df.iloc[0, 0])   if not active_df.empty  else 0
act_mtd     = int(act_mtd_df.iloc[0, 0])  if not act_mtd_df.empty else 0
act_lm      = int(act_lm_df.iloc[0, 0])   if not act_lm_df.empty  else 0
rev_mtd     = float(rev_mtd_df.iloc[0, 0]) if not rev_mtd_df.empty else 0.0
mom_delta   = act_mtd - act_lm

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Active SIMs", f"{active_sims:,}")
k2.metric("Activations This Month", f"{act_mtd:,}", delta=f"{mom_delta:+,} vs last month")
k3.metric("Revenue MTD", f"R{rev_mtd:,.0f}")
k4.metric("Last Month Activations", f"{act_lm:,}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

monthly_act["MONTH_START"] = pd.to_datetime(monthly_act["MONTH_START"])
monthly_rev["MONTH_START"] = pd.to_datetime(monthly_rev["MONTH_START"])


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
    x_act = monthly_act["MONTH_START"].dt.strftime("%b '%y").tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_act, y=monthly_act["ACTIVATIONS"].tolist(),
        name="Activations", marker_color=HYPERMINT, marker_line_width=0,
        hovertemplate="%{x}<br><b>%{y:,} activations</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x_act,
        y=monthly_act["ACTIVATIONS"].rolling(3, min_periods=1).mean().round(0).tolist(),
        mode="lines", name="3M avg", line=dict(color=HIGHVOLT_ORANGE, width=2),
        hovertemplate="%{x}<br>3M avg: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(**_base("Monthly Activations — 13 Months"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    x_rev = monthly_rev["MONTH_START"].dt.strftime("%b '%y").tolist()
    fig2 = go.Figure(go.Bar(
        x=x_rev, y=monthly_rev["TOTAL_REVENUE"].tolist(),
        marker_color=SONIC_BLUE, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    layout2 = _base("Monthly Revenue — 13 Months")
    layout2["yaxis"]["tickprefix"] = "R"
    layout2["yaxis"]["tickformat"] = ",.0f"
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    if not channel_df.empty and "CHANNEL" in channel_df.columns:
        fig3 = go.Figure(go.Pie(
            labels=channel_df["CHANNEL"].tolist(),
            values=channel_df["SIMS"].tolist(),
            hole=0.45,
            marker=dict(colors=CHART_PALETTE),
            textfont=dict(size=11),
            hovertemplate="%{label}<br><b>%{value:,} SIMs (%{percent})</b><extra></extra>",
        ))
        fig3.update_layout(
            title=dict(text="SIM Acquisition by Channel (All Time)", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            legend=dict(orientation="h", y=-0.1, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    if not churn_df.empty and "CHURN_REASON" in churn_df.columns:
        fig4 = go.Figure(go.Bar(
            y=churn_df["CHURN_REASON"].tolist(),
            x=churn_df["CHURN_COUNT"].tolist(),
            orientation="h",
            marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
            hovertemplate="%{y}<br><b>%{x:,} churns</b><extra></extra>",
        ))
        fig4.update_layout(
            title=dict(text="Churn by Reason — Last 3 Months", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
            yaxis=dict(showgrid=False, autorange="reversed"),
            bargap=0.3,
        )
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
