"""
Income Statement Summary — Financials section
Data: TEST INCOME STATEMENT.xlsx ('Format Is' sheet), SharePoint snapshot — see
utils/financials.py for source/refresh notes.
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
from utils.financials import load_financials, section_total, ytd, SNAPSHOT_DATE, UNVERIFIED_FROM
from utils.page_helpers import placeholder_chart

st.set_page_config(page_title="Income Statement Summary | Telco Retail", page_icon="💰", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Income Statement Summary", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Source: hand-maintained Excel workbook on SharePoint, snapshotted {SNAPSHOT_DATE}. "
    f"No distinct budget series exists in this sheet, so Budget vs Actual is "
    f"<span style='color:{HIGHVOLT_ORANGE};'>still pending</span> a separate budget source.</p>",
    unsafe_allow_html=True,
)

df = load_financials()
today = pd.Timestamp(date.today())

revenue  = section_total(df, "Revenue")
gp       = section_total(df, "Gross Profit")
ebitda_bs = section_total(df, "EBITDA before SAC")
reported = section_total(df, "Reported EBITDA")

ytd_rev, ytd_gp = ytd(revenue, today), ytd(gp, today)
ytd_ebitda, ytd_rep = ytd(ebitda_bs, today), ytd(reported, today)

k1, k2, k3, k4 = st.columns(4)
k1.metric("YTD Revenue", f"R{ytd_rev:,.0f}", help=f"Jan–{today.strftime('%b %Y')}")
k2.metric("YTD Gross Profit", f"R{ytd_gp:,.0f}")
k3.metric("YTD EBITDA before SAC", f"R{ytd_ebitda:,.0f}")
k4.metric("YTD Reported EBITDA", f"R{ytd_rep:,.0f}")

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
    year_start = pd.Timestamp(year=today.year, month=1, day=1)
    cal_ytd = revenue[(revenue.index >= year_start) & (revenue.index <= today)]
    gp_ytd_s = gp[(gp.index >= year_start) & (gp.index <= today)]
    x_cal = cal_ytd.index.strftime("%b").tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_cal, y=cal_ytd.tolist(), name="Revenue",
        marker_color=SONIC_BLUE, marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        x=x_cal, y=gp_ytd_s.reindex(cal_ytd.index, fill_value=0).tolist(), name="Gross Profit",
        marker_color=HYPERMINT, marker_line_width=0,
    ))
    fig.update_layout(**_base(f"YTD P&L Summary — {today.year}"), barmode="group")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    placeholder_chart(
        "Budget vs Actual", "No budget series in this workbook — needs a separate budget source",
        height=310,
    )
