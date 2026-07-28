"""
Margin Efficiency Metrics — Financials section
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
from utils.financials import load_financials, section_total, line, latest_two, SNAPSHOT_DATE, UNVERIFIED_FROM

st.set_page_config(page_title="Margin Efficiency Metrics | Telco Retail", page_icon="📊", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Margin Efficiency Metrics", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Source: hand-maintained Excel workbook on SharePoint, snapshotted {SNAPSHOT_DATE}. "
    f"The GL stops at EBITDA — there's no D&A/interest/tax breakdown, so a true "
    f"Net Margin % isn't available here; Reported EBITDA Margin % is shown instead.</p>",
    unsafe_allow_html=True,
)

df = load_financials()
today = pd.Timestamp(date.today())

revenue   = section_total(df, "Revenue")
reported  = section_total(df, "Reported EBITDA")
gp_pct    = line(df, "GP %") * 100
service_gp_pct = line(df, "Service GP %") * 100
opex_pct  = line(df, "Fixed Costs/Revenue") * 100
ebitda_margin = (reported / revenue.replace(0, float("nan")) * 100).round(2)

gp_this, gp_last_v = latest_two(gp_pct, today)
svc_this, svc_last = latest_two(service_gp_pct, today)
ebd_this, ebd_last = latest_two(ebitda_margin, today)
opex_this, opex_last = latest_two(opex_pct, today)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Gross Margin %", f"{gp_this:.1f}%", delta=f"{gp_this-gp_last_v:+.1f}pp vs last month")
k2.metric("Service GP %", f"{svc_this:.1f}%", delta=f"{svc_this-svc_last:+.1f}pp vs last month")
k3.metric("Reported EBITDA Margin %", f"{ebd_this:.1f}%", delta=f"{ebd_this-ebd_last:+.1f}pp vs last month")
k4.metric("Opex / Revenue %", f"{opex_this:.1f}%", delta=f"{opex_this-opex_last:+.1f}pp vs last month",
          delta_color="inverse")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)


def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", tickformat=",.1f"),
        bargap=0.3,
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )


trend_cutoff = min(today + pd.DateOffset(months=6), UNVERIFIED_FROM - pd.DateOffset(months=1))
gp_t   = gp_pct[gp_pct.index <= trend_cutoff].tail(13)
svc_t  = service_gp_pct[service_gp_pct.index <= trend_cutoff].tail(13)
ebd_t  = ebitda_margin[ebitda_margin.index <= trend_cutoff].tail(13)
opex_t = opex_pct[opex_pct.index <= trend_cutoff].tail(13)
x_t    = gp_t.index.strftime("%b '%y").tolist()

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_t, y=gp_t.tolist(), name="Gross Margin %",
                              mode="lines+markers", line=dict(color=HYPERMINT, width=2)))
    fig.add_trace(go.Scatter(x=x_t, y=svc_t.reindex(gp_t.index).tolist(), name="Service GP %",
                              mode="lines+markers", line=dict(color=SONIC_BLUE, width=2)))
    fig.add_trace(go.Scatter(x=x_t, y=ebd_t.reindex(gp_t.index).tolist(), name="Reported EBITDA Margin %",
                              mode="lines+markers", line=dict(color=ULTRAVIOLET, width=2)))
    fig.update_layout(**_base("Margin % Trends (13 months)"), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Bar(
        x=x_t, y=opex_t.tolist(), marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
        hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>",
    ))
    fig2.update_layout(**_base("Opex as % of Revenue — Monthly"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
