"""
Revenue Metrics — Financials section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE
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
from utils.page_helpers import placeholder_chart

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"
MERGE_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE"

st.set_page_config(page_title="Revenue Metrics | Telco Retail", page_icon="💰", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Revenue Metrics", badge="Financials")

@st.cache_data(ttl=1800, show_spinner="Loading revenue metrics…")
def load_metrics():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', r.TRANSACTION_DATE) AS MONTH_START,
            SUM(COALESCE(r.REVENUE_CELLC_RECHARGE_VALUE,0)
              + COALESCE(r.REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
              + COALESCE(r.REVENUE_APP_PURCHASES_VALUE,0)
              + COALESCE(r.REVENUE_MAY_BILLRUN_VALUE,0)
              + COALESCE(r.REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)) AS TOTAL_REVENUE,
            COUNT(DISTINCT r.ACCOUNT_NUMBER) AS PAYING_ACCOUNTS
        FROM {REV_TABLE} r
        WHERE r.TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_activations():
    df = run_query(f"""
        SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

metrics = load_metrics()
activations = load_activations()
metrics["MONTH_START"] = pd.to_datetime(metrics["MONTH_START"])
activations["MONTH_START"] = pd.to_datetime(activations["MONTH_START"])

merged = metrics.merge(activations, on="MONTH_START", how="left")
merged["ARPU"] = (merged["TOTAL_REVENUE"] / merged["PAYING_ACCOUNTS"].replace(0, float("nan"))).round(2)
merged["RPU"]  = (merged["TOTAL_REVENUE"] / merged["ACTIVATIONS"].replace(0, float("nan"))).round(2)

x = merged["MONTH_START"].dt.strftime("%b '%y").tolist()

this_m_rev  = float(merged.iloc[-1]["TOTAL_REVENUE"]) if not merged.empty else 0
last_m_rev  = float(merged.iloc[-2]["TOTAL_REVENUE"]) if len(merged) >= 2 else 0
this_m_arpu = float(merged.iloc[-1]["ARPU"]) if not merged.empty else 0
this_m_accs = int(merged.iloc[-1]["PAYING_ACCOUNTS"]) if not merged.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue This Month", f"R{this_m_rev:,.0f}")
k2.metric("vs Last Month", f"R{last_m_rev:,.0f}", delta=f"R{this_m_rev-last_m_rev:+,.0f}")
k3.metric("ARPU This Month", f"R{this_m_arpu:,.2f}")
k4.metric("Paying Accounts This Month", f"{this_m_accs:,}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER),
        bargap=0.3,
    )

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure(go.Bar(
        x=x, y=merged["TOTAL_REVENUE"].tolist(),
        marker_color=HYPERMINT, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    layout = _base("Total Revenue (13 months)")
    layout["yaxis"]["tickprefix"] = "R"
    layout["yaxis"]["tickformat"] = ",.0f"
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=x, y=merged["ARPU"].tolist(), name="ARPU",
        mode="lines+markers", line=dict(color=HYPERMINT, width=2), yaxis="y1",
    ))
    fig2.add_trace(go.Bar(
        x=x, y=merged["PAYING_ACCOUNTS"].tolist(), name="Paying Accounts",
        marker_color=SONIC_BLUE, marker_line_width=0, opacity=0.5, yaxis="y2",
    ))
    fig2.update_layout(
        **_base("ARPU vs Paying Accounts"),
        yaxis=dict(title="ARPU (R)", tickprefix="R", tickformat=",.2f", showgrid=True, gridcolor=BORDER),
        yaxis2=dict(title="Paying Accounts", overlaying="y", side="right", showgrid=False, tickformat=","),
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified", barmode="overlay",
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    fig3 = go.Figure(go.Scatter(
        x=x, y=merged["RPU"].tolist(),
        mode="lines+markers", line=dict(color=ULTRAVIOLET, width=2),
        marker=dict(color=ULTRAVIOLET, size=5),
        hovertemplate="%{x}<br><b>RPU: R%{y:,.2f}</b><extra></extra>",
    ))
    layout3 = _base("Revenue per Activation (RPU)")
    layout3["yaxis"]["tickprefix"] = "R"
    layout3["yaxis"]["tickformat"] = ",.2f"
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    placeholder_chart("Net Revenue (excl. VAT & cost)", "Income Statement / GL data", height=310)
