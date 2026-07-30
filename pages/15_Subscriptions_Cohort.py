"""
Subscriptions Cohort Analysis — Subscriptions section
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA
Filter: CHANNEL (Telesales Billed/Paid, App Billed/Paid)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, BORDER, ZERO_WHITE, CHART_PALETTE, hex_to_rgba,
)
from utils.snowflake_conn import run_query
from utils.page_helpers import placeholder_chart

BILLING_TABLE = "UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA"

st.set_page_config(page_title="Subscriptions Cohort | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions Cohort Analysis", badge="Subscriptions")

with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Channel</div>",
        unsafe_allow_html=True,
    )
    sel_channels = st.multiselect(
        "Channels",
        ["MOBILE STORE", "DISTRIBUTION", "ONLINE", "FINANCIAL SERVICES", "AFFINITY", "NRP"],
        default=[],
        placeholder="All channels",
        label_visibility="collapsed",
    )

where = ""
if sel_channels:
    vals = ", ".join(repr(c) for c in sel_channels)
    where = f"AND UPPER(CHANNEL) IN ({vals})"

@st.cache_data(ttl=1800, show_spinner="Loading cohort data…")
def load_cohort(w: str):
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', SALESDATE) AS ACQUIRED_MONTH,
            DATE_TRUNC('month', BILLINGDATE) AS BILLING_MONTH,
            SUM(BILLED_COUNT) AS BILLED,
            SUM(PAID_COUNT) AS PAID,
            SUM(BILLED_AMOUNT_EXCL_VAT) AS BILLED_AMT,
            SUM(PAID_AMOUNT_EXCL_VAT) AS PAID_AMT
        FROM {BILLING_TABLE}
        WHERE ORGANIZATION = 'uconnect'
          AND SALESDATE >= DATEADD(month,-12,CURRENT_DATE())
          AND BILLINGDATE >= DATEADD(month,-12,CURRENT_DATE())
          AND SALESDATE IS NOT NULL
          AND BILLINGDATE IS NOT NULL
          {w}
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def load_monthly_trend(w: str):
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', BILLINGDATE) AS MONTH_START,
            UPPER(COALESCE(CHANNEL,'UNKNOWN')) AS CHANNEL,
            SUM(BILLED_COUNT) AS BILLED,
            SUM(PAID_COUNT) AS PAID
        FROM {BILLING_TABLE}
        WHERE ORGANIZATION = 'uconnect'
          AND BILLINGDATE >= DATEADD(month,-13,CURRENT_DATE())
          {w}
        GROUP BY 1,2 ORDER BY 1,2
    """)
    df.columns = [c.upper() for c in df.columns]
    return df

cohort  = load_cohort(where)
monthly = load_monthly_trend(where)

cohort["ACQUIRED_MONTH"]  = pd.to_datetime(cohort["ACQUIRED_MONTH"])
cohort["BILLING_MONTH"]   = pd.to_datetime(cohort["BILLING_MONTH"])
monthly["MONTH_START"]    = pd.to_datetime(monthly["MONTH_START"])

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
    if not monthly.empty:
        pivot = monthly.pivot_table(index="MONTH_START", columns="CHANNEL", values="BILLED", fill_value=0)
        fig = go.Figure()
        for i, col in enumerate(pivot.columns):
            fig.add_trace(go.Bar(
                x=pivot.index.strftime("%b '%y").tolist(), y=pivot[col].tolist(),
                name=col, marker_color=CHART_PALETTE[i % len(CHART_PALETTE)], marker_line_width=0,
            ))
        layout = _base("Monthly Billed Subscriptions by Channel")
        layout["barmode"] = "stack"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No billing data for selected channels.")

with c2:
    if not cohort.empty:
        # Cohort retention: by acquired month, how many were still billed in subsequent months
        cohort_pivot = cohort.pivot_table(
            index="ACQUIRED_MONTH", columns="BILLING_MONTH", values="BILLED", fill_value=0
        )
        fig2 = go.Figure(go.Heatmap(
            z=cohort_pivot.values.tolist(),
            x=cohort_pivot.columns.strftime("%b '%y").tolist(),
            y=cohort_pivot.index.strftime("%b '%y").tolist(),
            colorscale=[[0, "rgba(0,0,0,0)"], [0.5, hex_to_rgba(SONIC_BLUE, 0.6)], [1, HYPERMINT]],
            hovertemplate="Acquired: %{y}<br>Billed: %{x}<br><b>Count: %{z:,}</b><extra></extra>",
            showscale=True,
        ))
        layout2 = dict(
            title=dict(text="Cohort Retention Heatmap (Billed Count)", font=dict(color=ZERO_WHITE, size=14), x=0),
            paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
            font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
            xaxis=dict(tickfont=dict(size=9, color="#888")),
            yaxis=dict(tickfont=dict(size=9, color="#888")),
        )
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    else:
        placeholder_chart("Cohort Retention Heatmap", "No cohort data", height=310)

c3, c4 = st.columns(2, gap="medium")
with c3:
    placeholder_chart(
        "Telesales Billed / Paid Cohort",
        "Telesales channel not identified in VW_SPOT_BILLING_DATA — pending CHANNEL mapping",
        height=300,
    )
with c4:
    placeholder_chart(
        "App Billed / Paid Cohort",
        "App channel mapping pending — ONLINE may be the equivalent",
        height=300,
    )
