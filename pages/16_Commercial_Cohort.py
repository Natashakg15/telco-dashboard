"""
Commercial Cohort Analysis — Commercial section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE + UCONNECT_MAY_MERGE_REVENUE
Revenue Cohort, Cohort 1/2/3 Acquired & Active SIMs
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
from utils.page_helpers import placeholder_chart

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Commercial Cohort | Telco Retail", page_icon="💼", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Commercial Cohort Analysis", badge="Commercial")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Activation cohort view from UCONNECT_MAY_MERGE. "
    f"Revenue Cohort tables (Cohort 1/2/3) require a dedicated cohort revenue source — "
    f"<span style='color:{HIGHVOLT_ORANGE};'>pending data access.</span></p>",
    unsafe_allow_html=True,
)

@st.cache_data(ttl=1800, show_spinner="Loading cohort data…")
def load_acquisitions():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', ACTIVATION_DATE) AS ACQ_MONTH,
            COUNT(*) AS ACQUIRED,
            SUM(CASE WHEN TERMINATION_DATE IS NULL THEN 1 ELSE 0 END) AS STILL_ACTIVE
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-12,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_revenue_per_cohort():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', m.ACTIVATION_DATE) AS ACQ_MONTH,
            SUM(COALESCE(r.REVENUE_CELLC_RECHARGE_VALUE,0)
              + COALESCE(r.REVENUE_APP_PURCHASES_VALUE,0)
              + COALESCE(r.REVENUE_MAY_BILLRUN_VALUE,0)
              + COALESCE(r.REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)) AS TOTAL_REVENUE,
            COUNT(DISTINCT m.ACCOUNT_NUMBER) AS ACCOUNTS
        FROM {MERGE_TABLE} m
        JOIN {REV_TABLE} r ON m.ACCOUNT_NUMBER = r.ACCOUNT_NUMBER
        WHERE m.ACTIVATION_DATE >= DATEADD(month,-12,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

acq = load_acquisitions()
rev = load_revenue_per_cohort()

acq["ACQ_MONTH"] = pd.to_datetime(acq["ACQ_MONTH"])
rev["ACQ_MONTH"] = pd.to_datetime(rev["ACQ_MONTH"])

acq["RETENTION_RATE"] = (acq["STILL_ACTIVE"] / acq["ACQUIRED"].replace(0, float("nan")) * 100).round(1)

x_acq = acq["ACQ_MONTH"].dt.strftime("%b '%y").tolist()

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
        x=x_acq, y=acq["ACQUIRED"].tolist(),
        name="Acquired", marker_color=SONIC_BLUE, marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        x=x_acq, y=acq["STILL_ACTIVE"].tolist(),
        name="Still Active", marker_color=HYPERMINT, marker_line_width=0,
    ))
    layout = _base("Acquired vs Still Active SIMs by Cohort Month")
    layout["barmode"] = "group"
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Scatter(
        x=x_acq, y=acq["RETENTION_RATE"].tolist(),
        mode="lines+markers",
        line=dict(color=HYPERMINT, width=2), marker=dict(color=HYPERMINT, size=5),
        hovertemplate="%{x}<br><b>Retention: %{y:.1f}%</b><extra></extra>",
    ))
    layout2 = _base("SIM Retention Rate by Cohort Month (%)")
    layout2["yaxis"] = dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", range=[0, 105])
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    if not rev.empty:
        rev["ARPU"] = (rev["TOTAL_REVENUE"] / rev["ACCOUNTS"].replace(0, float("nan"))).round(2)
        fig3 = go.Figure(go.Bar(
            x=rev["ACQ_MONTH"].dt.strftime("%b '%y").tolist(),
            y=rev["ARPU"].tolist(),
            marker_color=ULTRAVIOLET, marker_line_width=0,
            hovertemplate="%{x}<br><b>ARPU: R%{y:,.2f}</b><extra></extra>",
        ))
        layout3 = _base("Avg Revenue per Acquired SIM by Cohort Month")
        layout3["yaxis"]["tickprefix"] = "R"
        layout3["yaxis"]["tickformat"] = ",.2f"
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        placeholder_chart("ARPU by Cohort Month", "Revenue join returned no data", height=310)

with c4:
    placeholder_chart(
        "Cohort 1 / 2 / 3 — Acquired & Active SIMs",
        "Dedicated COHORT table required — pending data access",
        height=310,
    )
