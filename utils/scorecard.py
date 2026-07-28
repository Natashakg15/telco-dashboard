"""
Shared scorecard rendering utility.
Each tenant scorecard page passes a config dict and calls render_scorecard().
Cached loaders are module-level so Streamlit caches per unique SQL string.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.ci import (
    HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE,
    SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE,
    inject_css, page_header,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

USAGE_TABLE = "UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS"


# ── Cached data loaders (keyed by the WHERE string so each tenant is separate) ─

@st.cache_data(ttl=1800, show_spinner=False)
def _load_monthly(where_merge: str) -> pd.DataFrame:
    df = run_query(f"""
        SELECT
            DATE_TRUNC('month', ACTIVATION_DATE) AS MONTH_START,
            COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE {where_merge}
          AND ACTIVATION_DATE >= DATEADD(month, -13, CURRENT_DATE())
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    if "MONTH_START" not in df.columns and "ACTIVATION_DATE" in df.columns:
        df = df.rename(columns={"ACTIVATION_DATE": "MONTH_START"})
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def _load_daily(where_merge: str) -> pd.DataFrame:
    df = run_query(f"""
        SELECT
            ACTIVATION_DATE,
            COUNT(*) AS ACTIVATIONS
        FROM {MERGE_TABLE}
        WHERE {where_merge}
          AND ACTIVATION_DATE >= CURRENT_DATE() - 90
        GROUP BY 1 ORDER BY 1
    """)
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def _load_quality(where_usage: str) -> pd.Series:
    df = run_query(f"""
        SELECT
            SUM(CASE WHEN USAGE_0_30_DAYS = '1'         THEN 1 ELSE 0 END) AS ACTIVE_1_COUNT,
            COUNT(*)                                                         AS TOTAL_SIMS,
            SUM(CASE WHEN USAGE_0_30_DAYS = '1' THEN 1 ELSE 0 END)::FLOAT
                / NULLIF(COUNT(*), 0)                                        AS ACTIVE_1_PCT,
            SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) BETWEEN CURRENT_DATE()-60
                                                      AND CURRENT_DATE()-35
                          AND DAYS_SINCE_LAST_USAGE = 'SIM Never Used'
                     THEN 1 ELSE 0 END)                                      AS SIMS_NEVER_USED,
            SUM(CASE WHEN DATE(ACCOUNTCREATEDATE) BETWEEN CURRENT_DATE()-60
                                                      AND CURRENT_DATE()-35
                     THEN 1 ELSE 0 END)                                      AS REGISTERED_BASE_35_60,
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
        WHERE {where_usage}
    """)
    df.columns = [c.upper() for c in df.columns]
    if df.empty:
        return pd.Series(dtype=float)
    row = df.iloc[0]
    reg_base = row.get("REGISTERED_BASE_35_60")
    row["SIMS_NEVER_USED_PCT"] = (
        row.get("SIMS_NEVER_USED", 0) / reg_base if reg_base else None
    )
    return row


@st.cache_data(ttl=1800, show_spinner=False)
def _load_ros_7day(where_merge: str, excluded_stores: tuple) -> float | None:
    """
    ROS (Rate of Sale) 7-day avg — matches PBIX 'ROS_L7 DAYS SQL <tenant>' native queries:
    distinct activating accounts over a trailing 7-calendar-day window (today-6..today),
    divided by 6. Only defined in the source model for Spar, Build It, Pet Pool, Fashion Fusion.
    """
    excl_clause = ""
    if excluded_stores:
        vals = ", ".join("'" + s.replace("'", "''") + "'" for s in excluded_stores)
        excl_clause = f"AND TENANT NOT IN ({vals})"
    df = run_query(f"""
        SELECT ROUND(COUNT(DISTINCT ACCOUNT_NUMBER) / 6.0, 2) AS ROS_7_DAYS
        FROM {MERGE_TABLE}
        WHERE ({where_merge})
          AND MASTER_TENANT = 'uConnect'
          {excl_clause}
          AND ACTIVATION_DATE BETWEEN DATEADD(day, -6, CURRENT_DATE()) AND CURRENT_DATE()
    """)
    df.columns = [c.upper() for c in df.columns]
    if df.empty:
        return None
    val = df.iloc[0].get("ROS_7_DAYS")
    return None if val is None or pd.isna(val) else float(val)


