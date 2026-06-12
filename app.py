"""
Telco Retail Dashboard — Menu / Home Page
Spot CI  ·  Pack v1  ·  40 pages
"""
import streamlit as st
import streamlit.components.v1 as components
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
    "Subscriptions Cohort Analysis":      "pages/15_Subscriptions_Cohort.py",
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
    },
]

# ── Render section cards ──────────────────────────────────────────────────────
cols = st.columns(3, gap="medium")

for idx, section in enumerate(SECTIONS):
    col = cols[idx % 3]
    accent = section["accent"]

    # Build items HTML + JS navigation map
    items_html = ""
    nav_map = {}   # label → url path
    for p in section["pages"]:
        name = p.strip()
        is_sub = p.startswith(" ") or (len(p) > 0 and p[0] == "↳")
        indent = "padding-left:14px;" if is_sub else ""
        if name in NAVIGABLE_PAGES:
            filepath = NAVIGABLE_PAGES[name].split("/")[-1].replace(".py", "").lstrip("0123456789_")
            url = f"/{filepath}"
            nav_map[name] = url
            safe_key = name.replace("'", "\\'")
            items_html += (
                f"<li style='padding:2px 0; {indent}'>"
                f"<span class='nav-link' onclick=\"navigate('{url}')\" "
                f"style='color:{HYPERMINT}; font-weight:600; font-size:13px; "
                f"cursor:pointer;'>{name}</span></li>"
            )
        else:
            color = "#555" if is_sub else "#888"
            items_html += (
                f"<li style='color:{color}; font-size:13px; padding:2px 0; {indent}'>{name}</li>"
            )

    card_height = 72 + len(section["pages"]) * 26

    card_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{ background:transparent; font-family: Helvetica, Arial, sans-serif; }}
      .card {{
        background:{SURFACE_1};
        border:1px solid {BORDER};
        border-top:3px solid {accent};
        border-radius:12px;
        padding:18px 20px 18px 20px;
      }}
      .card-title {{
        display:flex; align-items:center; gap:10px; margin-bottom:12px;
      }}
      .card-title .icon {{ font-size:20px; }}
      .card-title .label {{
        font-size:15px; font-weight:700; color:{accent};
        font-family: Helvetica, Arial, sans-serif;
      }}
      ul {{ padding-left:16px; list-style:disc; }}
      .nav-link:hover {{ color:#ffffff !important; text-decoration:underline; }}
    </style>
    </head>
    <body>
    <div class="card">
      <div class="card-title">
        <span class="icon">{section["icon"]}</span>
        <span class="label">{section["title"]}</span>
      </div>
      <ul>{items_html}</ul>
    </div>
    <script>
      function navigate(url) {{
        window.parent.location.href = url;
      }}
    </script>
    </body>
    </html>
    """

    with col:
        components.html(card_html, height=card_height, scrolling=False)

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
