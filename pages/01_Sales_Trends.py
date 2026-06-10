"""
Sales Trends — Page 1 of Sales section
Data source: UCONNECT_DW.ANALYTICS.UCONNECT_MAY_MERGE
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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Trends | Telco Retail",
    page_icon="📈",
    layout="wide",
)
inject_css()
page_header("Sales Trends", badge="Sales")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Tenant list (for filter)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_tenants():
    df = run_query(f"""
        SELECT DISTINCT TENANT
        FROM {MERGE_TABLE}
        WHERE TENANT IS NOT NULL AND TENANT != ''
        ORDER BY TENANT
    """)
    col = "TENANT" if "TENANT" in df.columns else df.columns[0]
    return df[col].tolist()

all_tenants = load_tenants()

# ─────────────────────────────────────────────────────────────────────────────
# 2. Tenant filter (only affects bar charts)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='color:{HYPERMINT}; font-weight:700; font-size:13px; "
        f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
        f"Tenant Filter</div>",
        unsafe_allow_html=True,
    )
    st.caption("Filters the trend charts only. Tables are unaffected.")
    selected_tenants = st.multiselect(
        "Select tenants",
        options=all_tenants,
        default=[],
        placeholder="All tenants",
        label_visibility="collapsed",
    )

tenant_clause = (
    f"AND TENANT IN ({', '.join(repr(t) for t in selected_tenants)})"
    if selected_tenants else ""
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Load trend data (filtered by tenant selection)
# ─────────────────────────────────────────────────────────────────────────────
today = date.today()
last_7_start  = today - timedelta(days=6)
month_start   = today.replace(day=1)
prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

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
    """Tenant tables are NEVER filtered — always show full picture."""
    return run_query(f"""
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
        ORDER BY LAST_MONTH DESC
    """)

daily_df   = load_daily(tenant_clause)
tables_df  = load_tables_data()

daily_df["ACTIVATION_DATE"] = pd.to_datetime(daily_df["ACTIVATION_DATE"])

# ─────────────────────────────────────────────────────────────────────────────
# 4. Derived aggregations
# ─────────────────────────────────────────────────────────────────────────────
# Weekly
weekly_df = (
    daily_df.set_index("ACTIVATION_DATE")
    .resample("W-MON", label="left", closed="left")["ACTIVATIONS"]
    .sum()
    .reset_index()
    .rename(columns={"ACTIVATION_DATE": "WEEK_START"})
)

# Monthly
monthly_df = (
    daily_df.set_index("ACTIVATION_DATE")
    .resample("MS")["ACTIVATIONS"]
    .sum()
    .reset_index()
    .rename(columns={"ACTIVATION_DATE": "MONTH_START"})
)

# Last 7 days
last7_df = daily_df[daily_df["ACTIVATION_DATE"] >= pd.Timestamp(last_7_start)]

# ─────────────────────────────────────────────────────────────────────────────
# 5. KPI strip
# ─────────────────────────────────────────────────────────────────────────────
this_month_total  = int(monthly_df.iloc[-1]["ACTIVATIONS"]) if not monthly_df.empty else 0
last_month_total  = int(monthly_df.iloc[-2]["ACTIVATIONS"]) if len(monthly_df) >= 2 else 0
last7_total       = int(last7_df["ACTIVATIONS"].sum())
today_total_raw   = daily_df[daily_df["ACTIVATION_DATE"] == pd.Timestamp(today)]
today_total       = int(today_total_raw["ACTIVATIONS"].iloc[0]) if not today_total_raw.empty else 0
mom_delta         = this_month_total - last_month_total

k1, k2, k3, k4 = st.columns(4)
k1.metric("Today", f"{today_total:,}")
k2.metric("Last 7 Days", f"{last7_total:,}")
k3.metric("This Month", f"{this_month_total:,}")
k4.metric("vs Last Month", f"{last_month_total:,}", delta=f"{mom_delta:+,}")

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Helper: Spot-styled bar chart
# ─────────────────────────────────────────────────────────────────────────────
def spot_bar(x, y, title, x_label="", colour=HYPERMINT, last_n=None):
    if last_n:
        x, y = x[-last_n:], y[-last_n:]
    fig = go.Figure(
        go.Bar(
            x=x, y=y,
            marker_color=colour,
            marker_line_width=0,
            hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color=ZERO_WHITE, size=14), x=0),
        paper_bgcolor=SURFACE_1,
        plot_bgcolor=SURFACE_1,
        font=dict(color="#888", size=11),
        margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(
            showgrid=False,
            linecolor=BORDER,
            tickfont=dict(size=10, color="#888"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=BORDER,
            linecolor="rgba(0,0,0,0)",
            tickformat=",",
        ),
        bargap=0.3,
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# 7. Trend charts — 2×2 grid
# ─────────────────────────────────────────────────────────────────────────────
filter_note = (
    f"<span style='color:{HIGHVOLT_ORANGE};font-size:12px;'>⬟ Filtered: "
    + ", ".join(selected_tenants[:3])
    + ("…" if len(selected_tenants) > 3 else "")
    + "</span>"
    if selected_tenants
    else ""
)
if filter_note:
    st.markdown(filter_note, unsafe_allow_html=True)

row1_c1, row1_c2 = st.columns(2, gap="medium")
row2_c1, row2_c2 = st.columns(2, gap="medium")

with row1_c1:
    fig = spot_bar(
        x=last7_df["ACTIVATION_DATE"].dt.strftime("%a %d %b").tolist(),
        y=last7_df["ACTIVATIONS"].tolist(),
        title="Last 7 Days — Daily Activations",
        colour=HYPERMINT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with row1_c2:
    fig = spot_bar(
        x=daily_df["ACTIVATION_DATE"].dt.strftime("%d %b").tolist(),
        y=daily_df["ACTIVATIONS"].tolist(),
        title="Daily Activations (Rolling 13 Months)",
        colour=SONIC_BLUE,
        last_n=90,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with row2_c1:
    fig = spot_bar(
        x=weekly_df["WEEK_START"].dt.strftime("Wk %d %b '%y").tolist(),
        y=weekly_df["ACTIVATIONS"].tolist(),
        title="Weekly Activations",
        colour=ULTRAVIOLET,
        last_n=26,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with row2_c2:
    fig = spot_bar(
        x=monthly_df["MONTH_START"].dt.strftime("%b '%y").tolist(),
        y=monthly_df["ACTIVATIONS"].tolist(),
        title="Monthly Activations",
        colour=HIGHVOLT_ORANGE,
        last_n=13,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────────────────────────────────────
# 8. Tenant league tables — NOT affected by filter
# ─────────────────────────────────────────────────────────────────────────────

def map_tenant_group(name: str) -> str:
    """Group raw tenant names into canonical buckets, matching Power Query logic."""
    n = name or ""
    if "Build It" in n or "Build IT" in n or "Build it" in n:
        return "Build It"
    if "Mica" in n:
        return "Mica"
    if "Midas" in n or "ACA" in n or "Greenfields" in n:
        return "Midas"
    if "Pet Pool & Home" in n:
        return "Pet Pool & Home"
    if "Progas" in n:
        return "Progas"
    if "Ladysmith Office National" in n:
        return "Ladysmith Office National"
    if "Spargs" in n or "Savemor" in n or "Spar" in n:
        return "Spar Retail"
    if "Fashion" in n:
        return "Fashion Fusion"
    if n == "The Unlimited":
        return "The Unlimited"
    if n == "Halaala":
        return "Halaala"
    if n == "Mobile Store":
        return "Mobile Store"
    if n == "Spot Airtime Rewards" or "Deals Direct" in n:
        return "NRP"
    if n == "OnAir":
        return "OnAir"
    if n == "OnAir Connect 50":
        return "OnAir Non Sales"
    if "AllLife" in n:
        return "AllLife"
    if n in ("uConnect App", "uConnect Digital"):
        return "uConnect App & Digital"
    if "Aheers" in n:
        return "Aheers"
    if n == "Spot Mobile":
        return "Spot Mobile"
    if n == "Me&You":
        return "Me&You"
    if n == "KR Motor Spares Bothas Hill" or n == "KR Motor Spares - Midas" or n == "ACA Auto parts":
        return "Midas"
    if n == "Greenfields Hardware":
        return "Mica"
    if "On Tap" in n:
        return "On Tap"
    return "Other Tenants"


def group_and_sort(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    df = df.copy()
    df["Tenant"] = df["TENANT"].apply(map_tenant_group)
    grouped = (
        df.groupby("Tenant", as_index=False)[value_col]
        .sum()
        .rename(columns={value_col: "Activations"})
    )
    others = grouped[grouped["Tenant"] == "Other Tenants"]
    rest = grouped[grouped["Tenant"] != "Other Tenants"].sort_values("Activations", ascending=False)
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

# Validate: the totals in these tables should match the monthly bar chart values
# (both come from the same unfiltered query)

tc1, spacer, tc2 = st.columns([1, 0.05, 1])

def style_table(df: pd.DataFrame, accent: str) -> str:
    """Return a simple HTML table styled to Spot CI."""
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
    st.markdown(
        style_table(last_month_by_tenant.head(20), SONIC_BLUE),
        unsafe_allow_html=True,
    )

with tc2:
    st.markdown(
        f"<div style='color:#888; font-size:12px; text-transform:uppercase; "
        f"letter-spacing:0.08em; margin-bottom:8px;'>{this_month_label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        style_table(this_month_by_tenant.head(20), HYPERMINT),
        unsafe_allow_html=True,
    )
