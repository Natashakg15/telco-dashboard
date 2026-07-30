"""
Subscriptions - App — Subscriptions section, page 2 of 6
Data: UCONNECT_DW.ANALYTICS.VW_UCONNECT_APP_SUBSCRIPTIONS
Table choice confirmed live against Snowflake: its DESCRIPTION values
('10GB', 'UNLIMITED TALK + 10GB', etc.) match the real PBI page's deal
legend exactly - a different table from the CAMPAIGNNAME-based billing pages.
"""
import streamlit as st

from utils.ci import inject_css, page_header
from utils.page_helpers import render_app_subscription_page

st.set_page_config(page_title="Subscriptions - App | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions - App", badge="Subscriptions · 2 of 6")

render_app_subscription_page()
