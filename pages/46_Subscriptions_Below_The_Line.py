"""
Subscriptions - Below the Line — Subscriptions section, page 4 of 6
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA

⚠ Unresolved: see pages/45_Subscriptions_WhatsApp.py - this page currently
shares the same underlying filter as WhatsApp (CAMPAIGNNAME='DIGITAL UCONNECT
UPSELL'), since no distinguishing field was found live. Re-check once
Snowflake access is restored.
"""
import streamlit as st

from utils.ci import inject_css, page_header, HIGHVOLT_ORANGE
from utils.page_helpers import render_subscription_billing_page

st.set_page_config(page_title="Subscriptions - Below the Line | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions - Below the Line", badge="Subscriptions · 4 of 6")

st.markdown(
    f"<p style='color:{HIGHVOLT_ORANGE}; font-size:11px; margin-bottom:12px;'>"
    "⚠ Unresolved split vs. \"WhatsApp\" - both currently show the same "
    "underlying campaign total. Re-check against live report numbers once "
    "Snowflake access is restored.</p>",
    unsafe_allow_html=True,
)

CAMPAIGNS = ["DIGITAL UCONNECT UPSELL"]

render_subscription_billing_page(CAMPAIGNS)
