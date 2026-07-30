"""
Cost of Sale Metrics — Financials section
Data: TEST INCOME STATEMENT.xlsx ('Format Is' sheet) for GL costs, cross-referenced
with UCONNECT_MAY_MERGE (live Snowflake) for activation counts. See
utils/financials.py for source/refresh notes on the Excel snapshot.
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
from utils.snowflake_conn import run_query, MERGE_TABLE
from utils.financials import (
    load_financials, section_total, section_breakdown, lines_sum, latest_two,
    SNAPSHOT_DATE, UNVERIFIED_FROM,
)

st.set_page_config(page_title="Cost of Sale Metrics | Telco Retail", page_icon="💸", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Cost of Sale Metrics", badge="Financials")

st.markdown(
    f"<p style='color:#666; font-size:12px; margin-bottom:16px;'>"
    f"GL cost data from a hand-maintained Excel workbook on SharePoint, snapshotted "
    f"{SNAPSHOT_DATE} — cross-referenced with live Snowflake activation counts.</p>",
    unsafe_allow_html=True,
)

AIRTIME_LINES = ["Voice_uConnect", "Data_uConnect", "Voice_credits", "Data credits"]

df = load_financials()
today = pd.Timestamp(date.today())

revenue  = section_total(df, "Revenue")
cos      = section_total(df, "Cost of Sales")
airtime  = lines_sum(df, AIRTIME_LINES)
cos_pct  = (cos / revenue.replace(0, float("nan")) * 100)


@st.cache_data(ttl=1800, show_spinner=False)
def load_activations():
    q = run_query(f"""
        SELECT DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START, COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month,-13,CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    q.columns = [c.upper() for c in q.columns]
    q["MONTH_START"] = pd.to_datetime(q["MONTH_START"])
    return q.set_index("MONTH_START")["ACTIVATIONS"]


activations = load_activations()

# SIM Kitting/Stock costs live under the Acquisition Cost section, not Cost of Sales,
# but "SIM cost per activation" is the actual business question this KPI is answering.
sim_costs = lines_sum(df, ["SIM Kitting Costs", "uConnect Sim Stock"])
sim_cost_per_act = (sim_costs / activations.replace(0, float("nan")))

cos_this, cos_last = latest_two(cos, today)
cos_pct_this, cos_pct_last = latest_two(cos_pct, today)
sim_this, sim_last = latest_two(sim_cost_per_act, today)
air_this, air_last = latest_two(airtime, today)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Cost of Sales", f"R{cos_this:,.0f}", delta=f"R{cos_this-cos_last:+,.0f} vs last month")
k2.metric("CoS as % of Revenue", f"{cos_pct_this:.1f}%", delta=f"{cos_pct_this-cos_pct_last:+.1f}pp vs last month",
          delta_color="inverse")
k3.metric(
    "SIM Cost per Activation",
    f"R{sim_this:,.2f}" if pd.notna(sim_this) else "—",
    delta=f"R{sim_this - sim_last:+.2f} vs last month" if pd.notna(sim_this) and pd.notna(sim_last) else None,
    delta_color="inverse",
    help="(SIM Kitting Costs + uConnect Sim Stock) ÷ Snowflake activation count. "
         "These GL lines sit under Acquisition Cost, not Cost of Sales.",
)
k4.metric("Airtime CoS", f"R{air_this:,.0f}", delta=f"R{air_this-air_last:+,.0f} vs last month",
          delta_color="inverse", help="Voice_uConnect + Data_uConnect + Voice_credits + Data credits")

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
breakdown = section_breakdown(df, "Cost of Sales", by="subheader")
breakdown = breakdown[breakdown.index <= trend_cutoff].tail(13)
x_t = breakdown.index.strftime("%b '%y").tolist()

c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = go.Figure()
    for col, color in zip(breakdown.columns, [SONIC_BLUE, HIGHVOLT_ORANGE]):
        fig.add_trace(go.Bar(x=x_t, y=breakdown[col].tolist(), name=col, marker_color=color, marker_line_width=0))
    layout = _base("CoS Components — Monthly")
    layout["yaxis"]["tickprefix"] = "R"
    layout["yaxis"]["tickformat"] = ",.0f"
    fig.update_layout(**layout, barmode="stack")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    cos_pct_t = cos_pct[cos_pct.index <= trend_cutoff].tail(13)
    fig2 = go.Figure(go.Scatter(
        x=x_t, y=cos_pct_t.reindex(breakdown.index).tolist(),
        mode="lines+markers", line=dict(color=ULTRAVIOLET, width=2),
        hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>",
    ))
    layout2 = _base("CoS % of Revenue — Monthly Trend")
    layout2["yaxis"]["ticksuffix"] = "%"
    layout2["yaxis"]["tickformat"] = ",.1f"
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

c3, c4 = st.columns(2, gap="medium")
with c3:
    sim_t = sim_cost_per_act[sim_cost_per_act.index <= min(today, activations.index.max() if len(activations) else today)].tail(13)
    fig3 = go.Figure(go.Scatter(
        x=sim_t.index.strftime("%b '%y").tolist(), y=sim_t.tolist(),
        mode="lines+markers", line=dict(color=HYPERMINT, width=2),
        hovertemplate="%{x}<br><b>R%{y:,.2f}</b><extra></extra>",
    ))
    layout3 = _base("SIM Cost per Activation — Trend")
    layout3["yaxis"]["tickprefix"] = "R"
    layout3["yaxis"]["tickformat"] = ",.2f"
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    air_t = airtime[airtime.index <= trend_cutoff].tail(13)
    fig4 = go.Figure(go.Bar(
        x=air_t.index.strftime("%b '%y").tolist(), y=air_t.tolist(),
        marker_color=SONIC_BLUE, marker_line_width=0,
        hovertemplate="%{x}<br><b>R%{y:,.0f}</b><extra></extra>",
    ))
    layout4 = _base("Airtime CoS — Monthly")
    layout4["yaxis"]["tickprefix"] = "R"
    layout4["yaxis"]["tickformat"] = ",.0f"
    fig4.update_layout(**layout4)
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
