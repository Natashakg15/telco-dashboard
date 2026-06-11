"""
Spar Scorecard
Replicates the PBIX 'Spar scorecard' page.

Live data (in MCP):
  UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE              — activations
  UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS — SIM quality

Placeholders (data not yet in MCP):
  NEW QOS, ROS, SNU, AVG Vouchers  — QOS / ROS / avg voucher KPIs & store pivot
  ROS_L7 DAYS SQL BI                — ROS 7-day avg card
  L12  month voucher redemptions    — voucher redemptions trend
  COHORT                            — cohort revenue charts
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    INKCORE, SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

USAGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS"

# ── Spar SQL filter ────────────────────────────────────────────────────────────
# Matches PBIX _Tenant uConnect_.Grouped = 'Spar Retail'
# Excludes Midas stores that happen to contain 'spar' (e.g. KR Motor Spares)
SPAR_WHERE_MERGE = """
    (LOWER(TENANT) LIKE '%spar%' OR LOWER(TENANT) LIKE '%savemor%')
    AND LOWER(TENANT) NOT LIKE '%midas%'
"""
SPAR_WHERE_USAGE = """
    (LOWER(TENANT_NAME) LIKE '%spar%' OR LOWER(TENANT_NAME) LIKE '%savemor%')
    AND LOWER(TENANT_NAME) NOT LIKE '%midas%'
"""

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spar Scorecard | Telco Retail",
    page_icon="🏪",
    layout="wide",
)
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Spar Scorecard", badge="Scorecard")

# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner="Loading Spar activations…")
def load_monthly_activations():
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START,
            COUNT(*)                              AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE {SPAR_WHERE_MERGE}
          AND ACTIVATION_DATE >= DATEADD(month, -13, CURRENT_DATE())
        GROUP BY 1
        ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_daily_activations():
    df = run_query(f"""
        SELECT
            ACTIVATION_DATE,
            COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE {SPAR_WHERE_MERGE}
          AND ACTIVATION_DATE >= CURRENT_DATE() - 90
        GROUP BY 1
        ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_sim_quality():
    """Active 1 % and SIMs Never Used for Spar stores — last 30-day cohort."""
    df = run_query(f"""
        SELECT
            -- Active SIMs: used within 30 days
            SUM(CASE WHEN USAGE_0_30_DAYS = '1'         THEN 1 ELSE 0 END) AS ACTIVE_1_COUNT,
            -- SIMs Never Used
            SUM(CASE WHEN LASTUSAGEDATETIME IS NULL      THEN 1 ELSE 0 END) AS SIMS_NEVER_USED,
            -- Total active subscriptions
            COUNT(*)                                                         AS TOTAL_SIMS,
            -- Active 1 %
            SUM(CASE WHEN USAGE_0_30_DAYS = '1' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0)                                        AS ACTIVE_1_PCT,
            -- 30-35 day cohort quality (QoS proxy)
            SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) BETWEEN CURRENT_DATE()-35
                                                      AND CURRENT_DATE()-30
                          AND TRY_TO_NUMBER(DAYS_SINCE_LAST_USAGE) <= 7
                     THEN 1 ELSE 0 END)::FLOAT
            / NULLIF(
                SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) BETWEEN CURRENT_DATE()-35
                                                          AND CURRENT_DATE()-30
                         THEN 1 ELSE 0 END), 0
            )                                                                AS QOS_PROXY_PCT
        FROM {USAGE_TABLE}
        WHERE {SPAR_WHERE_USAGE}
    """)
    df.columns = [c.upper() for c in df.columns]
    return df.iloc[0] if not df.empty else {}