# Rate of Sale flag thresholds — verified from the PBIX's native ROS_L7 DAYS SQL <tenant> queries.
# Not defined in the source model for the other 4 scorecards (Mica, Aheers, Progas, Midas).
ROS_THRESHOLD = {
    "Spar": 30,
    "Build It": 26,
    "Pet Pool & Home": 20,
    "Fashion Fusion": 30,
}

# Store exclusion lists — verified from the same queries (store-level opt-outs, e.g. duplicates
# or "DO NOT USE" entries). Pet Pool and Fashion Fusion have none defined in the source.
ROS_EXCLUDED_STORES = {
    "Spar": (
        "Spar Mbazwana", "Spar Kei (Spargs)", "Spar Jozini", "Spar Durban Central",
        "Spar Mandini Tops(DO NOT USE FOR ANYTHING)", "Spar Ephondweni", "Spar Avonmore",
        "Spar Hlabisa", "Spar KosiBay", "Spar Mtunzini", "Spar Kensington",
        "Spar Ikwezi (Spargs)", "Spar Bhambanana", "Spar Dutywa 2 (Spargs)",
        "Spar Mandini (Foodlovers)", "Spar Bhambanana 2", "Spar Mduku", "Spar Shaluza",
        "Spar Nyakaza", "Savemor Bhambanana 2", "Spar Ingwavuma", "Spar Ndumu",
        "Spar Pongola", "Spar Spencers (Spargs)", "Spar Umzimkhulu", "Spar Beacon Bay (Spargs)",
        "Spar Beacon Bay 2 (Spargs)", "Spar Belair", "Spar Duzi", "Spar Golden Gate",
        "Spar Harding", "Spar Hibberdene", "Spar Ixopo", "Spar Knowles", "Spar Manaba",
        "Spar Marina", "Spar Olivedale", "Spar Parys", "Spar Phoenix", "Spar Saint George",
        "Spar Seapoint", "Spar Selgro", "Spar Sutherland 2 (Spargs)", "Spar Umkomaas",
        "Spar Umlazi", "Spar Waterloo", "Spar West Street", "Spar Winklespruit",
    ),
    "Build It": ("Bothas Hill", "Cullinan", "KwaMlanga", "Mthatha (Spargs)", "Southway Mall"),
    "Pet Pool & Home": (),
    "Fashion Fusion": (),
}

# Cost-of-wastage unit rates (Rand per SIM never used, +6 fixed) — verified from the PBIX
# 'Cost of Wastage <tenant>' measures. Only Spar and Build It among the 8 scorecards have a
# rate defined in the source model; Savemor's rate (15.07) is distinct from Spar's (16.69) but
# this dashboard's Spar page already groups Savemor into "Spar", matching the existing where_merge.
WASTAGE_RATE = {
    "Spar": 16.69,
    "Build It": 18.50,
}


