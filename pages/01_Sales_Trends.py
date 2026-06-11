"""
Sales Trends — Page 1 of Sales section
Data sources:
  UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE
  UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.ci import (
    inject_css, page_header,
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    INKCORE, SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE, CHART_PALETTE,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

USAGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Trends | Telco Retail",
    page_icon="📈",
    layout="wide",
)
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Sales Trends", badge="Sales")

# ─────────────────────────────────────────────────────────────────────────────
# Tenant grouping logic  (matches _Tenant uConnect_ calculated table in PBIX)
# ─────────────────────────────────────────────────────────────────────────────
def map_tenant_group(name: str) -> str:
    n = name or ""
    nl = n.lower()
    if "build it" in nl:
        return "Build It"
    if "midas" in nl or "kr motor spares" in nl or "aca auto parts" in nl or "aca autoparts" in nl:
        return "Midas"
    if "mica" in nl or "greenfields hardware" in nl:
        return "Mica"
    if "spargs" in nl or "savemor" in nl or "spar" in nl:
        return "Spar Retail"
    if "fashion" in nl:
        return "Fashion Fusion"
    if "progas" in nl:
        return "Progas"
    if "aheers" in nl:
        return "Aheers"
    if nl == "the unlimited":
        return "The Unlimited"
    if "ladysmith office national" in nl:
        return "Ladysmith Office National"
    if "onair" in nl or "on air" in nl:
        return "OnAir"
    if "pet pool" in nl:
        return "Pet Pool & Home"
    if nl == "spot mobile":
        return "Spot Mobile"
    if "uconnect app" in nl or "uconnect digital" in nl:
        return "Spot Connect App & Digital"
    return "Other Tenants"


DEFINED_GROUPS = [
    "Spar Retail", "Build It", "Midas", "Mica", "Fashion Fusion",
    "Progas", "Aheers", "The Unlimited", "Ladysmith Office National",
    "OnAir", "Pet Pool & Home", "Spot Mobile", "Spot Connect App & Digital",
]

# ─────────────────────────────────────────────────────────────────────────────
# 1. Tenant filter
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_tenants():
    df = run_query(f"""
        SELECT DISTINCT TENANT
        FROM {MERGE_TABLE}
        WHERE TENANT IS NOT NULL AND TENANT != ''
        ORDER BY TENANT
    """)
    df.columns = [c.upper() for c in df.columns]
    return df["TENANT"].tolist()

all_raw_tenants = load_tenants()

group_to_raw: dict[str, list[str]] = {}
for t in all_raw_tenants:
    g = map_tenant_group(t)
    group_to_raw.setdefault(g, []).append(t)

available_groups = sorted(
    [g for g in DEFINED_GROUPS if g in group_to_raw],
    key=lambda x: DEFINED_GROUPS.index(x),
)
if "Other Tenants" in group_to_raw:
    available_groups.append("Other Tenants")

with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Tenant Filter</div>",
        unsafe_allow_html=True,
    )
    st.caption("Filters the trend charts only. Tables are unaffected.")
    selected_groups = st.multiselect(
        "Select tenant groups",
        options=available_groups,
        default=[],
        placeholder="All tenants",
        label_visibility="collapsed",
    )

if selected_groups:
    raw_for_filter = [t for g in selected_groups for t in group_to_raw.get(g, [])]
    tenant_clause = f"AND TENANT IN ({', '.join(repr(t) for t in raw_for_filter)})"
else:
    tenant_clause = ""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Data loaders
# ─────────────────────────────────────────────────────────────────────────────
today = date.today()
last_7_start = today - timedelta(days=6)
month_start  = today.replace(day=1)

@st.cache_data(ttl=1800, show_spinner="Loading trend data…")
def load_daily(tenant_filter: str):
    df = run_query(f"""
        SELECT
            ACTIVATION_DATE,
            COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE ACTIVATION_DATE >= DATEADD(month, -13, CURRENT_DATE())
          {tenant_filter}
        GROUP BY 1
        ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_tables_data():
    """Tenant tables — always unfiltered to show full picture."""
    df = run_query(f"""
        SELECT
            TENANT,
            SUM(CASE WHEN DATE_TRUNC('month', ACTIVATION_DATE)
                          = DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
                     THEN 1 ELSE 0 END) AS LAST_MONTH,
            SUM(CASE WHEN DATE_TRUNC('month', ACTIVATION_DATE)
                          = DATE_TRUNC('month', CURRENT_DATE())
                     THEN 1 ELSE 0 END) AS THIS_MONTH
        FROM {MERGE_TABLE}
        WHERE TENANT IS NOT NULL AND TENANT != ''
          AND ACTIVATION_DATE >= DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
        GROUP BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_snu_active1():
    """
    Sims Never Used and Active 1 counts by activation date — last 90 days.
    Sims Never Used  = account that has never had any usage (LASTUSAGEDATETIME IS NULL)
    Active 1         = account used within 30 days of activation (USAGE_0_30_DAYS = '1')
    Both grouped by DATE(ACCOUNTCREATEDATE) to match PBIX ACCOUNTCREATEDATE day axis.
    """
    df = run_query(f"""
        SELECT
            DATE(ACCOUNTCREATEDATE)                                         AS DT,
            SUM(CASE WHEN LASTUSAGEDATETIME IS NULL THEN 1 ELSE 0 END)      AS SIMS_NEVER_USED,
            SUM(CASE WHEN USAGE_0_30_DAYS = '1'     THEN 1 ELSE 0 END)      AS ACTIVE_1
        FROM {USAGE_TABLE}
        WHERE DATE(ACCOUNTCREATEDATE) >= CURRENT_DATE() - 90
        GROUP BY 1
        ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


daily_df  = load_daily(tenant_clause)
tables_df = load_tables_data()
snu_df    = load_snu_active1()

daily_df["ACTIVATION_DATE"] = pd.to_datetime(daily_df["ACTIVATION_DATE"])
snu_df["DT"] = pd.to_datetime(snu_df["DT"])

# ─────────────────────────────────────────────────────────────────────────────
# 3. Derived aggregations
# ─────────────────────────────────────────────────────────────────────────────
weekly_df = (
    daily_df.set_index("ACTIVATION_DATE")
    .resample("W-MON", label="left", closed="left")["ACTIVATIONS"]
    .sum()
    .reset_index()
    .rename(columns={"ACTIVATION_DATE": "WEEK_START"})
)

monthly_df = (
    daily_df.set_index("ACTIVATION_DATE")
    .resample("MS")["ACTIVATIONS"]
    .sum()
    .reset_index()
    .rename(columns={"ACTIVATION_DATE": "MONTH_START"})
)

last7_df = daily_df[daily_df["ACTIVATION_DATE"] >= pd.Timestamp(last_7_start)].copy()

# Rolling 7-day average — matches PBIX "Sales L7 Day Avg" calculated table
rolling_df = (
    daily_df.set_index("ACTIVATION_DATE")
    .sort_index()
    .reindex(pd.date_range(daily_df["ACTIVATION_DATE"].min(), daily_df["ACTIVATION_DATE"].max()))
    .rename_axis("ACTIVATION_DATE")
    .fillna(0)
    .reset_index()
)
rolling_df["ROLLING_7DAY_AVG"] = (
    rolling_df["ACTIVATIONS"].rolling(7, min_periods=1).mean().round(1)
)
# Keep last 90 days to keep the chart readable
rolling_df = rolling_df[
    rolling_df["ACTIVATION_DATE"] >= pd.Timestamp(today - timedelta(days=89))
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. KPI strip
# ─────────────────────────────────────────────────────────────────────────────
this_month_total = int(monthly_df.iloc[-1]["ACTIVATIONS"]) if not monthly_df.empty else 0
last_month_total = int(monthly_df.iloc[-2]["ACTIVATIONS"]) if len(monthly_df) >= 2 else 0
last7_total      = int(last7_df["ACTIVATIONS"].sum())
today_row        = daily_df[daily_df["ACTIVATION_DATE"] == pd.Timestamp(today)]
today_total      = int(today_row["ACTIVATIONS"].iloc[0]) if not today_row.empty else 0
mom_delta        = this_month_total - last_month_total

k1, k2, k3, k4 = st.columns(4)
k1.metric("Today", f"{today_total:,}")
k2.metric("Last 7 Days", f"{last7_total:,}")
k3.metric("This Month", f"{this_month_total:,}")
k4.metric("vs Last Month", f"{last_month_total:,}", delta=f"{mom_delta:+,}")

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Chart helpers
# ─────────────────────────────────────────────────────────────────────────────
def _base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1,
        plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11),
        margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor=BORDER, linecolor="rgba(0,0,0,0)",
                   tickformat=","),
        bargap=0.3,
    )