@st.cache_data(ttl=1800, show_spinner=False)
def load_store_breakdown():
    """Per-store activation counts this month and last month."""
    df = run_query(f"""
        SELECT
            TENANT,
            SUM(CASE WHEN DATE_TRUNC('month', ACTIVATION_DATE)
                          = DATE_TRUNC('month', CURRENT_DATE())
                     THEN 1 ELSE 0 END) AS THIS_MONTH,
            SUM(CASE WHEN DATE_TRUNC('month', ACTIVATION_DATE)
                          = DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
                     THEN 1 ELSE 0 END) AS LAST_MONTH
        FROM {MERGE_TABLE}
        WHERE {SPAR_WHERE_MERGE}
          AND ACTIVATION_DATE >= DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
        GROUP BY 1
        ORDER BY THIS_MONTH DESC
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


monthly_df   = load_monthly_activations()
daily_df     = load_daily_activations()
quality      = load_sim_quality()
store_df     = load_store_breakdown()

# Normalise date columns — guard against demo fallback returning different names
if "MONTH_START" not in monthly_df.columns and "ACTIVATION_DATE" in monthly_df.columns:
    monthly_df = monthly_df.rename(columns={"ACTIVATION_DATE": "MONTH_START"})
monthly_df["MONTH_START"]   = pd.to_datetime(monthly_df["MONTH_START"])
daily_df["ACTIVATION_DATE"] = pd.to_datetime(daily_df["ACTIVATION_DATE"])

today        = date.today()
month_start  = today.replace(day=1)
prev_m_label = (month_start - timedelta(days=1)).strftime("%B %Y")
this_m_label = today.strftime("%B %Y")

this_month_acts = int(monthly_df.iloc[-1]["ACTIVATIONS"]) if not monthly_df.empty else 0
last_month_acts = int(monthly_df.iloc[-2]["ACTIVATIONS"]) if len(monthly_df) >= 2 else 0
mom_delta       = this_month_acts - last_month_acts

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def fmt_pct(val):
    try:
        f = float(val)
        return "—" if f != f else f"{f * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1,
        plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11),
        margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, linecolor="rgba(0,0,0,0)", tickformat=","),
        bargap=0.3,
    )


def placeholder_card(label: str, source: str):
    """Styled placeholder card for metrics pending data access."""
    st.markdown(
        f"""
        <div style='background:{SURFACE_1}; border:1px dashed {BORDER};
                    border-radius:10px; padding:18px 16px; text-align:center;
                    min-height:90px;'>
            <div style='color:#555; font-size:11px; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:6px;'>{label}</div>
            <div style='color:#444; font-size:22px; font-weight:700;'>—</div>
            <div style='color:#3a3a3a; font-size:10px; margin-top:6px;'>
                Pending: <span style='color:{HIGHVOLT_ORANGE};'>{source}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def placeholder_chart(title: str, source: str, height: int = 260):
    """Styled placeholder chart panel."""
    st.markdown(
        f"""
        <div style='background:{SURFACE_1}; border:1px dashed {BORDER};
                    border-radius:10px; padding:24px 20px; height:{height}px;
                    display:flex; flex-direction:column; justify-content:center;
                    align-items:center; text-align:center;'>
            <div style='color:{ZERO_WHITE}; font-size:13px; font-weight:600;
                        margin-bottom:8px;'>{title}</div>
            <div style='color:#555; font-size:12px;'>Chart pending data access</div>
            <div style='color:{HIGHVOLT_ORANGE}; font-size:11px; margin-top:6px;'>
                Source: {source}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. KPI strip — activations (live) + QOS/ROS/vouchers (placeholder)
# ─────────────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("This Month", f"{this_month_acts:,}")
k2.metric("Last Month",  f"{last_month_acts:,}", delta=f"{mom_delta:+,}")
k3.metric("Active 1 %",  fmt_pct(quality.get("ACTIVE_1_PCT")))
k4.metric("SIMs Never Used", f'{int(quality.get("SIMS_NEVER_USED", 0) or 0):,}')

with k5:
    placeholder_card("QOS 7-Day Avg", "NEW QOS table")
with k6:
    placeholder_card("ROS 7-Day Avg", "ROS_L7 DAYS SQL BI")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Monthly activations combo chart (live) + sales per day (placeholder)
# ─────────────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2, gap="medium")

with c1:
    # Rolling 7-day avg on daily data
    rolling = (
        daily_df.set_index("ACTIVATION_DATE")
        .reindex(pd.date_range(daily_df["ACTIVATION_DATE"].min(),
                               daily_df["ACTIVATION_DATE"].max()))
        .rename_axis("ACTIVATION_DATE").fillna(0).reset_index()
    )
    rolling["ROLLING_7DAY_AVG"] = rolling["ACTIVATIONS"].rolling(7, min_periods=1).mean().round(1)
    x = rolling["ACTIVATION_DATE"].dt.strftime("%d %b").tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=rolling["ACTIVATIONS"].tolist(),
        name="Daily Activations",
        marker_color=SONIC_BLUE, marker_line_width=0, opacity=0.7,
        hovertemplate="%{x}<br><b>Activations: %{y:,}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=rolling["ROLLING_7DAY_AVG"].tolist(),
        name="7-Day Avg", mode="lines",
        line=dict(color=HYPERMINT, width=2),
        hovertemplate="%{x}<br><b>7-Day Avg: %{y:,.1f}</b><extra></extra>",
    ))
    layout = _base_layout("Daily Activations & 7-Day Rolling Avg — Spar (Last 90 Days)")
    layout.update(dict(
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11),
                    bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    ))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    placeholder_chart(
        "Sales Per Day (Avg) — Spar",
        "NEW QOS, ROS, SNU, AVG Vouchers",
        height=310,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 3. Monthly activations bar (live) + L12 voucher redemptions (placeholder)
# ─────────────────────────────────────────────────────────────────────────────
c3, c4 = st.columns(2, gap="medium")

with c3:
    fig_m = go.Figure(go.Bar(
        x=monthly_df["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly_df["ACTIVATIONS"].tolist(),
        marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
        hovertemplate="%{x}<br><b>Activations: %{y:,}</b><extra></extra>",
    ))
    fig_m.update_layout(**_base_layout("Monthly Activations — Spar (13 Months)"))
    st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})

with c4:
    placeholder_chart(
        "L12 Month Voucher Redemptions — Spar",
        "L12 month voucher redemptions",
        height=310,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 4. Cohort revenue charts (placeholders — need COHORT table)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:12px;'>"
    f"Cohort Revenue Analysis</h3>",
    unsafe_allow_html=True,
)
ch1, ch2 = st.columns(2, gap="medium")

with ch1:
    placeholder_chart(
        "Average Revenue per Acquired — by Cohort Month",
        "COHORT table",
        height=280,
    )
with ch2:
    placeholder_chart(
        "Total Margin — by Cohort Month",
        "COHORT table",
        height=280,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 5. Store performance pivot — QOS / ROS / vouchers (placeholder top section)
#    + Activations by store (live)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:4px;'>"
    f"Store Performance</h3>"
    f"<p style='color:#666; font-size:12px; margin-top:0; margin-bottom:12px;'>"
    f"QOS / ROS / voucher columns pending <span style='color:{HIGHVOLT_ORANGE};'>"
    f"NEW QOS, ROS, SNU, AVG Vouchers</span> data access. "
    f"Activations columns are live.</p>",
    unsafe_allow_html=True,
)

# Build display table
if not store_df.empty:
    display = store_df.copy()
    display.columns = [c.title().replace("_", " ") for c in display.columns]
    display.insert(0, "#", range(1, len(display) + 1))
    display["QOS 7D Avg"] = "—"
    display["ROS 7D Avg"] = "—"
    display["Avg Vouchers"] = "—"

    # Render as styled HTML table
    col_order = ["#", "Tenant", "This Month", "Last Month", "QOS 7D Avg", "ROS 7D Avg", "Avg Vouchers"]
    display = display.rename(columns={"Tenant": "Tenant"})[col_order]

    header_cells = "".join(
        f"<th style='padding:8px 10px; color:#555; font-size:11px; text-align:{'left' if i < 2 else 'right'}; "
        f"background:{SURFACE_2};'>{col}</th>"
        for i, col in enumerate(col_order)
    )

    def row_html(row):
        cells = ""
        for i, col in enumerate(col_order):
            val = row[col]
            align = "left" if i < 2 else "right"
            if col == "#":
                color = "#555"
                val_str = str(val)
            elif col == "Tenant":
                color = ZERO_WHITE
                val_str = str(val)
            elif col in ("This Month", "Last Month"):
                color = HYPERMINT if col == "This Month" else SONIC_BLUE
                val_str = f"{int(val):,}" if val else "0"
            else:
                color = "#444"
                val_str = str(val)
            cells += (
                f"<td style='padding:6px 10px; color:{color}; font-size:12px; "
                f"text-align:{align};'>{val_str}</td>"
            )
        return f"<tr>{cells}</tr>"

    rows_html = "".join(row_html(r) for _, r in display.iterrows())

    st.markdown(
        f"""
        <div style='overflow-x:auto;'>
        <table style='width:100%; border-collapse:collapse;
                      background:{SURFACE_1}; border-radius:10px; overflow:hidden;'>
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("No store data available for the current period.")
