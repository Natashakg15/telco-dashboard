"""
Subscriptions - Telesales — Subscriptions section, page 1 of 6
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA
CAMPAIGNNAME set confirmed live against Snowflake (spot-sql MCP): these are
the "generic subscription upsell" campaigns sold via the telesales/distribution
channel, as opposed to the app-bundle, WhatsApp, or mobile-store-specific ones.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_subscription_billing_page

st.set_page_config(page_title="Subscriptions - Telesales | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions - Telesales", badge="Subscriptions · 1 of 6")

CAMPAIGNS = [
    "UCONNECT UPSELL", "UCONNECT UPSELL 2", "UCONNECT TRIPLESAVE",
    "UCONNECT BREAKFREE", "UCONNECT BREAKFREE 2", "UCONNECT BREAKFREE INSTORE",
    "HALAALA BREAKFREE 1", "HALAALA BREAKFREE  1",
    "UCONNECT - UNREASONABLE HOSPITALITY", "UCONNECT", "UCONNECT VAS INSTORE",
]

render_subscription_billing_page(CAMPAIGNS)
