"""
Subscriptions - Mobile Store — Subscriptions section, page 5 of 6
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA
CAMPAIGNNAME confirmed live against Snowflake.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_subscription_billing_page

st.set_page_config(page_title="Subscriptions - Mobile Store | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions - Mobile Store", badge="Subscriptions · 5 of 6")

CAMPAIGNS = ["MOBILE STORE 2"]

render_subscription_billing_page(CAMPAIGNS)
