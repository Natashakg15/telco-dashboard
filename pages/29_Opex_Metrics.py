"""
Opex Metrics — Financials section
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
    SURFACE_1, BORDER, ZERO_WHITE, CHART_PALETTE,
)
from utils.financials import (
    load_financials, section_total, lines_sum, latest_two, SNAPSHOT_DATE, UNVERIFIED_FROM,
)

st.set_page_config(page_title="Opex Metrics | Telco Retail", page_icon="🏦", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Opex Metrics", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"Source: hand-maintained Excel workbook on SharePoint, snapshotted {SNAPSHOT_DATE}. "
    f"Marketing spend sits under the GL's Acquisition Cost section, not Opex — shown "
    f"here anyway since that's the actual question this card answers.</p>",
    unsafe_allow_html=True,
)

MARKETING_LINES = ["Marketing Cost for Retail stores", "Digital/Print Marketing", "Advertising & Marketing"]

df = load_financials()
today = pd.Timestamp(date.today())

revenue   = section_total(df, "Revenue")
opex      = section_total(df, "Opex")
staff     = lines_sum(df, ["Salaries", "Provision for Bonus"])
marketing = lines_sum(df, MARKETING_LINES)
opex_pct  = (opex / revenue.replace(0, float("nan")) * 100)

opex_this, opex_last = latest_two(opex, today)
pct_this, pct_last = latest_two(opex_pct, today)
staff_this, staff_last = latest_two(staff, today)
mkt_this, mkt_last = latest_two(marketing, today)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Opex", f"R{opex_this:,.0f}", delta=f"R{opex_this-opex_last:+,.0f} vs last month",
          delta_color="inverse")
k2.metric("Opex as % of Revenue", f"{pct_this:.1f}%", delta=f"{pct_this-pct_last:+.1f}pp vs last month",
          delta_color="inverse")
k3.metric("Staff Costs", f"R{staff_this:,.0f}", delta=f"R{staff_this-staff_last:+,.0f} vs last month",
          delta_color="inverse", help="Salaries + Provision for Bonus")
k4.metric("Marketing Spend", f"R{mkt_this:,.0f}", delta=f"R{mkt_this-mkt_last:+,.0f} vs last month",
          delta_color="inverse")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)


def _base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1, plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11), margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER),
        bargap=0.3,
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11), bgcolor="rgba(0,0,0,0)"),
    )


trend_cutoff = min(today + pd.DateOffset(months=6), UNVERIFIED_FROM - pd.DateOffset(months=1))
latest_actual_month = df[df["month"] <= today]["month"].max()
opex_month = df[(df["section"] == "Opex") & (df["month"] == latest_actual_month)]
top5 = opex_month.groupby("detail")["value"].sum().sort_values(ascending=False).head(5)

opex_t = opex[opex.index <= trend_cutoff].tail(13)
opex_pct_t = opex_pct[opex_pct.index <= trend_cutoff].tail(13)
x_t = opex_t.index.strftime("%b '%y").tolist()

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure(go.Bar(
        x=top5.index.tolist(), y=top5.values.tolist(),
        marker_color=CHART_PALETTE[:len(top5)], marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    layout = _base(f"Top 5 Opex Lines — {opex_month['month'].iloc[0].strftime('%b %Y') if not opex_month.empty else ''}")
    layout["yaxis"]["tickprefix"] = "R"
    layout["yaxis"]["tickformat"] = ",.0f"
    layout["xaxis"]["tickangle"] = -20
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    fig2 = go.Figure(go.Bar(
        x=x_t, y=opex_t.tolist(), marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    layout2 = _base("Total Opex — Trend (13 months)")
    layout2["yaxis"]["tickprefix"] = "R"
    layout2["yaxis"]["tickformat"] = ",.0f"
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    fig3 = go.Figure(go.Scatter(
        x=x_t, y=opex_pct_t.reindex(opex_t.index).tolist(),
        mode="lines+markers", line=dict(color=ULTRAVIOLET, width=2),
        hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>",
    ))
    layout3 = _base("Opex % of Revenue — Monthly")
    layout3["yaxis"]["ticksuffix"] = "%"
    layout3["yaxis"]["tickformat"] = ",.1f"
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    st.markdown(
        f"<div style='color:#666; font-size:12px; padding-top:40px; text-align:center;'>"
        f"No separate budget series exists in this workbook — Budget vs Actual Opex "
        f"is <span style='color:{HIGHVOLT_ORANGE};'>still pending</span> a distinct budget source.</div>",
        unsafe_allow_html=True,
    )
