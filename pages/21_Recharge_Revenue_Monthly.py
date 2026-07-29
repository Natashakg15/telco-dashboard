"""
Recharge Revenue Monthly — Recharges section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2,
)
from utils.snowflake_conn import run_query

REV_TABLE = "UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE_REVENUE"

st.set_page_config(page_title="Recharge Revenue Monthly | Telco Retail", page_icon="💰", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Recharge Revenue Monthly", badge="Recharges")

@st.cache_data(ttl=1800, show_spinner="Loading revenue data…")
def load_monthly():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', TRANSACTION_DATE) AS MONTH_START,
            SUM(COALESCE(REVENUE_CELLC_RECHARGE_VALUE,0))             AS CELLC,
            SUM(COALESCE(REVENUE_RETAIL_VOUCHER_REDEMPTIONS_VALUE,0)) AS VOUCHER,
            SUM(COALESCE(REVENUE_APP_PURCHASES_VALUE,0))              AS APP,
            SUM(COALESCE(REVENUE_MAY_BILLRUN_VALUE,0))                AS BILLRUN,
            SUM(COALESCE(REVENUE_POST_PAID_SUCCESSFULL_VALUE,0))      AS POSTPAID,
            SUM(COALESCE(REVENUE_MAY_WEBSITE_RECHARGES_VALUE,0))      AS WEBSITE,
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
            ) AS TOTAL_REVENUE
        FROM {REV_TABLE}
        WHERE TRANSACTION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

df = load_monthly()
df["MONTH_START"] = pd.to_datetime(df["MONTH_START"])
x = df["MONTH_START"].dt.strftime("%b '%y").tolist()

this_m_total = float(df.iloc[-1]["TOTAL_REVENUE"]) if not df.empty else 0
last_m_total = float(df.iloc[-2]["TOTAL_REVENUE"]) if len(df) >= 2 else 0
this_m_cellc = float(df.iloc[-1]["CELLC"]) if not df.empty else 0
this_m_app   = float(df.iloc[-1]["APP"])   if not df.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue This Month", f"R{this_m_total:,.0f}")
k2.metric("Total Revenue Last Month", f"R{last_m_total:,.0f}", delta=f"R{this_m_total-last_m_total:+,.0f}")
k3.metric("Cell C Recharge This Month", f"R{this_m_cellc:,.0f}")
k4.metric("App Purchases This Month", f"R{this_m_app:,.0f}")

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
    streams = [
        ("Cell C Recharge", "CELLC", HYPERMINT),
        ("Billrun",         "BILLRUN", SONIC_BLUE),
        ("Postpaid",        "POSTPAID", ULTRAVIOLET),
        ("App",             "APP", HIGHVOLT_ORANGE),
        ("Voucher",         "VOUCHER", "#9b59b6"),
        ("Website",         "WEBSITE", "#1abc9c"),
    ]
    for name, col, colour in streams:
        if col in df.columns:
            fig.add_trace(go.Bar(
                x=x, y=df[col].tolist(),
                name=name, marker_color=colour, marker_line_width=0,
            ))
    fig.update_layout(**_base("Monthly Revenue by Stream (Stacked)"))
    fig.update_layout(barmode="stack")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Bar(
        x=x, y=df["TOTAL_REVENUE"].tolist(),
        marker_color=HYPERMINT, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    fig2.update_layout(**_base("Total Monthly Revenue"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Detail table ──────────────────────────────────────────────────────────────
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin:16px 0 8px 0;'>Monthly Revenue Detail</h3>",
    unsafe_allow_html=True,
)
display = df.copy()
display["MONTH_START"] = display["MONTH_START"].dt.strftime("%b '%y")
cols_show = ["MONTH_START","CELLC","BILLRUN","POSTPAID","APP","VOUCHER","WEBSITE","TOTAL_REVENUE"]
display = display[[c for c in cols_show if c in display.columns]]
rename = {
    "MONTH_START":"Month","CELLC":"Cell C","BILLRUN":"Billrun","POSTPAID":"Postpaid",
    "APP":"App","VOUCHER":"Voucher","WEBSITE":"Website","TOTAL_REVENUE":"Total"
}
display = display.rename(columns=rename).sort_values("Month", ascending=False)
for col in [c for c in display.columns if c != "Month"]:
    display[col] = display[col].apply(lambda v: f"R{float(v):,.0f}" if pd.notna(v) else "—")
st.dataframe(display, use_container_width=True, hide_index=True)