@st.cache_data(ttl=1800, show_spinner=False)
def _load_stores(where_merge: str) -> pd.DataFrame:
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
        WHERE {where_merge}
          AND ACTIVATION_DATE >= DATE_TRUNC('month', DATEADD(month,-1,CURRENT_DATE()))
        GROUP BY 1
        ORDER BY THIS_MONTH DESC
    """)
    df.columns = [c.upper() for c in df.columns]
    df = df.rename(columns={
        "TENANT": "Tenant",
        "THIS_MONTH": "This Month",
        "LAST_MONTH": "Last Month",
    })
    return df


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _fmt_pct(val):
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


def _placeholder_card(label: str, source: str):
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


def _placeholder_chart(title: str, source: str, height: int = 300):
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


def _store_table_html(df: pd.DataFrame) -> str:
    col_order = ["#", "Tenant", "This Month", "Last Month", "QOS 7D Avg", "ROS 7D Avg", "Avg Vouchers"]
    display = df.copy()
    display.insert(0, "#", range(1, len(display) + 1))
    display["QOS 7D Avg"]   = "—"
    display["ROS 7D Avg"]   = "—"
    display["Avg Vouchers"] = "—"

    header = "".join(
        f"<th style='padding:8px 10px; color:#555; font-size:11px; background:{SURFACE_2}; "
        f"text-align:{'left' if i < 2 else 'right'};'>{c}</th>"
        for i, c in enumerate(col_order)
    )
    rows = ""
    for _, row in display.iterrows():
        cells = ""
        for i, col in enumerate(col_order):
            val = row[col]
            align = "left" if i < 2 else "right"
            if col == "#":
                color, val_str = "#555", str(int(val))
            elif col == "Tenant":
                color, val_str = ZERO_WHITE, str(val)
            elif col == "This Month":
                color, val_str = HYPERMINT, f"{int(val):,}"
            elif col == "Last Month":
                color, val_str = SONIC_BLUE, f"{int(val):,}"
            else:
                color, val_str = "#444", "—"
            cells += (
                f"<td style='padding:6px 10px; color:{color}; font-size:12px; "
                f"text-align:{align};'>{val_str}</td>"
            )
        rows += f"<tr>{cells}</tr>"

    return (
        f"<div style='overflow-x:auto;'>"
        f"<table style='width:100%; border-collapse:collapse; background:{SURFACE_1}; "
        f"border-radius:10px; overflow:hidden;'>"
        f"<thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div>"
    )


# ── Main render function ───────────────────────────────────────────────────────

def render_scorecard(cfg: dict):
    """
    cfg keys:
      name         str   — display name e.g. "Build It"
      where_merge  str   — SQL WHERE fragment for UCONNECT_MAY_MERGE
      where_usage  str   — SQL WHERE fragment for VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS
    """
    inject_css()
    st.page_link("app.py", label="← Back to Menu")
    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
    page_header(f"{cfg['name']} Scorecard", badge="Scorecard")

    name         = cfg["name"]
    where_merge  = cfg["where_merge"]
    where_usage  = cfg["where_usage"]

    # ── Load data ──────────────────────────────────────────────────────────────
    with st.spinner(f"Loading {name} data…"):
        monthly_df = _load_monthly(where_merge)
        daily_df   = _load_daily(where_merge)
        quality    = _load_quality(where_usage)
        store_df   = _load_stores(where_merge)
        ros_7day   = (
            _load_ros_7day(where_merge, ROS_EXCLUDED_STORES.get(name, ()))
            if name in ROS_THRESHOLD else None
        )

    monthly_df["MONTH_START"]   = pd.to_datetime(monthly_df["MONTH_START"])
    daily_df["ACTIVATION_DATE"] = pd.to_datetime(daily_df["ACTIVATION_DATE"])

    today        = date.today()
    month_start  = today.replace(day=1)
    prev_m_label = (month_start - timedelta(days=1)).strftime("%B %Y")
    this_m_label = today.strftime("%B %Y")

    this_month = int(monthly_df.iloc[-1]["ACTIVATIONS"]) if not monthly_df.empty else 0
    last_month = int(monthly_df.iloc[-2]["ACTIVATIONS"]) if len(monthly_df) >= 2 else 0
    mom_delta  = this_month - last_month

    # ── 1. KPI strip ──────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("This Month",      f"{this_month:,}")
    k2.metric("Last Month",      f"{last_month:,}", delta=f"{mom_delta:+,}")
    k3.metric("Active 1 %",      _fmt_pct(quality.get("ACTIVE_1_PCT")))
    snu_count = int(quality.get("SIMS_NEVER_USED", 0) or 0)
    k4.metric(
        "SIMs Never Used (35-60d)", f"{snu_count:,}",
        help="Accounts created 35-60 days ago with no usage since — matches the PBIX definition "
             "(previously this card used a different, unwindowed condition).",
        delta=_fmt_pct(quality.get("SIMS_NEVER_USED_PCT")), delta_color="off",
    )
    with k5:
        _placeholder_card("QOS 7-Day Avg", "NEW QOS table")
    with k6:
        if ros_7day is not None:
            threshold = ROS_THRESHOLD[name]
            at_risk = ros_7day < threshold
            k6.metric(
                "ROS 7-Day Avg", f"{ros_7day:,.2f}",
                help=f"Distinct activations over the trailing 7 days, ÷6. Flagged if below {threshold}.",
                delta="Below threshold" if at_risk else "On target",
                delta_color="inverse" if at_risk else "normal",
            )
        else:
            _placeholder_card("ROS 7-Day Avg", "ROS_L7 DAYS SQL — not built for this tenant")

    wastage_rate = WASTAGE_RATE.get(name)
    if wastage_rate is not None:
        wk1, _ = st.columns([1, 5])
        wk1.metric(
            "Cost of Wastage", f"R{(snu_count * wastage_rate + 6):,.0f}",
            help=f"(SIMs Never Used × R{wastage_rate}) + R6 fixed cost — matches the PBIX "
                 f"'Cost of Wastage {name}' measure.",
        )

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    # ── 2. Rolling avg combo + sales per day placeholder ──────────────────────
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        if not daily_df.empty:
            rolling = (
                daily_df.set_index("ACTIVATION_DATE")
                .reindex(pd.date_range(daily_df["ACTIVATION_DATE"].min(),
                                       daily_df["ACTIVATION_DATE"].max()))
                .rename_axis("ACTIVATION_DATE").fillna(0).reset_index()
            )
            rolling["ROLLING_7DAY_AVG"] = (
                rolling["ACTIVATIONS"].rolling(7, min_periods=1).mean().round(1)
            )
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
            layout = _base_layout(f"Daily Activations & 7-Day Rolling Avg — {name} (90 Days)")
            layout.update(dict(
                legend=dict(orientation="h", y=1.08,
                            font=dict(color=ZERO_WHITE, size=11),
                            bgcolor="rgba(0,0,0,0)"),
                hovermode="x unified",
            ))
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            _placeholder_chart(f"Daily Activations — {name}", "No data yet", height=310)

    with c2:
        _placeholder_chart(
            f"Sales Per Day (Avg) — {name}",
            "NEW QOS, ROS, SNU, AVG Vouchers",
            height=310,
        )

    # ── 3. Monthly activations + voucher redemptions placeholder ──────────────
    c3, c4 = st.columns(2, gap="medium")

    with c3:
        if not monthly_df.empty:
            fig_m = go.Figure(go.Bar(
                x=monthly_df["MONTH_START"].dt.strftime("%b '%y").tolist(),
                y=monthly_df["ACTIVATIONS"].tolist(),
                marker_color=HIGHVOLT_ORANGE, marker_line_width=0,
                hovertemplate="%{x}<br><b>Activations: %{y:,}</b><extra></extra>",
            ))
            fig_m.update_layout(**_base_layout(f"Monthly Activations — {name} (13 Months)"))
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
        else:
            _placeholder_chart(f"Monthly Activations — {name}", "No data yet", height=310)

    with c4:
        _placeholder_chart(
            f"L12 Month Voucher Redemptions — {name}",
            "L12 month voucher redemptions",
            height=310,
        )

    # ── 4. Cohort revenue placeholders ────────────────────────────────────────
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:12px;'>"
        f"Cohort Revenue Analysis</h3>",
        unsafe_allow_html=True,
    )
    ch1, ch2 = st.columns(2, gap="medium")
    with ch1:
        _placeholder_chart(
            "Average Revenue per Acquired — by Cohort Month",
            "COHORT table", height=280,
        )
    with ch2:
        _placeholder_chart(
            "Total Margin — by Cohort Month",
            "COHORT table", height=280,
        )

    # ── 5. Store table ─────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='color:{HYPERMINT}; font-size:15px; margin-bottom:4px;'>"
        f"Store Performance</h3>"
        f"<p style='color:#666; font-size:12px; margin-top:0; margin-bottom:12px;'>"
        f"QOS / ROS / voucher columns pending "
        f"<span style='color:{HIGHVOLT_ORANGE};'>NEW QOS, ROS, SNU, AVG Vouchers</span> "
        f"data access. Activations are live.</p>",
        unsafe_allow_html=True,
    )
    if not store_df.empty:
        st.markdown(_store_table_html(store_df), unsafe_allow_html=True)
    else:
        st.info("No store data available for the current period.")
