"""
New SIM Activations and Utilisation — Sales section, page 3 of 4
Data: UCONNECT_DW.ANALYTICS.VW_ACTIVE_SUBSCRIPTIONS_USAGE_DETAILS

"Other tenants (incl. First Group, Amazing Vouchers and All Life)" is the
one catch-all bucket on this page that's a best-effort guess: only the 3
named entities are included below, not a true "everything left over" catch-
all (that would require every other page's exclusion list applied here too).
Re-check against live report numbers once Snowflake access is restored.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_activation_utilisation_grid

st.set_page_config(page_title="New SIM Activations & Utilisation 3 | Telco Retail", page_icon="📡", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("New SIM Activations and Utilisation", badge="Sales · 3 of 4")

st.markdown(
    "<p style='color:#888; font-size:11px; margin-bottom:12px;'>"
    "⚠ \"Other tenants\" bucket below is a best-effort guess (named entities only, "
    "not a true catch-all) — re-check against live numbers once Snowflake access is restored.</p>",
    unsafe_allow_html=True,
)

GROUPS = [
    {"label": "uConnect app",      "where": "TENANT_NAME LIKE 'uConnect App%'"},
    {"label": "All Life",          "where": "SOURCE = 'AllLife'"},
    {"label": "Mobile Store",      "where": "TENANT_NAME LIKE 'Mobile Store%'"},
    {"label": "Other tenants (incl. First Group, Amazing Vouchers and All Life)",
     "where": "TENANT_NAME IN ('First Group Investment Holdings (Pty) Ltd', 'Amazing Vouchers') OR SOURCE = 'AllLife'"},
]

render_activation_utilisation_grid(GROUPS)
