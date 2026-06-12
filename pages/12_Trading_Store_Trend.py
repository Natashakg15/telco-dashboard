"""
Trading Store Trend — Sales section
Data: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE
"Trading stores" = F2F (face-to-face) retail channel
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, SURFACE_2,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

st.set_page_config(page_title="Trading Store Trend | Telco Retail", page_icon="🏪", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Trading Store Trend", badge="Sales")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Channel Filter</div>",
        unsafe_allow_html=True,
    )
    channels = st.multiselect(
        "Sales channel",
        ["F2F", "Telesales", "Digital", "OTHER"],
        default=["F2F"],
        label_visibility="collapsed",
    )

where = ""
if channels:
    vals = ", ".join(repr(c) for c in channels)
    where = f"AND SALES_CHANNEL IN ({vals})"

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner="Loading trading store data…")
def load_monthly(w: str):
    df = run_query(f"""
        SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE()) {w}
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_weekly(w: str):
    df = run_query(f"""
        SELECT DATE_TRUNC('week', ACTIVATION_DATE) AS WEEK_START, COUNT(*) AS CNT
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(week,-26,CURRENT_DATE()) {w}
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_top_tenants(w: str):
    df = run_query(f"""
        SELECT TENANT,
            SUM(CASE WHEN DATE_TRUNC('month',ACTIVATION_DATE)=DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS THIS_MONTH,
            SUM(CASE WHEN DATE_TRUNC('month',ACTIVATION_DATE)=DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE())) THEN 1 ELSE 0 END) AS LAST_MONTH
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
          AND TENANT IS NOT NULL {w}
        GROUP BY 1 ORDER BY THIS_MONTH DESC
        LIMIT 20
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_kpis(w: str):
    df = run_query(f"""
        SELECT
            SUM(CASE WHEN ACTIVATION_DATE >= DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS THIS_MONTH,
            SUM(CASE WHEN ACTIVATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE()))
                          AND ACTIVATION_DATE < DATE_TRUNC('month',CURRENT_DATE()) THEN 1 ELSE 0 END) AS LAST_MONTH,
            SUM(CASE WHEN ACTIVATION_DATE >= CURRENT_DATE()-6 THEN 1 ELSE 0 END) AS LAST_7
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATE_TRUNC('month',DATEADD(month,-1,CURRENT_DATE())) {w}
    """)
    df.columns = [c.upper() for c in df.columns]
    return df.iloc[0] if not df.empty else {}

kpis      = load_kpis(where)
monthly   = load_monthly(where)
weekly    = load_weekly(where)
tenants   = load_top_tenants(where)

monthly["MONTH_START"] = pd.to_datetime(monthly["MONTH_START"])
weekly["WEEK_START"]   = pd.to_datetime(weekly["WEEK_START"])

this_m = int(kpis.get("THIS_MONTH") or 0)
last_m = int(kpis.get("LAST_MONTH") or 0)
last_7 = int(kpis.get("LAST_7") or 0)

# ── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("This Month", f"{this_m:,}")
k2.metric("Last Month", f"{last_m:,}", delta=f"{this_m-last_m:+,}")
k3.metric("Last 7 Days", f"{last_7:,}")
k4.metric("Active Channels", ", ".join(channels) if channels else "All")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, linecolor="rgba(0,0,0,0)", tickformat=","),
        bargap=0.3,
    )

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure(go.Bar(
        x=monthly["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly["CNT"].tolist(),
        marker_color=SONIC_BLUE, marker_line_width=0,
        hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
    ))
    fig.update_layout(**_base("Monthly Activations — Trading Stores (13 months)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Bar(
        x=weekly["WEEK_START"].dt.strftime("Wk %d %b '%y").tolist(),
        y=weekly["CNT"].tolist(),
        marker_color=HYPERMINT, marker_line_width=0,
        hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
    ))
    fig2.update_layout(**_base("Weekly Activations — Trading Stores (26 weeks)"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Tenant table ──────────────────────────────────────────────────────────────
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin:16px 0 8px 0;'>Top Stores by Activations</h3>",
    unsafe_allow_html=True,
)
if not tenants.empty:
    rows_html = ""
    for i, row in enumerate(tenants.itertuples(), 1):
        delta = int(row.THIS_MONTH) - int(row.LAST_MONTH)
        delta_color = HYPERMINT if delta >= 0 else HIGHVOLT_ORANGE
        delta_str = f"+{delta:,}" if delta >= 0 else f"{delta:,}"
        rows_html += (
            f"<tr>"
            f"<td style='padding:6px 10px;color:#555;font-size:12px;'>{i}.</td>"
            f"<td style='padding:6px 10px;color:{ZERO_WHITE};font-size:13px;'>{row.TENANT}</td>"
            f"<td style='padding:6px 10px;color:{HYPERMINT};font-weight:600;font-size:13px;text-align:right;'>{int(row.THIS_MONTH):,}</td>"
            f"<td style='padding:6px 10px;color:{SONIC_BLUE};font-size:13px;text-align:right;'>{int(row.LAST_MONTH):,}</td>"
            f"<td style='padding:6px 10px;color:{delta_color};font-size:13px;text-align:right;'>{delta_str}</td>"
            f"</tr>"
        )
    header = "".join(
        f"<th style='padding:8px 10px;background:{SURFACE_2};color:#555;font-size:11px;text-align:{'left' if i<2 else 'right'};'>{h}</th>"
        for i,h in enumerate(["#","Store","This Month","Last Month","Δ"])
    )
    st.markdown(
        f"<div style='overflow-x:auto;'>"
        f"<table style='width:100%;border-collapse:collapse;background:{SURFACE_1};border-radius:10px;overflow:hidden;'>"
        f"<thead><tr>{header}</tr></thead><tbody>{rows_html}</tbody></table></div>",
        unsafe_allow_html=True,
    )
else:
    st.info("No store data for selected channels.")
