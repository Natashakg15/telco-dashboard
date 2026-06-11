"""
Quality of Sales — Sales section, Page 2
Data sources:
  UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS
  UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE  (daily activations for chart bars)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    INKCORE, SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE,
)
from utils.snowflake_conn import run_query

USAGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quality of Sales | Telco Retail",
    page_icon="🎯",
    layout="wide",
)
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Quality of Sales", badge="Sales")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='text-align:center; padding:24px 0 16px 0;'>"
        f"<div style='font-size:28px; font-weight:800; color:{HYPERMINT};"
        f"letter-spacing:-0.03em;'>SPOT</div>"
        f"<div style='font-size:11px; color:#666; letter-spacing:0.12em;"
        f"text-transform:uppercase; margin-top:2px;'>Connect</div>"
        f"</div><hr style='border-color:{BORDER}; margin:0 0 16px 0;'/>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner="Loading quality metrics…")
def load_kpis():
    """
    Single-pass query for all four KPI cards.

    Column notes (from schema inspection):
      USAGE_0_30_DAYS      — TEXT: '1' = used in last 30 days, '0' = did not,
                             'SIM Never Used' = no usage ever
      DAYS_SINCE_LAST_USAGE — TEXT: numeric string or 'SIM Never Used'
      ACCOUNTCREATEDATE    — TIMESTAMP_NTZ
      LASTUSAGEDATETIME    — TIMESTAMP_NTZ, NULL when never used
    """
    df = run_query(f"""
        SELECT
            -- ① Active 7 Days % for 30-35 day cohort
            --   (accounts in cohort active in last 7 days / all accounts in cohort)
            SUM(
                CASE WHEN DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 35
                          AND DATE(ACCOUNTCREATEDATE) <= CURRENT_DATE() - 30
                          AND TRY_TO_NUMBER(DAYS_SINCE_LAST_USAGE) <= 7
                     THEN 1 ELSE 0 END
            )::FLOAT
            / NULLIF(
                SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 35
                              AND DATE(ACCOUNTCREATEDATE) <= CURRENT_DATE() - 30
                         THEN 1 ELSE 0 END), 0
            ) AS ACTIVE7_30_35_PCT,

            -- ② Still Using After 1 Month
            --   (7-day actives in 30-35 cohort) / (ever-used accounts in 30-35 cohort)
            --   "of those who used at least once"
            SUM(
                CASE WHEN DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 35
                          AND DATE(ACCOUNTCREATEDATE) <= CURRENT_DATE() - 30
                          AND TRY_TO_NUMBER(DAYS_SINCE_LAST_USAGE) <= 7
                     THEN 1 ELSE 0 END
            )::FLOAT
            / NULLIF(
                SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 35
                              AND DATE(ACCOUNTCREATEDATE) <= CURRENT_DATE() - 30
                              AND LASTUSAGEDATETIME IS NOT NULL
                         THEN 1 ELSE 0 END), 0
            ) AS STILL_USING_PCT,

            -- ③ Quality of Sales Indicator
            --   Active 1 % for accounts created 2-4 days ago
            --   (proxy for near-real-time SIM activation quality)
            SUM(
                CASE WHEN DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 4
                          AND DATE(ACCOUNTCREATEDATE) <= CURRENT_DATE() - 2
                          AND USAGE_0_30_DAYS = '1'
                     THEN 1 ELSE 0 END
            )::FLOAT
            / NULLIF(
                SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 4
                              AND DATE(ACCOUNTCREATEDATE) <= CURRENT_DATE() - 2
                         THEN 1 ELSE 0 END), 0
            ) AS QUALITY_INDICATOR_PCT

        FROM {USAGE_TABLE}
    """)
    df.columns = [c.upper() for c in df.columns]
    if df.empty:
        import pandas as pd
        return pd.Series({
            "ACTIVE7_30_35_PCT":    None,
            "STILL_USING_PCT":      None,
            "QUALITY_INDICATOR_PCT": None,
        })
    return df.iloc[0]


@st.cache_data(ttl=1800, show_spinner="Loading chart data…")
def load_chart_data():
    """
    Single query from the active subscriptions view:
      ACTIVATIONS — count of accounts created each day (bars)
      ACTIVE1_PCT — % of those accounts that used their SIM within 30 days (line)
    """
    df = run_query(f"""
        SELECT
            DATE(ACCOUNTCREATEDATE)                                       AS DT,
            COUNT(*)                                                      AS ACTIVATIONS,
            SUM(CASE WHEN USAGE_0_30_DAYS = '1' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0)                                     AS ACTIVE1_PCT
        FROM {USAGE_TABLE}
        WHERE DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 30
        GROUP BY 1
        ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    if df.empty:
        return pd.DataFrame(columns=["DT", "ACTIVATIONS", "ACTIVE1_PCT"])
    return df