def spot_bar(x, y, title, colour=HYPERMINT, last_n=None):
    if last_n:
        x, y = x[-last_n:], y[-last_n:]
    fig = go.Figure(go.Bar(
        x=x, y=y,
        marker_color=colour,
        marker_line_width=0,
        hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
    ))
    fig.update_layout(**_base_layout(title))
    return fig


def rolling_combo_chart(df):
    """
    Line + bar combo matching PBIX 'Last 7 day average' visual.
    Bars = daily activations, Line = 7-day rolling average.
    """
    x = df["ACTIVATION_DATE"].dt.strftime("%d %b").tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=df["ACTIVATIONS"].tolist(),
        name="Daily Activations",
        marker_color=SONIC_BLUE,
        marker_line_width=0,
        opacity=0.7,
        hovertemplate="%{x}<br><b>Activations: %{y:,}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df["ROLLING_7DAY_AVG"].tolist(),
        name="7-Day Avg",
        mode="lines",
        line=dict(color=HYPERMINT, width=2),
        hovertemplate="%{x}<br><b>7-Day Avg: %{y:,.1f}</b><extra></extra>",
    ))
    layout = _base_layout("Daily Activations & 7-Day Rolling Average")
    layout.update(dict(
        legend=dict(orientation="h", y=1.08, font=dict(color=ZERO_WHITE, size=11),
                    bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    ))
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 6. Filter note
# ─────────────────────────────────────────────────────────────────────────────
if selected_groups:
    st.markdown(
        f"<span style='color:{HIGHVOLT_ORANGE};font-size:12px;'>⬟ Filtered: "
        + ", ".join(selected_groups[:3])
        + ("…" if len(selected_groups) > 3 else "")
        + "</span>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 7. Rolling avg combo chart (full width)
# ─────────────────────────────────────────────────────────────────────────────
st.plotly_chart(
    rolling_combo_chart(rolling_df),
    use_container_width=True,
    config={"displayModeBar": False},
)

# ─────────────────────────────────────────────────────────────────────────────
# 8. Trend charts — 2×2 grid
# ─────────────────────────────────────────────────────────────────────────────
row1_c1, row1_c2 = st.columns(2, gap="medium")
row2_c1, row2_c2 = st.columns(2, gap="medium")

with row1_c1:
    st.plotly_chart(
        spot_bar(
            x=last7_df["ACTIVATION_DATE"].dt.strftime("%a %d %b").tolist(),
            y=last7_df["ACTIVATIONS"].tolist(),
            title="Last 7 Days — Daily Activations",
            colour=HYPERMINT,
        ),
        use_container_width=True, config={"displayModeBar": False},
    )

with row1_c2:
    st.plotly_chart(
        spot_bar(
            x=weekly_df["WEEK_START"].dt.strftime("Wk %d %b '%y").tolist(),
            y=weekly_df["ACTIVATIONS"].tolist(),
            title="Weekly Activations",
            colour=ULTRAVIOLET,
            last_n=26,
        ),
        use_container_width=True, config={"displayModeBar": False},
    )

with row2_c1:
    st.plotly_chart(
        spot_bar(
            x=monthly_df["MONTH_START"].dt.strftime("%b '%y").tolist(),
            y=monthly_df["ACTIVATIONS"].tolist(),
            title="Monthly Activations",
            colour=HIGHVOLT_ORANGE,
            last_n=13,
        ),
        use_container_width=True, config={"displayModeBar": False},
    )

with row2_c2:
    # Daily rolling 13 months (compressed view)
    st.plotly_chart(
        spot_bar(
            x=daily_df["ACTIVATION_DATE"].dt.strftime("%d %b").tolist(),
            y=daily_df["ACTIVATIONS"].tolist(),
            title="Daily Activations (Rolling 13 Months)",
            colour=SONIC_BLUE,
            last_n=90,
        ),
        use_container_width=True, config={"displayModeBar": False},
    )

# ─────────────────────────────────────────────────────────────────────────────
# 9. Sims Never Used & Active 1 — last 90 days (from VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:2px;'>"
    f"SIM Quality Indicators</h3>"
    f"<p style='color:#666; font-size:12px; margin-top:0; margin-bottom:12px;'>"
    f"Source: active subscriptions view &nbsp;·&nbsp; last 90 days by activation date. "
    f"Unaffected by the tenant filter above.</p>",
    unsafe_allow_html=True,
)

snu_c1, snu_c2 = st.columns(2, gap="medium")

with snu_c1:
    fig_snu = go.Figure(go.Bar(
        x=snu_df["DT"].dt.strftime("%d %b").tolist(),
        y=snu_df["SIMS_NEVER_USED"].tolist(),
        marker_color=HIGHVOLT_ORANGE,
        marker_line_width=0,
        hovertemplate="%{x}<br><b>SIMs Never Used: %{y:,}</b><extra></extra>",
    ))
    layout = _base_layout("SIMs Never Used — by Activation Date")
    layout["yaxis"]["title"] = dict(text="Count", font=dict(color="#888", size=11))
    fig_snu.update_layout(**layout)
    st.plotly_chart(fig_snu, use_container_width=True, config={"displayModeBar": False})

with snu_c2:
    fig_a1 = go.Figure(go.Bar(
        x=snu_df["DT"].dt.strftime("%d %b").tolist(),
        y=snu_df["ACTIVE_1"].tolist(),
        marker_color=HYPERMINT,
        marker_line_width=0,
        hovertemplate="%{x}<br><b>Active 1: %{y:,}</b><extra></extra>",
    ))
    layout = _base_layout("Active 1 — by Activation Date")
    layout["yaxis"]["title"] = dict(text="Count", font=dict(color="#888", size=11))
    fig_a1.update_layout(**layout)
    st.plotly_chart(fig_a1, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────────────────────────────────────
# 10. Tenant league tables
# ─────────────────────────────────────────────────────────────────────────────
def group_and_sort(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    d = df.copy()
    d.columns = [c.upper() for c in d.columns]
    value_col = value_col.upper()
    if "TENANT" not in d.columns or value_col not in d.columns:
        return pd.DataFrame(columns=["Tenant", "Activations"])
    d["Tenant"] = d["TENANT"].apply(map_tenant_group)
    grouped = (
        d.groupby("Tenant", as_index=False)[value_col]
        .sum()
        .rename(columns={value_col: "Activations"})
    )
    others = grouped[grouped["Tenant"] == "Other Tenants"]
    rest   = grouped[grouped["Tenant"] != "Other Tenants"].sort_values("Activations", ascending=False)
    result = pd.concat([rest, others], ignore_index=True)
    result.index = range(1, len(result) + 1)
    return result


st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:4px;'>"
    f"Tenant Rankings</h3>"
    f"<p style='color:#666; font-size:12px; margin-top:0;'>"
    f"Best → worst by activations. Unaffected by the tenant filter above.</p>",
    unsafe_allow_html=True,
)

prev_month_label = (month_start - timedelta(days=1)).strftime("%B %Y")
this_month_label = today.strftime("%B %Y")

last_month_by_tenant = group_and_sort(tables_df, "LAST_MONTH")
this_month_by_tenant = group_and_sort(tables_df, "THIS_MONTH")

tc1, spacer, tc2 = st.columns([1, 0.05, 1])


def style_table(df: pd.DataFrame, accent: str) -> str:
    rows = ""
    for rank, row in enumerate(df.itertuples(), 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
        rows += (
            f"<tr>"
            f"<td style='padding:6px 8px; color:#888; font-size:12px;'>{medal}</td>"
            f"<td style='padding:6px 8px; color:{ZERO_WHITE}; font-size:13px;'>{row.Tenant}</td>"
            f"<td style='padding:6px 8px; color:{accent}; font-weight:600; "
            f"font-size:13px; text-align:right;'>{int(row.Activations):,}</td>"
            f"</tr>"
        )
    return f"""
    <table style='width:100%; border-collapse:collapse;
                  background:{SURFACE_1}; border-radius:10px; overflow:hidden;'>
        <thead>
            <tr style='background:{SURFACE_2};'>
                <th style='padding:8px; color:#555; font-size:11px; text-align:left;'>#</th>
                <th style='padding:8px; color:#555; font-size:11px; text-align:left;'>Tenant</th>
                <th style='padding:8px; color:{accent}; font-size:11px; text-align:right;'>
                    Activations</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


with tc1:
    st.markdown(
        f"<div style='color:#888; font-size:12px; text-transform:uppercase; "
        f"letter-spacing:0.08em; margin-bottom:8px;'>{prev_month_label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(style_table(last_month_by_tenant, SONIC_BLUE), unsafe_allow_html=True)

with tc2:
    st.markdown(
        f"<div style='color:#888; font-size:12px; text-transform:uppercase; "
        f"letter-spacing:0.08em; margin-bottom:8px;'>{this_month_label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(style_table(this_month_by_tenant, HYPERMINT), unsafe_allow_html=True)
