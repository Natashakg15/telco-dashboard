"""
Spot CI — Brand Guidelines 2025
Centralised colour/font tokens for all dashboard pages.

Light-theme repaint (matching the other live Spot dashboards: light gray
page canvas, white content cards, dark-navy KPI stat tiles, HighVolt Orange
as primary accent) is implemented by REPURPOSING these token values rather
than renaming them — every page file imports these by name (SURFACE_1,
ZERO_WHITE, BORDER, etc.), so changing what they point to here cascades the
new look everywhere without touching 40 page files individually. This means
some names no longer literally describe their value (e.g. ZERO_WHITE now
holds a near-black hex, because it plays the role "text colour on top of
SURFACE_1" and SURFACE_1 is now white, not "the literal colour white"). If
you're hunting for a "dark navy" or "off-white" constant and it's not here,
this is why — check the role/comment, not just the name.
"""

# ── Palette ──────────────────────────────────────────────────────────────────
INKCORE        = "#0e0e0e"   # dark navy/near-black — now used specifically for
                             # KPI stat tiles (metric containers), not the page bg
ZERO_WHITE     = "#12141a"   # repurposed: primary text colour on light surfaces
                             # (was literal white for dark-theme text)
HYPERMINT      = "#13f460"   # accent (green)
SONIC_BLUE     = "#2d40e9"   # accent (blue)
ULTRAVIOLET    = "#52BEC0"   # accent (teal/cyan)
HIGHVOLT_ORANGE= "#f44610"   # primary accent (orange) — leads the palette

# Text/icon colour specifically for content sitting on a dark background
# (stat tiles, buttons, filter pills) — decoupled from ZERO_WHITE now that
# ZERO_WHITE means "dark text on light surface".
ON_DARK_TEXT   = "#ffffff"

# Chart colour sequence (rotate through these for multi-series charts).
CHART_PALETTE = [HIGHVOLT_ORANGE, HYPERMINT, SONIC_BLUE, ULTRAVIOLET, "#a0a0a0"]

# ── Card / surface shades ─────────────────────────────────────────────────────
PAGE_BG   = "#f0f1f4"   # page canvas (was INKCORE, dark)
SURFACE_1 = "#ffffff"   # card / chart background (was dark #1a1a1a)
SURFACE_2 = "#f5f6f8"   # slightly recessed surface, e.g. table headers (was #242424)
BORDER    = "#e3e5ea"   # subtle light border (was dark #2e2e2e)

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
      background-color: {PAGE_BG};
      color: {ZERO_WHITE};
  }}

  /* ── Top bar ── */
  header[data-testid="stHeader"] {{
      background-color: {PAGE_BG};
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

  /* ── Metric cards — dark stat tiles, matching the reference dashboards ──
     NOTE: Streamlit 1.60's DOM uses data-testid="stMetric" (label/value are
     nested markdown containers, not plain text) - both old and new testids
     are targeted since this has drifted across Streamlit versions before.
     High-specificity + !important throughout: Streamlit's own emotion-cache
     rules otherwise win the cascade even against !important single-attribute
     selectors. ── */
  div.stMetric[data-testid="metric-container"],
  div.stMetric[data-testid="stMetric"] {{
      background-color: {INKCORE} !important;
      border: 1px solid {INKCORE} !important;
      border-radius: 12px !important;
      padding: 16px 20px !important;
  }}
  div.stMetric [data-testid="stMetricLabel"] p,
  div.stMetric [data-testid="stMetricLabel"] {{
      color: #9aa0aa !important;
      font-size: 12px !important;
      text-transform: uppercase;
      letter-spacing: 0.08em;
  }}
  div.stMetric [data-testid="stMetricValue"] p,
  div.stMetric [data-testid="stMetricValue"] {{
      color: {ON_DARK_TEXT} !important;
      font-weight: 700 !important;
  }}
  div.stMetric [data-testid="stMetricDelta"] p {{
      font-weight: 600 !important;
  }}

  /* ── DataFrames / tables ── */
  .dataframe thead th {{
      background-color: {SURFACE_2} !important;
      color: {HIGHVOLT_ORANGE} !important;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
  }}
  .dataframe tbody td {{
      color: {ZERO_WHITE} !important;
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
      color: #6b7280;
      margin-bottom: 16px;
  }}

  /* ── Filter pill ── */
  div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
      background-color: {HIGHVOLT_ORANGE} !important;
      color: {ON_DARK_TEXT} !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
      background-color: {HIGHVOLT_ORANGE};
      color: {ON_DARK_TEXT};
      border: none;
      border-radius: 8px;
      font-weight: 600;
  }}
  .stButton > button:hover {{
      background-color: {SONIC_BLUE};
      color: {ON_DARK_TEXT};
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
      color: {INKCORE} !important;
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
        st.markdown(f"<p style='color:#6b7280;margin-top:-16px;font-size:14px;'>{subtitle}</p>",
                    unsafe_allow_html=True)
