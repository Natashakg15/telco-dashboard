"""
Subscriptions - Mobile Store DigiM VAS — Subscriptions section, page 6 of 6
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA
CAMPAIGNNAME set confirmed live against Snowflake.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_subscription_billing_page

st.set_page_config(page_title="Subscriptions - Mobile Store DigiM VAS | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions - Mobile Store DigiM VAS", badge="Subscriptions · 6 of 6")

CAMPAIGNS = ["DIGIM VAS", "DIGIM RESELLS", "DIGIM RESELLS HD"]

render_subscription_billing_page(CAMPAIGNS)
