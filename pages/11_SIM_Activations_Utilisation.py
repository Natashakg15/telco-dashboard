"""
New SIM Activations and Utilisation — Sales section, page 1 of 4
Data: UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS
Split by tenant group, matching the real Power BI report's 4 pages (each a
2x2 grid of daily-activations-bar + Active-1%-line combo charts). Page split
confirmed from user-supplied screenshots of the live PBIX.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_activation_utilisation_grid

st.set_page_config(page_title="New SIM Activations & Utilisation 1 | Telco Retail", page_icon="📡", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("New SIM Activations and Utilisation", badge="Sales · 1 of 4")

GROUPS = [
    {"label": "Spar",              "where": "TENANT_NAME LIKE 'Spar%'"},
    {"label": "Build It",          "where": "TENANT_NAME LIKE 'Build It%'"},
    {"label": "Pet Pool & Home",   "where": "TENANT_NAME LIKE 'Pet Pool & Home%'"},
    {"label": "Fashion Fusion",    "where": "TENANT_NAME LIKE 'Fashion Fusion%'"},
]

render_activation_utilisation_grid(GROUPS)
