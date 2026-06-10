"""
Telco Retail Dashboard — Menu / Home Page
Spot CI  ·  Pack v1
"""
import streamlit as st
from utils.ci import inject_css, HYPERMINT, SONIC_BLUE, ULTRAVIOLET, HIGHVOLT_ORANGE, INKCORE, SURFACE_1, SURFACE_2, BORDER, ZERO_WHITE

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
            <div style='font-size:28px; font-weight:800; color:{HYPERMINT};
                        letter-spacing:-0.03em;'>SPOT</div>
            <div style='font-size:11px; color:#666; letter-spacing:0.12em;
                        text-transform:uppercase; margin-top:2px;'>Connect</div>
        </div>
        <hr style='border-color:{BORDER}; margin:0 0 16px 0;'/>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Use the pages listed below the menu to navigate the dashboard.")

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='padding: 48px 0 8px 0;'>
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
    "Sales Trends": "pages/01_Sales_Trends.py",
}

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
    },
    {
        "icon": "📈",
        "title": "Sales",
        "accent": SONIC_BLUE,
        "pages": [
            "Sales Trends",
            "Quality of Sales by Tenant & Store",
            "SIM Activations & Utilisation",
            "  ↳ New SIM Activations & Utilisation 1–4",
            "Scorecards",
            "  ↳ SPAR · Build It · Mica · Pet Pool & Home",
            "  ↳ Aheers · Fashion Fusion · Progas · Midas",
            "Trading Store Trend",
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
            "Cohort Analysis",
            "  ↳ Telesales Billed/Paid · App Billed/Paid",
        ],
    },
    {
        "icon": "💼",
        "title": "Commercial",
        "accent": "#9b59b6",
        "pages": [
            "Cohort Analysis",
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
    },
]

# ── Render section cards ──────────────────────────────────────────────────────
cols = st.columns(3, gap="medium")

for idx, section in enumerate(SECTIONS):
    col = cols[idx % 3]
    accent = section["accent"]

    def page_item_html(p: str) -> str:
        name = p.strip()
        is_sub = p.startswith(" ")
        if name in NAVIGABLE_PAGES:
            # Derive Streamlit's URL path from the filename
            # e.g. "pages/01_Sales_Trends.py" → "/Sales_Trends"
            url = "/" + NAVIGABLE_PAGES[name].split("/")[-1].replace(".py", "").lstrip("0123456789_")
            return (
                f"<li style='font-size:13px; padding:2px 0;'>"
                f"<a href='{url}' target='_self' style='color:{HYPERMINT}; font-weight:600;"
                f"text-decoration:none;'>{name}</a></li>"
            )
        color = "#aaa" if is_sub else ZERO_WHITE
        return f"<li style='color:{color}; font-size:13px; padding:2px 0;'>{name}</li>"

    pages_html = "".join(page_item_html(p) for p in section["pages"])

    with col:
        st.markdown(
            f"""
            <div style='
                background:{SURFACE_1};
                border:1px solid {BORDER};
                border-top: 3px solid {accent};
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
