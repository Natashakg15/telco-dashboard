"""
Telco Retail Dashboard — Menu / Home Page
Spot CI  ·  Pack v1  ·  40 pages
"""
from datetime import datetime, timedelta, timezone

import streamlit as st
from utils.ci import (
    inject_css, HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE, INKCORE,
    SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE, ON_DARK_TEXT,
)
from utils.snowflake_conn import run_query, MERGE_TABLE

SAST = timezone(timedelta(hours=2))


@st.cache_data(ttl=300, show_spinner=False)
def load_last_refresh():
    """Real data-freshness indicator: latest UPDATE_TIMESTAMP actually written
    to UCONNECT_MAY_MERGE, not just when this page happened to render."""
    df = run_query(f"""
        SELECT
            TO_VARCHAR(MAX(UPDATE_TIMESTAMP), 'YYYY-MM-DD"T"HH24:MI:SS') AS LAST_REFRESH,
            DATEDIFF('minute', MAX(UPDATE_TIMESTAMP), CURRENT_TIMESTAMP()) AS MINUTES_AGO
        FROM {MERGE_TABLE}
    """)
    df.columns = [c.upper() for c in df.columns]
    if df.empty or df.iloc[0]["LAST_REFRESH"] == "demo":
        return None
    return {
        "timestamp_utc": datetime.strptime(df.iloc[0]["LAST_REFRESH"], "%Y-%m-%dT%H:%M:%S"),
        "minutes_ago": int(df.iloc[0]["MINUTES_AGO"]),
    }


def _format_ago(minutes: int) -> str:
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"