# ── Load ──────────────────────────────────────────────────────────────────────
kpis     = load_kpis()
chart_df = load_chart_data()

# ─────────────────────────────────────────────────────────────────────────────
# Helper — format a 0-1 float as a percentage string
# ─────────────────────────────────────────────────────────────────────────────
def fmt_pct(val):
    try:
        f = float(val)
        if f != f:          # NaN
            return "—"
        return f"{f * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# KPI strip — 4 cards
# ─────────────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Active 7 Days After 1 Month",
    fmt_pct(kpis.get("ACTIVE7_30_35_PCT")),
    help="Accounts created 30-35 days ago that used their SIM in the last 7 days, as a % of all accounts in that cohort.",
)
k2.metric(
    "Still Using After 1 Month",
    fmt_pct(kpis.get("STILL_USING_PCT")),
    help="Of accounts created 30-35 days ago that used their SIM at least once, what % are still active in the last 7 days.",
)
k3.metric(
    "Quality of Sales Indicator",
    fmt_pct(kpis.get("QUALITY_INDICATOR_PCT")),
    help="Active 1 % for accounts created 2-4 days ago — early signal of SIM activation quality.",
)
k4.metric(
    "Last Month M1 ARPU",
    "—",
    help="Coming soon.",
)

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Combo chart — bars: daily activations · line: Active 1 % (secondary axis)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:2px;'>"
    f"Daily Activations &amp; Active 1 % — Last 31 Days</h3>"
    f"<p style='color:#666; font-size:12px; margin-top:0; margin-bottom:12px;'>"
    f"Bars = new activations (left axis) &nbsp;·&nbsp; "
    f"Line = % of accounts created that day who used their SIM within 30 days (right axis).</p>",
    unsafe_allow_html=True,
)

chart_df["DT"] = pd.to_datetime(chart_df["DT"])
chart_df = chart_df.sort_values("DT")
x_labels = chart_df["DT"].dt.strftime("%d %b").tolist()

fig = go.Figure()

# Bars — daily activations
fig.add_trace(go.Bar(
    x=x_labels,
    y=chart_df["ACTIVATIONS"].tolist(),
    name="Daily Activations",
    marker_color=SONIC_BLUE,
    marker_line_width=0,
    hovertemplate="%{x}<br><b>Activations: %{y:,}</b><extra></extra>",
    yaxis="y1",
))

# Line — Active 1 %
fig.add_trace(go.Scatter(
    x=x_labels,
    y=(chart_df["ACTIVE1_PCT"] * 100).round(1).tolist(),
    name="Active 1 %",
    mode="lines+markers",
    line=dict(color=HYPERMINT, width=2),
    marker=dict(size=5, color=HYPERMINT),
    hovertemplate="%{x}<br><b>Active 1 %%: %{y:.1f}%%</b><extra></extra>",
    yaxis="y2",
))

fig.update_layout(
    paper_bgcolor=SURFACE_1,
    plot_bgcolor=SURFACE_1,
    font=dict(color="#888", size=11),
    margin=dict(l=8, r=8, t=32, b=8),
    legend=dict(
        orientation="h",
        y=1.08,
        font=dict(color=ZERO_WHITE, size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        showgrid=False,
        linecolor=BORDER,
        tickfont=dict(size=10, color="#888"),
    ),
    yaxis=dict(
        title="Activations",
        showgrid=True,
        gridcolor=BORDER,
        linecolor="rgba(0,0,0,0)",
        tickformat=",",
        title=dict(text="Activations", font=dict(color=SONIC_BLUE, size=11)),
        tickfont=dict(color=SONIC_BLUE),
    ),
    yaxis2=dict(
        title=dict(text="Active 1 %", font=dict(color=HYPERMINT, size=11)),
        overlaying="y",
        side="right",
        showgrid=False,
        tickformat=".0f",
        ticksuffix="%",
        tickfont=dict(color=HYPERMINT),
        range=[0, 105],
    ),
    bargap=0.3,
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
