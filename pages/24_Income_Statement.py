"""
Income Statement — Financials section
Data: TEST INCOME STATEMENT.xlsx ('Format Is' sheet), SharePoint snapshot — see
utils/financials.py for source/refresh notes and the Mar-2027+ data caveat.
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
from utils.financials import (
    load_financials, section_total, line, latest_two, SNAPSHOT_DATE, UNVERIFIED_FROM,
)

st.set_page_config(page_title="Income Statement | Telco Retail", page_icon="💰", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Income Statement", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Source: hand-maintained Excel workbook on SharePoint, snapshotted {SNAPSHOT_DATE} — "
    f"not yet a live connection, won't auto-refresh. Months from "
    f"{UNVERIFIED_FROM.strftime('%b %Y')} onward look like a stale/different budget "
    f"scenario (Reported EBITDA jumps to a much larger, steadily worsening loss) — "
    f"treat those as <span style='color:{HIGHVOLT_ORANGE};'>unverified</span>, not fact.</p>",
    unsafe_allow_html=True,
)

df = load_financials()
today = pd.Timestamp(date.today())

revenue   = section_total(df, "Revenue")
cos       = section_total(df, "Cost of Sales")
gp        = section_total(df, "Gross Profit")
opex      = section_total(df, "Opex")
ebitda_bs = section_total(df, "EBITDA before SAC")
acq       = section_total(df, "Acqusition Cost")
reported  = section_total(df, "Reported EBITDA")

rev_this, rev_last     = latest_two(revenue, today)
gp_this, gp_last       = latest_two(gp, today)
ebitda_this, ebitda_last = latest_two(ebitda_bs, today)
rep_this, rep_last     = latest_two(reported, today)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Revenue", f"R{rev_this:,.0f}", delta=f"R{rev_this-rev_last:+,.0f} vs last month")
k2.metric("Gross Profit", f"R{gp_this:,.0f}", delta=f"R{gp_this-gp_last:+,.0f} vs last month")
k3.metric("EBITDA before SAC", f"R{ebitda_this:,.0f}", delta=f"R{ebitda_this-ebitda_last:+,.0f} vs last month")
k4.metric("Reported EBITDA", f"R{rep_this:,.0f}", delta=f"R{rep_this-rep_last:+,.0f} vs last month")

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


# Trim the trend charts to actual + near-term months, leaving the unverified
# tail out of the default view rather than presenting it as if it were solid.
trend_cutoff = min(today + pd.DateOffset(months=6), UNVERIFIED_FROM - pd.DateOffset(months=1))
rev_t   = revenue[revenue.index <= trend_cutoff].tail(24)
gp_t    = gp[gp.index <= trend_cutoff].tail(24)
rep_t   = reported[reported.index <= trend_cutoff].tail(24)
x_trend = rev_t.index.strftime("%b '%y").tolist()

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_trend, y=rev_t.tolist(), name="Revenue",
        marker_color=SONIC_BLUE, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x_trend, y=gp_t.reindex(rev_t.index, fill_value=0).tolist(), name="Gross Profit",
        mode="lines+markers", line=dict(color=HYPERMINT, width=2),
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    fig.update_layout(**_base("Revenue vs Gross Profit — Monthly"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    latest_month = revenue[revenue.index <= today].index.max()
    if pd.notna(latest_month) and latest_month <= UNVERIFIED_FROM:
        # Cost of Sales / Opex / Acquisition Cost are stored as positive magnitudes
        # in the sheet (Revenue - CoS = Gross Profit exactly) - negate for the waterfall.
        wf_rev  = float(revenue.get(latest_month, 0))
        wf_cos  = -float(cos.get(latest_month, 0))
        wf_opex = -float(opex.get(latest_month, 0))
        wf_acq  = -float(acq.get(latest_month, 0))
        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "total", "relative", "total", "relative", "total"],
            x=["Revenue", "Cost of Sales", "Gross Profit", "Opex", "EBITDA before SAC",
               "Acquisition Cost", "Reported EBITDA"],
            y=[wf_rev, wf_cos, 0, wf_opex, 0, wf_acq, 0],
            connector=dict(line=dict(color=BORDER)),
            increasing=dict(marker=dict(color=HYPERMINT)),
            decreasing=dict(marker=dict(color=HIGHVOLT_ORANGE)),
            totals=dict(marker=dict(color=SONIC_BLUE)),
        ))
        fig_wf.update_layout(**_base(f"P&L Waterfall — {latest_month.strftime('%b %Y')}"))
        st.plotly_chart(fig_wf, use_container_width=True, config={"displayModeBar": False})
    else:
        st.caption("Waterfall unavailable for the latest data point — falls in the unverified range.")

c3, c4 = st.columns(2, gap="medium")
with c3:
    fig3 = go.Figure(go.Scatter(
        x=x_trend, y=rep_t.reindex(rev_t.index, fill_value=0).tolist(),
        mode="lines+markers", line=dict(color=ULTRAVIOLET, width=2),
        fill="tozeroy", fillcolor="rgba(82,190,192,0.08)",
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    fig3.update_layout(**_base("Reported EBITDA — Monthly Trend"))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    gp_pct_full = line(df, "GP %") * 100
    gp_pct = gp_pct_full[gp_pct_full.index <= trend_cutoff].tail(24)
    fig4 = go.Figure(go.Scatter(
        x=x_trend, y=gp_pct.reindex(rev_t.index).tolist(),
        mode="lines+markers", line=dict(color=HYPERMINT, width=2),
        hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>",
    ))
    layout4 = _base("Gross Profit % — Monthly Trend")
    layout4["yaxis"] = dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", tickformat=",.1f")
    fig4.update_layout(**layout4)
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
with st.expander("Full monthly P&L detail"):
    detail_df = pd.DataFrame({
        "Revenue": revenue, "Cost of Sales": cos, "Gross Profit": gp,
        "Opex": opex, "EBITDA before SAC": ebitda_bs,
        "Acquisition Cost": acq, "Reported EBITDA": reported,
    }).sort_index()
    detail_df.index = detail_df.index.strftime("%b %Y")
    st.dataframe(detail_df.style.format("R{:,.0f}"), use_container_width=True)
