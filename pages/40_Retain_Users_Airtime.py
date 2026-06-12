"""
Retain Users via Free Airtime — Strategy section
Data: UCONNECT_MAY_MERGE_REVENUE (REVENUE_PAID_FOR_REWARDS_VALUE / QUANTITY)
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

st.set_page_config(page_title="Retain Users via Free Airtime | Telco Retail", page_icon="🎁", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Retain Users via Free Airtime", badge="Strategy")

@st.cache_data(ttl=1800, show_spinner="Loading reward data…")
def load_monthly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            SUM(COALESCE(REVENUE_PAID_FOR_REWARDS_QUANTITY,0)) AS REWARD_QTY,
            SUM(COALESCE(REVENUE_PAID_FOR_REWARDS_VALUE,0))    AS REWARD_VALUE
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

df = load_monthly()
df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])

this_m_qty = int(df.iloc[-1]["REWARD_QTY"]) if not df.empty else 0
this_m_val = float(df.iloc[-1]["REWARD_VALUE"]) if not df.empty else 0
last_m_qty = int(df.iloc[-2]["REWARD_QTY"]) if len(df) >= 2 else 0
total_val  = float(df["REWARD_VALUE"].sum()) if not df.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Rewards Paid This Month (Qty)", f"{this_m_qty:,}")
k2.metric("Reward Value This Month", f"R{this_m_val:,.0f}")
k3.metric("Rewards Last Month (Qty)", f"{last_m_qty:,}", delta=f"{this_m_qty-last_m_qty:+,}")
k4.metric("Total Reward Spend (13M)", f"R{total_val:,.0f}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        bargap=0.3,
    )

x = df["MONTH_START"].dt.strftime("%b '%y").tolist()

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure(go.Bar(
        x=x, y=df["REWARD_QTY"].tolist(),
        marker_color=HYPERMINT, marker_line_width=0,
        hovertemplate="%{x}<br><b>Rewards: %{y:,}</b><extra></extra>",
    ))
    fig.update_layout(**_base("Free Airtime Rewards Paid — Monthly Qty (13 months)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Bar(
        x=x, y=df["REWARD_VALUE"].tolist(),
        marker_color=SONIC_BLUE, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    layout2 = _base("Free Airtime Reward Value — Monthly (R)")
    layout2["yaxis"]["tickprefix"] = "R"
    layout2["yaxis"]["tickformat"] = ",.0f"
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    placeholder_chart(
        "Retention Rate for Reward Recipients",
        "CDR / usage + rewards join — pending data access",
        height=300,
    )
with c4:
    placeholder_chart(
        "Reward ROI — Revenue per Reward Recipient",
        "Cohort revenue + REVENUE_PAID_FOR_REWARDS join — pending cohort table",
        height=300,
    )
