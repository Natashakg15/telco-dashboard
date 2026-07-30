"""
Acquisition Cost Metrics — Financials section
Data: UCONNECT_MAY_MERGE (activations) + UCONNECT_MAY_MERGE_REVENUE (reward payouts)
Full CPA requires GL cost data (pending). Reward-based cost per acquisition available now.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, CHART_PALETTE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE
from utils.financials import load_financials, section_total, SNAPSHOT_DATE, UNVERIFIED_FROM

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Acquisition Cost Metrics | Telco Retail", page_icon="🎯", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Acquisition Cost Metrics", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Reward-based cost per acquisition from UCONNECT_MAY_MERGE_REVENUE (live). "
    f"Full CPA below uses the GL Acquisition Cost section from a hand-maintained "
    f"Excel snapshot ({SNAPSHOT_DATE}) — the two won't reconcile exactly since they're "
    f"different sources measuring overlapping but not identical cost lines.</p>",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=1800, show_spinner="Loading acquisition cost data…")
def load_monthly_combined():
    df = run_query(f"""
        SELECT
            m.MONTH_START,
            m.ACTIVATIONS,
            COALESCE(r.REWARD_VALUE, 0)                                        AS REWARD_VALUE,
            COALESCE(r.REWARD_QTY,   0)                                        AS REWARD_QTY,
            COALESCE(r.TOTAL_REVENUE, 0)                                       AS TOTAL_REVENUE,
            CASE WHEN m.ACTIVATIONS > 0
                 THEN COALESCE(r.REWARD_VALUE, 0) / m.ACTIVATIONS
                 ELSE 0 END                                                    AS REWARD_COST_PER_ACT
        FROM (
            SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS ACTIVATIONS
            FROM {MERGE_TABLE}
            WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
            GROUP BY 1
        ) m
        LEFT JOIN (
            SELECT
                DATE_TRUNC('month', TRANSACTION_DATE)              AS MONTH_START,
                SUM(COALESCE(REVENUE_PAID_FOR_REWARDS_VALUE,0))    AS REWARD_VALUE,
                SUM(COALESCE(REVENUE_PAID_FOR_REWARDS_QUANTITY,0)) AS REWARD_QTY,
                -- REVENUE_WHATSAPP_PURCHASES_VALUE excluded: corrupted for every row of
                -- WALLET='Recharge Wallet - Customer WhatsApp purchases' (~1e18-1e19
                -- magnitude, confirmed 2023-09 through 2026-07) - needs an upstream ETL fix.
                SUM(
                    COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
                  + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
                  + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
                  + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
                  + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)
                  + COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0)
                )                                                  AS TOTAL_REVENUE
            FROM {REV_TABLE}
            WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
            GROUP BY 1
        ) r ON m.MONTH_START = r.MONTH_START
        ORDER BY m.MONTH_START
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


df = load_monthly_combined()
df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])
x = df["MONTH_START"].dt.strftime("%b '%y").tolist()

this_m = df.iloc[-1]  if not df.empty else None
last_m = df.iloc[-2]  if len(df) >= 2 else None

reward_mtd   = float(this_m["REWARD_VALUE"])        if this_m is not None else 0.0
reward_qty   = int(this_m["REWARD_QTY"])            if this_m is not None else 0
cpa_this     = float(this_m["REWARD_COST_PER_ACT"]) if this_m is not None else 0.0
cpa_last     = float(last_m["REWARD_COST_PER_ACT"]) if last_m is not None else 0.0
total_reward = float(df["REWARD_VALUE"].sum())       if not df.empty else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Reward Payouts This Month", f"R{reward_mtd:,.0f}")
k2.metric("Rewards Paid This Month (Qty)", f"{reward_qty:,}")
k3.metric("Reward Cost per Activation", f"R{cpa_this:.2f}", delta=f"R{cpa_this-cpa_last:+.2f} vs last month")
k4.metric("Total Reward Spend (13M)", f"R{total_reward:,.0f}")

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
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=df["ACTIVATIONS"].tolist(),
        name="Activations", marker_color=HYPERMINT, marker_line_width=0, yaxis="y",
        hovertemplate="%{x}<br><b>%{y:,} activations</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df["REWARD_QTY"].tolist(),
        name="Rewards Paid", mode="lines+markers",
        line=dict(color=HIGHVOLT_ORANGE, width=2), marker=dict(size=4),
        yaxis="y2",
        hovertemplate="%{x}<br><b>%{y:,} rewards</b><extra></extra>",
    ))
    layout1 = _base("Activations vs Reward Qty — 13 Months")
    layout1["yaxis"] = dict(showgrid=True, gridcolor=BORDER, tickformat=",",
                             title=dict(text="Activations", font=dict(color=HYPERMINT, size=11)))
    layout1["yaxis2"] = dict(overlaying="y", side="right", showgrid=False, tickformat=",",
                              title=dict(text="Rewards Paid", font=dict(color=HIGHVOLT_ORANGE, size=11)))
    fig.update_layout(**layout1)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Scatter(
        x=x, y=df["REWARD_COST_PER_ACT"].tolist(),
        mode="lines+markers",
        line=dict(color=ULTRAVIOLET, width=2), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(82,190,192,0.08)",
        hovertemplate="%{x}<br><b>R%{y:.2f} per activation</b><extra></extra>",
    ))
    layout2 = _base("Reward Cost per Activation — Monthly Trend")
    layout2["yaxis"]["tickprefix"] = "R"
    layout2["yaxis"]["tickformat"] = ",.2f"
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    if not df.empty and "TOTAL_REVENUE" in df.columns:
        df["REWARD_PCT_REV"] = (
            df["REWARD_VALUE"] / df["TOTAL_REVENUE"].replace(0, float("nan")) * 100
        ).round(2)
        fig3 = go.Figure(go.Bar(
            x=x, y=df["REWARD_PCT_REV"].tolist(),
            marker_color=SONIC_BLUE, marker_line_width=0,
            hovertemplate="%{x}<br><b>%{y:.1f}% of revenue</b><extra></extra>",
        ))
        layout3 = _base("Reward Spend as % of Revenue — Monthly")
        layout3["yaxis"]["ticksuffix"] = "%"
        layout3["yaxis"]["tickformat"] = ",.1f"
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    fin_df = load_financials()
    gl_acq = section_total(fin_df, "Acqusition Cost")
    acts_by_month = df.set_index("MONTH_START")["ACTIVATIONS"]
    full_cpa = (gl_acq / acts_by_month.reindex(gl_acq.index).replace(0, float("nan")))
    trend_cutoff = min(pd.Timestamp(date.today()) + pd.DateOffset(months=1), UNVERIFIED_FROM)
    full_cpa_t = full_cpa[(full_cpa.index <= trend_cutoff) & full_cpa.index.isin(acts_by_month.index)].tail(13)
    if not full_cpa_t.dropna().empty:
        fig4 = go.Figure(go.Scatter(
            x=full_cpa_t.index.strftime("%b '%y").tolist(), y=full_cpa_t.tolist(),
            mode="lines+markers", line=dict(color=HIGHVOLT_ORANGE, width=2),
            fill="tozeroy", fillcolor="rgba(244,70,16,0.08)",
            hovertemplate="%{x}<br><b>R%{y:,.2f} per activation</b><extra></extra>",
        ))
        layout4 = _base("Full CPA — GL Acquisition Cost ÷ Activations")
        layout4["yaxis"]["tickprefix"] = "R"
        layout4["yaxis"]["tickformat"] = ",.2f"
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    else:
        st.caption("Full CPA unavailable — no overlapping months between GL and Snowflake activation data.")
