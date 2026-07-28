"""
Spot CI — Brand Guidelines 2025
Centralised colour/font tokens for all dashboard pages.
"""

# ── Palette ──────────────────────────────────────────────────────────────────
INKCORE        = "#0e0e0e"   # primary dark / backgrounds
ZERO_WHITE     = "#ffffff"   # light text / white fills
HYPERMINT      = "#13f460"   # primary accent (green)
SONIC_BLUE     = "#2d40e9"   # secondary accent (blue)
ULTRAVIOLET    = "#52BEC0"   # tertiary accent (teal/cyan)
HIGHVOLT_ORANGE= "#f44610"   # highlight / alert (orange)

# Chart colour sequence (rotate through these for multi-series charts).
# HighVolt Orange leads — matches the primary-accent usage on the other live
# Spot dashboards (KPI numbers, sparklines) for cross-board uniformity.
CHART_PALETTE = [HIGHVOLT_ORANGE, HYPERMINT, SONIC_BLUE, ULTRAVIOLET, "#a0a0a0"]

# ── Card / surface shades ─────────────────────────────────────────────────────
SURFACE_1 = "#1a1a1a"   # card background
SURFACE_2 = "#242424"   # slightly lifted surface
BORDER    = "#2e2e2e"   # subtle border

# ── Typography ────────────────────────────────────────────────────────────────
# At Hauss Std Retina is a licensed font; fall back to system sans for web use.
FONT_HEADER = "'At Hauss Std Retina', 'Helvetica Now', Helvetica, Arial, sans-serif"
FONT_BODY   = "'Helvetica Now', Helvetica, Arial, sans-serif"

# ── Shared CSS injected on every page ─────────────────────────────────────────
PAGE_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {{
      font-family: {FONT_BODY};
      background-color: {INKCORE};
      color: {ZERO_WHITE};
  }}

  /* ── Top bar ── */
  header[data-testid="stHeader"] {{
      background-color: {INKCORE};
      border-bottom: 1px solid {BORDER};
  }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
      background-color: {SURFACE_1};
      border-right: 1px solid {BORDER};
  }}
  section[data-testid="stSidebar"] * {{
      color: {ZERO_WHITE} !important;
  }}

  /* ── Metric cards ── */
  div[data-testid="metric-container"] {{
      background-color: {SURFACE_1};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 16px 20px;
  }}
  div[data-testid="metric-container"] label {{
      color: #888 !important;
      font-size: 12px !important;
      text-transform: uppercase;
      letter-spacing: 0.08em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {ZERO_WHITE} !important;
      font-weight: 700;
  }}

  /* ── DataFrames / tables ── */
  .dataframe thead th {{
      background-color: {SURFACE_2} !important;
      color: {HIGHVOLT_ORANGE} !important;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
  }}
  .dataframe tbody tr:hover td {{
      background-color: {SURFACE_2} !important;
  }}

  /* ── Section headings ── */
  h1, h2, h3 {{
      font-family: {FONT_HEADER};
      letter-spacing: -0.02em;
  }}
  h1 {{ color: {ZERO_WHITE}; }}
  h2 {{ color: {ZERO_WHITE}; }}
  h3 {{ color: {HIGHVOLT_ORANGE}; }}

  /* ── Accent rule ── */
  .spot-rule {{
      height: 3px;
      background: linear-gradient(90deg, {HIGHVOLT_ORANGE}, {HYPERMINT}, {SONIC_BLUE});
      border: none;
      border-radius: 2px;
      margin: 8px 0 24px 0;
  }}

  /* ── Page badge ── */
  .spot-badge {{
      display: inline-block;
      background: {SURFACE_2};
      border: 1px solid {BORDER};
      border-radius: 6px;
      padding: 3px 10px;
      font-size: 11px;
      color: #888;
      margin-bottom: 16px;
  }}

  /* ── Filter pill ── */
  div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
      background-color: {HIGHVOLT_ORANGE} !important;
      color: {ZERO_WHITE} !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
      background-color: {HIGHVOLT_ORANGE};
      color: {ZERO_WHITE};
      border: none;
      border-radius: 8px;
      font-weight: 600;
  }}
  .stButton > button:hover {{
      background-color: {SONIC_BLUE};
      color: {ZERO_WHITE};
  }}

  /* ── Plotly chart background ── */
  .js-plotly-plot .plotly .bg {{
      fill: {SURFACE_1} !important;
  }}

  /* ── Hide auto-generated sidebar page list ── */
  [data-testid="stSidebarNav"],
  [data-testid="stSidebarNav"] + div:empty,
  section[data-testid="stSidebar"] nav,
  section[data-testid="stSidebar"] ul {{
      display: none !important;
  }}

  /* ── Page link — menu cards (plain text style) ── */
  [data-testid="stPageLink"] {{
      margin: 0 !important;
      padding: 0 !important;
  }}
  [data-testid="stPageLink"] a,
  [data-testid="stPageLink-NavLink"] {{
      color: {HIGHVOLT_ORANGE} !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      text-decoration: none !important;
      background: none !important;
      border: none !important;
      padding: 2px 0 !important;
      margin: 0 !important;
      display: inline !important;
      border-radius: 0 !important;
  }}
  [data-testid="stPageLink"] a:hover,
  [data-testid="stPageLink-NavLink"]:hover {{
      color: {ZERO_WHITE} !important;
      text-decoration: underline !important;
      background: none !important;
  }}
</style>
"""

def inject_css():
    """Call st.markdown(PAGE_CSS, unsafe_allow_html=True) at top of every page."""
    import streamlit as st
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", badge: str = ""):
    """Render a consistent Spot-branded page header."""
    import streamlit as st
    if badge:
        st.markdown(f'<div class="spot-badge">{badge}</div>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.markdown('<div class="spot-rule"></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color:#888;margin-top:-16px;font-size:14px;'>{subtitle}</p>",
                    unsafe_allow_html=True)
