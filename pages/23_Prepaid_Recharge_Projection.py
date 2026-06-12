"""
Prepaid Recharge Projection — Recharges section
Actual: VW_CELLC_RECHARGES; Forward: straight-line projection (pending forecast data)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE,
)
from utils.snowflake_conn import run_query
from utils.page_helpers import placeholder_chart

RECHARGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_CELLC_RECHARGES"

st.set_page_config(page_title="Prepaid Recharge Projection | Telco Retail", page_icon="📊", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Prepaid Recharge Projection", badge="Recharges")

@st.cache_data(ttl=1800, show_spinner="Loading recharge history…")
def load_monthly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            COUNT(*) AS QTY,
            SUM(VALUE) AS TOTAL_VALUE
        FROM {RECHARGE_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-12,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

df = load_monthly()
df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])

avg_qty = float(df["QTY"].mean()) if not df.empty else 0
avg_val = float(df["TOTAL_VALUE"].mean()) if not df.empty else 0
last_m_qty = int(df.iloc[-1]["QTY"]) if not df.empty else 0
last_m_val = float(df.iloc[-1]["TOTAL_VALUE"]) if not df.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Recharges Last Month", f"{last_m_qty:,}")
k2.metric("Revenue Last Month", f"R{last_m_val:,.0f}")
k3.metric("12M Avg Qty/Month", f"{avg_qty:,.0f}")
k4.metric("12M Avg Revenue/Month", f"R{avg_val:,.0f}")

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
        x=df["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=df["QTY"].tolist(),
        name="Actual",
        marker_color=SONIC_BLUE, marker_line_width=0,
    ))
    # Projection
    if not df.empty:
        last_date = df["MONTH_START"].max()
        fwd = pd.date_range(last_date + pd.DateOffset(months=1), periods=6, freq="MS")
        last3 = df.tail(3)["QTY"].values
        trend = (last3[-1] - last3[0]) / max(len(last3) - 1, 1) if len(last3) >= 2 else 0
        proj = [max(0, last_m_qty + trend * (i + 1)) for i in range(6)]
        fig.add_trace(go.Bar(
            x=fwd.strftime("%b '%y").tolist(), y=proj,
            name="Projected", marker_color=HYPERMINT, marker_line_width=0, opacity=0.5,
        ))
    layout = _base("Prepaid Recharge Qty — Actual + 6-Month Projection")
    layout["barmode"] = "group"
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=df["TOTAL_VALUE"].tolist(),
        name="Actual",
        marker_color=SONIC_BLUE, marker_line_width=0,
    ))
    if not df.empty:
        last_date = df["MONTH_START"].max()
        fwd = pd.date_range(last_date + pd.DateOffset(months=1), periods=6, freq="MS")
        last3v = df.tail(3)["TOTAL_VALUE"].values
        trend_v = (last3v[-1] - last3v[0]) / max(len(last3v) - 1, 1) if len(last3v) >= 2 else 0
        proj_v = [max(0, last_m_val + trend_v * (i + 1)) for i in range(6)]
        fig2.add_trace(go.Bar(
            x=fwd.strftime("%b '%y").tolist(), y=proj_v,
            name="Projected", marker_color=HYPERMINT, marker_line_width=0, opacity=0.5,
        ))
    layout2 = _base("Recharge Revenue — Actual + 6-Month Projection")
    layout2["barmode"] = "group"
    layout2["yaxis"]["tickprefix"] = "R"
    layout2["yaxis"]["tickformat"] = ",.0f"
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.markdown(
    f"<p style='color:{HIGHVOLT_ORANGE}; font-size:11px; margin-top:4px;'>"
    f"⚠ Projection uses straight-line trend from last 3 months. "
    f"Pending connection to budget / forecasting data for model-based projections.</p>",
    unsafe_allow_html=True,
)
