"""
Forward 12 & Trailing 12 — Financials section
Trailing 12: actual revenue from UCONNECT_MAY_MERGE_REVENUE
Forward 12: straight-line projection (placeholder) pending budget/forecast data
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
from utils.snowflake_conn import run_query
from utils.page_helpers import placeholder_chart

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Forward 12 & Trailing 12 | Telco Retail", page_icon="📅", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Forward 12 & Trailing 12", badge="Financials")

@st.cache_data(ttl=1800, show_spinner="Loading trailing revenue…")
def load_trailing():
    df = run_query(f"""
        -- REVENUE_WHATSAPP_PURCHASES_VALUE excluded: corrupted for every row of
        -- WALLET='Recharge Wallet - Customer WhatsApp purchases' (~1e18-1e19 magnitude,
        -- confirmed 2023-09 through 2026-07) - needs an upstream ETL fix first.
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            SUM(COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0)
              + COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)
              + COALESCE(REVENUE_APP_PURCHASES_VALUE,0)
              + COALESCE(REVENUE_MAY_BILLRUN_VALUE,0)
              + COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0)) AS TOTAL_REVENUE
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-12,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

trailing = load_trailing()
trailing["MONTH_START"] = pd.to_datetime(trailing["MONTH_START"])

trailing_12_total = float(trailing["TOTAL_REVENUE"].sum()) if not trailing.empty else 0
avg_monthly       = float(trailing["TOTAL_REVENUE"].mean()) if not trailing.empty else 0
last_m_rev        = float(trailing.iloc[-1]["TOTAL_REVENUE"]) if not trailing.empty else 0
fwd_12_proj       = avg_monthly * 12

k1, k2, k3, k4 = st.columns(4)
k1.metric("Trailing 12M Total", f"R{trailing_12_total:,.0f}")
k2.metric("Monthly Average (T12)", f"R{avg_monthly:,.0f}")
k3.metric("Forward 12M Projection", f"R{fwd_12_proj:,.0f}", help="Straight-line projection based on T12 average. Pending budget data.")
k4.metric("Last Month Revenue", f"R{last_m_rev:,.0f}")

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
    x_trailing = trailing["MONTH_START"].dt.strftime("%b '%y").tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_trailing, y=trailing["TOTAL_REVENUE"].tolist(),
        name="Actual Revenue",
        marker_color=SONIC_BLUE, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    # Add average line
    if avg_monthly:
        fig.add_trace(go.Scatter(
            x=x_trailing, y=[avg_monthly] * len(x_trailing),
            name="12M Average",
            mode="lines", line=dict(color=HYPERMINT, width=1.5, dash="dash"),
        ))
    fig.update_layout(**_base("Trailing 12 Months — Actual Revenue"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    # Forward 12: straight-line from avg + last point trend
    if not trailing.empty:
        last_date = trailing["MONTH_START"].max()
        fwd_dates = pd.date_range(last_date + pd.DateOffset(months=1), periods=12, freq="MS")
        # Simple linear trend from last 3 months
        last3 = trailing.tail(3)["TOTAL_REVENUE"].values
        if len(last3) >= 2:
            trend = (last3[-1] - last3[0]) / max(len(last3) - 1, 1)
        else:
            trend = 0
        fwd_vals = [max(0, last_m_rev + trend * (i + 1)) for i in range(12)]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=fwd_dates.strftime("%b '%y").tolist(), y=fwd_vals,
            name="Projected Revenue",
            marker_color=HYPERMINT, marker_line_width=0, opacity=0.6,
            hovertemplate="%{x}<br><b>Proj: R%{y:,.0f}</b><extra></extra>",
        ))
        fig2.add_annotation(
            text="⚠ Straight-line projection — pending budget/forecast data",
            xref="paper", yref="paper", x=0.5, y=1.05, showarrow=False,
            font=dict(color=HIGHVOLT_ORANGE, size=11),
        )
        layout2 = _base("Forward 12 Months — Straight-Line Projection")
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    else:
        placeholder_chart("Forward 12 Months", "Revenue forecast / budget data", height=310)

# ── Combined T12 + F12 ────────────────────────────────────────────────────────
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin:16px 0 8px 0;'>Combined View</h3>",
    unsafe_allow_html=True,
)
if not trailing.empty:
    last_date = trailing["MONTH_START"].max()
    fwd_dates = pd.date_range(last_date + pd.DateOffset(months=1), periods=12, freq="MS")
    last3 = trailing.tail(3)["TOTAL_REVENUE"].values
    trend = (last3[-1] - last3[0]) / max(len(last3) - 1, 1) if len(last3) >= 2 else 0
    fwd_vals = [max(0, last_m_rev + trend * (i + 1)) for i in range(12)]

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=trailing["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=trailing["TOTAL_REVENUE"].tolist(),
        name="Actual (T12)", marker_color=SONIC_BLUE, marker_line_width=0,
    ))
    fig3.add_trace(go.Bar(
        x=fwd_dates.strftime("%b '%y").tolist(), y=fwd_vals,
        name="Projected (F12)", marker_color=HYPERMINT, marker_line_width=0, opacity=0.5,
    ))
    layout3 = _base("Trailing 12 + Forward 12 Combined")
    layout3["barmode"] = "group"
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
