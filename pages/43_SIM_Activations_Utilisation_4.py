"""
New SIM Activations and Utilisation — Sales section, page 4 of 4
Data: UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_activation_utilisation_grid

st.set_page_config(page_title="New SIM Activations & Utilisation 4 | Telco Retail", page_icon="📡", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("New SIM Activations and Utilisation", badge="Sales · 4 of 4")

GROUPS = [
    {"label": "Aheers", "where": "TENANT_NAME LIKE 'Aheers%'"},
    {"label": "Mica",   "where": "TENANT_NAME LIKE 'Mica%'"},
]

render_activation_utilisation_grid(GROUPS)
