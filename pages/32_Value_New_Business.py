"""
Value of New Business — Financials section
Data: cohort-aging revenue built from UCONNECT_MAY_MERGE + UCONNECT_MAY_MERGE_REVENUE
(see utils/cohort.py) + reward-based CPA from UCONNECT_MAY_MERGE_REVENUE.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE
from utils.cohort import load_cohort_aging, REV_TABLE
from utils.page_helpers import placeholder_chart

st.set_page_config(page_title="Value of New Business | Telco Retail", page_icon="💎", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Value of New Business", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Cohort revenue built from UCONNECT_MAY_MERGE + UCONNECT_MAY_MERGE_REVENUE, no "
    f"dedicated cohort table. LTV is a proxy (cumulative revenue per acquired over the "
    f"available aging window, not a true lifetime estimate) — "
    f"<span style='color:{HIGHVOLT_ORANGE};'>treat as directional, not final.</span> "
    f"\"Payback by Channel\" isn't shown — revenue data has no channel dimension to join on.</p>",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=1800, show_spinner=False)
def load_reward_cpa():
    df = run_query(f"""
        SELECT
            m.MONTH_START, m.ACTIVATIONS,
            COALESCE(r.REWARD_VALUE, 0) / NULLIF(m.ACTIVATIONS, 0) AS REWARD_COST_PER_ACT
        FROM (
            SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS ACTIVATIONS
            FROM {MERGE_TABLE}
            WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
            GROUP BY 1
        ) m
        LEFT JOIN (
            SELECT DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
                   SUM(COALESCE(REVENUE_PAID_FOR_REWARDS_VALUE,0)) AS REWARD_VALUE
            FROM {REV_TABLE}
            WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
            GROUP BY 1
        ) r ON m.MONTH_START = r.MONTH_START
        ORDER BY m.MONTH_START
    """)
    df.columns = [c.upper() for c in df.columns]
    df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])
    return df


cohort_df = load_cohort_aging(months_back=13, max_age_months=12)
cpa_df = load_reward_cpa()
today = pd.Timestamp(date.today())

if cohort_df.empty:
    placeholder_chart("Value of New Business", "No overlapping activation/revenue data", height=310)
else:
    # LTV proxy: cumulative revenue-per-acquired across every age bucket available for each cohort.
    ltv_by_cohort = cohort_df.groupby("COHORT_MONTH")["REVENUE_PER_ACQUIRED"].sum().sort_index()
    age0_rev = cohort_df[cohort_df["AGE_MONTHS"] == 0].set_index("COHORT_MONTH")["REVENUE"].sort_index()

    this_cohort_month = age0_rev.index.max()
    new_biz_mtd = float(age0_rev.get(this_cohort_month, 0))
    ltv_latest = float(ltv_by_cohort.get(this_cohort_month, 0))

    cpa_series = cpa_df.set_index("MONTH_START")["REWARD_COST_PER_ACT"]
    cpa_latest = float(cpa_series.reindex([this_cohort_month]).iloc[0]) if this_cohort_month in cpa_series.index else 0.0
    ltv_cpa_ratio = (ltv_latest / cpa_latest) if cpa_latest else None

    avg_monthly_rev_per_active = cohort_df[cohort_df["AGE_MONTHS"] > 0]["REVENUE_PER_ACTIVE"].mean()
    months_to_payback = (cpa_latest / avg_monthly_rev_per_active) if avg_monthly_rev_per_active else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("New Business Revenue (latest full cohort)", f"R{new_biz_mtd:,.0f}",
              help=f"Revenue in the acquisition month itself, cohort = {this_cohort_month.strftime('%b %Y') if pd.notna(this_cohort_month) else '—'}")
    k2.metric("LTV Estimate (proxy)", f"R{ltv_latest:,.2f}",
              help="Cumulative revenue-per-acquired across all aging months available so far — not a true lifetime value.")
    k3.metric("LTV / CPA Ratio", f"{ltv_cpa_ratio:.2f}x" if ltv_cpa_ratio else "—",
              help="LTV proxy ÷ reward-based cost per activation.")
    k4.metric("Months to Payback", f"{months_to_payback:.1f}" if months_to_payback else "—",
              help="Reward-based CPA ÷ average monthly revenue per active account (age > 0).")

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    def _base(title=""):
        return dict(
            title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
            yaxis=dict(showgrid=True, gridcolor=BORDER),
            bargap=0.3,
            legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
        )

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        fig = go.Figure(go.Bar(
            x=age0_rev.index.strftime("%b '%y").tolist(), y=age0_rev.tolist(),
            marker_color=SONIC_BLUE, marker_line_width=0,
            hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
        ))
        layout = _base("New Business Value by Cohort Month (acquisition-month revenue)")
        layout["yaxis"]["tickprefix"] = "R"
        layout["yaxis"]["tickformat"] = ",.0f"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        recent_cohorts = sorted(cohort_df["COHORT_MONTH"].unique())[-4:]
        fig2 = go.Figure()
        for i, cm in enumerate(recent_cohorts):
            sub = cohort_df[cohort_df["COHORT_MONTH"] == cm].sort_values("AGE_MONTHS")
            cum = sub["REVENUE_PER_ACQUIRED"].cumsum()
            fig2.add_trace(go.Scatter(
                x=[f"M{a+1}" for a in sub["AGE_MONTHS"]], y=cum.tolist(),
                mode="lines+markers", name=pd.Timestamp(cm).strftime("%b '%y"),
                line=dict(width=2),
            ))
        layout2 = _base("Cumulative Revenue per Acquired — Last 4 Cohorts")
        layout2["yaxis"]["tickprefix"] = "R"
        layout2["yaxis"]["tickformat"] = ",.2f"
        fig2.update_layout(**layout2, hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    c3, c4 = st.columns(2, gap="medium")
    with c3:
        ratio_series = (ltv_by_cohort / cpa_series.reindex(ltv_by_cohort.index)).dropna()
        fig3 = go.Figure(go.Scatter(
            x=ratio_series.index.strftime("%b '%y").tolist(), y=ratio_series.tolist(),
            mode="lines+markers", line=dict(color=ULTRAVIOLET, width=2),
            hovertemplate="%{x}<br><b>%{y:.2f}x</b><extra></extra>",
        ))
        fig3.update_layout(**_base("LTV / CPA Trend by Cohort Month"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with c4:
        payback_series = (cpa_series.reindex(ltv_by_cohort.index) / avg_monthly_rev_per_active).dropna() \
            if avg_monthly_rev_per_active else pd.Series(dtype=float)
        if not payback_series.empty:
            fig4 = go.Figure(go.Bar(
                x=payback_series.index.strftime("%b '%y").tolist(), y=payback_series.tolist(),
                marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
                hovertemplate="%{x}<br><b>%{y:.1f} months</b><extra></extra>",
            ))
            fig4.update_layout(**_base("Estimated Payback Period — by Cohort Month"))
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        else:
            placeholder_chart("Payback Period Trend", "Insufficient overlapping CPA/revenue data", height=310)
