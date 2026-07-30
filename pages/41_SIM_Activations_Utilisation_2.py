"""
New SIM Activations and Utilisation — Sales section, page 2 of 4
Data: UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS

"OnAir" / "OnAir Non Sales" split and "NRP" are inferred, not confirmed
against a report-level filter definition (the Power BI modeling connection
only exposes the semantic model, not report-page filters):
  - "NRP" matches SOURCE = 'NRP' - a real, confirmed value on this table.
  - "OnAir" vs "OnAir Non Sales": TENANT_NAME has both a bare 'OnAir' row and
    variants like 'OnAir Connect 50'. Split here as bare 'OnAir' vs everything
    else starting with 'OnAir' - a reasonable guess, not verified. Re-check
    against live report numbers once Snowflake access is restored.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_activation_utilisation_grid

st.set_page_config(page_title="New SIM Activations & Utilisation 2 | Telco Retail", page_icon="📡", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("New SIM Activations and Utilisation", badge="Sales · 2 of 4")

st.markdown(
    "<p style='color:#888; font-size:11px; margin-bottom:12px;'>"
    "⚠ \"OnAir\" / \"OnAir Non Sales\" split is inferred, not confirmed against a report filter — "
    "re-check against live numbers once Snowflake access is restored.</p>",
    unsafe_allow_html=True,
)

GROUPS = [
    {"label": "The Unlimited",     "where": "TENANT_NAME LIKE 'The Unlimited%'"},
    {"label": "OnAir",             "where": "TENANT_NAME = 'OnAir'"},
    {"label": "NRP",               "where": "SOURCE = 'NRP'"},
    {"label": "OnAir Non Sales",   "where": "TENANT_NAME LIKE 'OnAir%' AND TENANT_NAME <> 'OnAir'"},
]

render_activation_utilisation_grid(GROUPS)