st.set_page_config(
    page_title="Telco Retail | Spot Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar nav hint ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style='text-align:center; padding: 24px 0 16px 0;'>
            <span class='spot-logo-pill' style='background:{INKCORE}; font-weight:800;
                         font-size:16px; padding:7px 16px; border-radius:20px;
                         letter-spacing:-0.02em; display:inline-block;'>
                Spot<sup style='font-size:9px; font-weight:700;'>™</sup>
            </span>
            <div style='font-size:11px; color:#666; letter-spacing:0.12em;
                        text-transform:uppercase; margin-top:8px;'>Connect</div>
        </div>
        <hr style='border-color:{BORDER}; margin:0 0 16px 0;'/>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Use the pages listed below the menu to navigate the dashboard.")

# ── Refresh indicator (top-right, real Snowflake data freshness) ──────────────
refresh = load_last_refresh()
_, refresh_col = st.columns([3, 2])
with refresh_col:
    if refresh:
        sast_time = refresh["timestamp_utc"].replace(tzinfo=timezone.utc).astimezone(SAST)
        st.markdown(
            f"<div style='text-align:right; font-size:12px; color:#666; padding-top:12px;'>"
            f"<span style='color:{HYPERMINT};'>●</span> Refreshed {_format_ago(refresh['minutes_ago'])} "
            f"&nbsp;·&nbsp; {sast_time.strftime('%d %b %Y at %H:%M')} SAST</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='text-align:right; font-size:12px; color:#666; padding-top:12px;'>"
            f"<span style='color:#999;'>●</span> Demo data — not live</div>",
            unsafe_allow_html=True,
        )

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='padding: 8px 0 8px 0;'>
        <div style='font-size: 13px; color:#666; letter-spacing:0.14em;
                    text-transform:uppercase; margin-bottom:8px;'>
            SPOT CONNECT
        </div>
        <h1 style='font-size:56px; font-weight:800; letter-spacing:-0.03em;
                   margin:0; line-height:1.05;'>
            Telco Retail
        </h1>
        <div style='display:flex; align-items:center; gap:12px; margin-top:12px;'>
            <span style='background:{HYPERMINT}; color:{INKCORE}; font-size:11px;
                         font-weight:700; padding:3px 10px; border-radius:20px;
                         letter-spacing:0.06em;'>PACK v1</span>
            <span style='color:#555; font-size:13px;'>Business Custodian: Siddeek Rahim</span>
        </div>
    </div>
    <div class="spot-rule" style='margin-top:24px;'></div>
    """,
    unsafe_allow_html=True,
)

# ── Intro copy ────────────────────────────────────────────────────────────────
st.markdown(
    "<p style='color:#888; max-width:680px; font-size:15px; margin-bottom:40px;'>"
    "This digital booklet consolidates Spot's Telco Retail analytics across strategy, "
    "sales, subscriptions, commercial activity, recharges and financials. "
    "Navigate via the sidebar or the section cards below."
    "</p>",
    unsafe_allow_html=True,
)

# ── Pages with live implementations ──────────────────────────────────────────
NAVIGABLE_PAGES = {
    # Strategy & Book
    "Exco Scorecard":                     "pages/33_Exco_Scorecard.py",
    "Spot Connect Book":                  "pages/34_Spot_Connect_Book.py",
    "OKR Scorecard":                      "pages/35_OKR_Scorecard.py",
    "OKR Trends":                         "pages/36_OKR_Trends.py",
    "Revenue Trends":                     "pages/37_Revenue_Trends.py",
    "Voice Usage by Tenant":              "pages/38_Voice_Usage_Tenant.py",
    "Data Usage by Tenant":               "pages/39_Data_Usage_Tenant.py",
    "Retain Users via Free Airtime":      "pages/40_Retain_Users_Airtime.py",
    # Sales
    "Sales Trends":                       "pages/01_Sales_Trends.py",
    "Quality of Sales by Tenant & Store": "pages/02_Quality_of_Sales.py",
    "SIM Activations & Utilisation":      "pages/11_SIM_Activations_Utilisation.py",
    "Trading Store Trend":                "pages/12_Trading_Store_Trend.py",
    "Pipeline & Provisional Commissions": "pages/13_Pipeline_Commissions.py",
    "↳ Spar":                             "pages/03_Spar_Scorecard.py",
    "↳ Build It":                         "pages/04_Build_It_Scorecard.py",
    "↳ Mica":                             "pages/05_Mica_Scorecard.py",
    "↳ Pet Pool & Home":                  "pages/06_Pet_Pool_Scorecard.py",
    "↳ Aheers":                           "pages/07_Aheers_Scorecard.py",
    "↳ Fashion Fusion":                   "pages/08_Fashion_Fusion_Scorecard.py",
    "↳ Progas":                           "pages/09_Progas_Scorecard.py",
    "↳ Midas":                            "pages/10_Midas_Scorecard.py",
    # Subscriptions
    "Subscriptions":                      "pages/14_Subscriptions.py",
    "↳ Telesales · App · WhatsApp · BTL": "pages/14_Subscriptions.py",
    "↳ Mobile Store · Mobile Store DigiM VAS": "pages/14_Subscriptions.py",
    "Subscriptions Cohort Analysis":      "pages/15_Subscriptions_Cohort.py",
    "↳ Telesales Billed/Paid · App Billed/Paid": "pages/15_Subscriptions_Cohort.py",
    # Commercial
    "Commercial Cohort Analysis":         "pages/16_Commercial_Cohort.py",
    "Wastage":                            "pages/17_Wastage.py",
    "Pargo Collections":                  "pages/18_Pargo_Collections.py",
    # Recharges
    "Recharge Qty Dash":                  "pages/19_Recharge_Qty_Dash.py",
    "Recharge Trend by Recharge Type":    "pages/20_Recharge_Trend_Type.py",
    "Recharge Revenue Monthly":           "pages/21_Recharge_Revenue_Monthly.py",
    "Revenue Comparisons":                "pages/22_Revenue_Comparisons.py",
    "Prepaid Recharge Projection":        "pages/23_Prepaid_Recharge_Projection.py",
    # Financials
    "Income Statement":                   "pages/24_Income_Statement.py",
    "Income Statement Summary":           "pages/25_Income_Statement_Summary.py",
    "Revenue Metrics":                    "pages/26_Revenue_Metrics.py",
    "Margin Efficiency Metrics":          "pages/27_Margin_Efficiency.py",
    "Cost of Sale Metrics":               "pages/28_Cost_of_Sale.py",
    "Opex Metrics":                       "pages/29_Opex_Metrics.py",
    "Acquisition Cost Metrics":           "pages/30_Acquisition_Cost.py",
    "Forward 12 & Trailing 12":           "pages/31_Forward_12_Trailing_12.py",
    "Value of New Business":              "pages/32_Value_New_Business.py",
}

# ── Build slug → page file lookup (used by nav intercept) ────────────────────
SLUG_TO_FILE = {
    v.split("/")[-1].replace(".py", "").lstrip("0123456789_"): v
    for v in NAVIGABLE_PAGES.values()
}

# ── Navigation intercept — must run before any rendering ─────────────────────
_go = st.query_params.get("go")
if _go and _go in SLUG_TO_FILE:
    st.switch_page(SLUG_TO_FILE[_go])

# ── Section card data ─────────────────────────────────────────────────────────
SECTIONS = [
    {
        "icon": "🎯",
        "title": "Strategy & Book",
        "accent": HYPERMINT,
        "pages": [
            "Exco Scorecard",
            "Spot Connect Book",
            "OKR Scorecard",
            "OKR Trends",
            "Revenue Trends",
            "Voice Usage by Tenant",
            "Data Usage by Tenant",
            "Retain Users via Free Airtime",
        ],
        "note": "Revenue Trends · Retain Users = live data",
    },
    {
        "icon": "📈",
        "title": "Sales",
        "accent": SONIC_BLUE,
        "pages": [
            "Sales Trends",
            "Quality of Sales by Tenant & Store",
            "SIM Activations & Utilisation",
            "Trading Store Trend",
            "Scorecards",
            "↳ Spar",
            "↳ Build It",
            "↳ Mica",
            "↳ Pet Pool & Home",
            "↳ Aheers",
            "↳ Fashion Fusion",
            "↳ Progas",
            "↳ Midas",
            "Pipeline & Provisional Commissions",
        ],
    },
    {
        "icon": "🔄",
        "title": "Subscriptions",
        "accent": ULTRAVIOLET,
        "pages": [
            "Subscriptions",
            "  ↳ Telesales · App · WhatsApp · BTL",
            "  ↳ Mobile Store · Mobile Store DigiM VAS",
            "Subscriptions Cohort Analysis",
            "  ↳ Telesales Billed/Paid · App Billed/Paid",
        ],
    },
    {
        "icon": "💼",
        "title": "Commercial",
        "accent": "#9b59b6",
        "pages": [
            "Commercial Cohort Analysis",
            "  ↳ Revenue Cohort · Cohorts 1/2/3 (Acq & Active)",
            "Wastage",
            "Pargo Collections",
        ],
    },
    {
        "icon": "⚡",
        "title": "Recharges",
        "accent": HIGHVOLT_ORANGE,
        "pages": [
            "Recharge Qty Dash",
            "Recharge Trend by Recharge Type",
            "Recharge Revenue Monthly",
            "Revenue Comparisons",
            "Prepaid Recharge Projection",
        ],
    },
    {
        "icon": "💰",
        "title": "Financials",
        "accent": "#f1c40f",
        "pages": [
            "Income Statement",
            "Income Statement Summary",
            "Revenue Metrics",
            "Margin Efficiency Metrics",
            "Cost of Sale Metrics",
            "Opex Metrics",
            "Acquisition Cost Metrics",
            "Forward 12 & Trailing 12",
            "Value of New Business",
        ],
        "note": "Income Statement → Opex Metrics = live (Excel snapshot, manual refresh). "
                 "Value of New Business still pending cohort data.",
    },
]

# ── Render section cards ──────────────────────────────────────────────────────
cols = st.columns(3, gap="medium")

for idx, section in enumerate(SECTIONS):
    col = cols[idx % 3]
    accent = section["accent"]

    def page_item_html(p: str) -> str:
        name = p.strip()
        is_sub = p.startswith(" ") or (len(p) > 0 and p[0] == "↳")
        indent = "padding-left:14px;" if is_sub else ""
        if name in NAVIGABLE_PAGES:
            slug = NAVIGABLE_PAGES[name].split("/")[-1].replace(".py", "").lstrip("0123456789_")
            return (
                f"<li style='padding:2px 0; {indent}'>"
                f"<a href='?go={slug}' style='color:{ZERO_WHITE}; font-weight:600; "
                f"font-size:13px; text-decoration:none;'>{name}</a></li>"
            )
        color = "#555" if is_sub else "#888"
        return f"<li style='color:{color}; font-size:13px; padding:2px 0; {indent}'>{name}</li>"

    pages_html = "".join(page_item_html(p) for p in section["pages"])

    with col:
        st.markdown(
            f"""
            <div style='
                background:{SURFACE_1};
                border:1px solid {BORDER};
                border-top:3px solid {accent};
                border-radius:12px;
                padding:20px 22px 22px 22px;
                margin-bottom:20px;
                min-height:280px;
            '>
                <div style='display:flex; align-items:center; gap:10px; margin-bottom:12px;'>
                    <span style='font-size:22px;'>{section["icon"]}</span>
                    <span style='font-size:16px; font-weight:700;
                                 color:{accent};'>{section["title"]}</span>
                </div>
                <ul style='margin:0; padding-left:16px; list-style:disc;'>
                    {pages_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <hr style='border-color:{BORDER}; margin:40px 0 16px 0;'/>
    <div style='display:flex; justify-content:space-between; align-items:center;'>
        <div>
            <span style='color:{HYPERMINT}; font-weight:700; font-size:14px;'>SPOT</span>
            <span style='color:#555; font-size:13px; margin-left:8px;'>Telco Retail · Pack v1</span>
        </div>
        <div style='color:#555; font-size:12px;'>
            Business Custodian: Siddeek Rahim &nbsp;·&nbsp; Powered by Snowflake
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
