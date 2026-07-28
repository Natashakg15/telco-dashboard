"""
Subscriptions — Subscriptions section
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA
Filter: CHANNEL (closest match to PBIX: Telesales → AFFINITY/DISTRIBUTION, App → ONLINE, Mobile Store → MOBILE STORE)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2, CHART_PALETTE,
)
from utils.snowflake_conn import run_query
from utils.page_helpers import placeholder_chart

BILLING_TABLE = "UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA"

CHANNEL_GROUPS = {
    "Mobile Store":       ["MOBILE STORE"],
    "Distribution":       ["DISTRIBUTION"],
    "Online / App":       ["ONLINE"],
    "Financial Services": ["FINANCIAL SERVICES"],
    "Affinity":           ["AFFINITY"],
    "NRP":                ["NRP"],
    "Other":              ["-", "UNKNOWN", "AUDIT", "TEST", "MOBIUS", "MR PRICE", "ON AIR FIBRE"],
}

st.set_page_config(page_title="Subscriptions | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions", badge="Subscriptions")

with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Channel</div>",
        unsafe_allow_html=True,
    )
    sel_channels = st.multiselect(
        "Channel groups",
        list(CHANNEL_GROUPS.keys()),
        default=[],
        placeholder="All channels",
        label_visibility="collapsed",
    )

# Build WHERE clause
if sel_channels:
    raw = [ch for g in sel_channels for ch in CHANNEL_GROUPS[g]]
    where = f"AND UPPER(CHANNEL) IN ({', '.join(repr(r) for r in raw)})"
else:
    where = ""

@st.cache_data(ttl=1800, show_spinner="Loading subscription data…")
def load_monthly(w: str):
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', BILLINGDATE) AS MONTH_START,
            COALESCE(UPPER(CHANNEL),'UNKNOWN') AS CHANNEL,
            SUM(BILLED_COUNT) AS BILLED,
            SUM(PAID_COUNT) AS PAID,
            SUM(BILLED_AMOUNT_EXCL_VAT) AS BILLED_AMT,
            SUM(PAID_AMOUNT_EXCL_VAT) AS PAID_AMT
        FROM {BILLING_TABLE}
        WHERE ORGANIZATION = 'uconnect'
          AND BILLINGDATE >= DATEADD(month,-13,CURRENT_DATE())
          AND BILLINGDATE IS NOT NULL
          {w}
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_kpis(w: str):
    df = run_query(f"""
        SELECT
            SUM(CASE WHEN DATE_TRUNC('month',BILLINGDATE)=DATE_TRUNC('month',CURRENT_DATE()) THEN BILLED_COUNT ELSE 0 END) AS BILLED_MTD,
            SUM(CASE WHEN DATE_TRUNC('month',BILLINGDATE)=DATE_TRUNC('month',CURRENT_DATE()) THEN PAID_COUNT ELSE 0 END) AS PAID_MTD,
            SUM(CASE WHEN DATE_TRUNC('month',BILLINGDATE)=DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE())) THEN BILLED_COUNT ELSE 0 END) AS BILLED_LM,
            SUM(CASE WHEN DATE_TRUNC('month',BILLINGDATE)=DATE_TRUNC('month',CURRENT_DATE()) THEN BILLED_AMOUNT_EXCL_VAT ELSE 0 END) AS AMT_MTD
        FROM {BILLING_TABLE}
        WHERE ORGANIZATION = 'uconnect'
          AND BILLINGDATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
          {w}
    """)
    df.columns = [c.upper() for c in df.columns]
    return df.iloc[0] if not df.empty else {}

kpis    = load_kpis(where)
monthly = load_monthly(where)
monthly["MONTH_START"] = pd.to_datetime(monthly["MONTH_START"])

billed_mtd = int(kpis.get("BILLED_MTD") or 0)
paid_mtd   = int(kpis.get("PAID_MTD") or 0)
billed_lm  = int(kpis.get("BILLED_LM") or 0)
amt_mtd    = float(kpis.get("AMT_MTD") or 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Billed This Month", f"{billed_mtd:,}")
k2.metric("Paid This Month", f"{paid_mtd:,}")
k3.metric("Billed Last Month", f"{billed_lm:,}", delta=f"{billed_mtd-billed_lm:+,}")
k4.metric("Billed Amount MTD", f"R{amt_mtd:,.0f}")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

def _base(title="", barmode="stack"):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickformat=","),
        bargap=0.3, barmode=barmode,
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )

c1, c2 = st.columns(2, gap="medium")

with c1:
    pivot = monthly.pivot_table(index="MONTH_START", columns="CHANNEL", values="BILLED", fill_value=0)
    fig = go.Figure()
    for i, col in enumerate(pivot.columns):
        fig.add_trace(go.Bar(
            x=pivot.index.strftime("%b '%y").tolist(), y=pivot[col].tolist(),
            name=col, marker_color=CHART_PALETTE[i % len(CHART_PALETTE)], marker_line_width=0,
        ))
    fig.update_layout(**_base("Monthly Billed Subscriptions by Channel"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    monthly_totals = monthly.groupby("MONTH_START").agg({"BILLED": "sum", "PAID": "sum"}).reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=monthly_totals["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly_totals["BILLED"].tolist(),
        name="Billed", marker_color=SONIC_BLUE, marker_line_width=0,
    ))
    fig2.add_trace(go.Bar(
        x=monthly_totals["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly_totals["PAID"].tolist(),
        name="Paid", marker_color=HYPERMINT, marker_line_width=0,
    ))
    fig2.update_layout(**_base("Billed vs Paid Subscriptions", barmode="group"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    monthly_totals["COLLECTION_RATE"] = (
        monthly_totals["PAID"] / monthly_totals["BILLED"].replace(0, float("nan")) * 100
    ).round(1)
    fig3 = go.Figure(go.Scatter(
        x=monthly_totals["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly_totals["COLLECTION_RATE"].tolist(),
        mode="lines+markers",
        line=dict(color=HYPERMINT, width=2), marker=dict(color=HYPERMINT, size=5),
        hovertemplate="%{x}<br><b>Collection Rate: %{y:.1f}%</b><extra></extra>",
    ))
    layout3 = _base("Collection Rate (Paid / Billed %)")
    layout3["yaxis"] = dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", range=[0, 105])
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    placeholder_chart(
        "Subscriptions by Sub-Channel (Telesales / App / WhatsApp / BTL / DigiM VAS)",
        "SOURCE/CHANNEL breakdown not matched in VW_SPOT_BILLING_DATA — pending mapping",
        height=310,
    )
