"""
Subscriptions - WhatsApp — Subscriptions section, page 3 of 6
Data: UCONNECT_DW.ANALYTICS.VW_SPOT_BILLING_DATA

⚠ Unresolved: this channel and "Below the line" (page 46) both trace back to
the same CAMPAIGNNAME='DIGITAL UCONNECT UPSELL' in VW_SPOT_BILLING_DATA, which
has only one DEALDESCRIPTION network-wide ('OA uConnect R100 Free Airtime
Monthly @ R35') and no further SOURCETYPE/SOURCENAME split confirmed live.
The real report's WhatsApp/BTL split must use a filter this connection can't
see. Both pages currently show the SAME full campaign total - re-check against
live report numbers once Snowflake access is restored, and narrow this filter
if a distinguishing field turns up.
"""
import streamlit as st

from utils.ci import inject_css, page_header, HIGHVOLT_ORANGE
from utils.page_helpers import render_subscription_billing_page

st.set_page_config(page_title="Subscriptions - WhatsApp | Telco Retail", page_icon="🔄", layout="wide")
inject_css()
st.page_link("app.py", label="← Back to Menu")
st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
page_header("Subscriptions - WhatsApp", badge="Subscriptions · 3 of 6")

st.markdown(
    f"<p style='color:{HIGHVOLT_ORANGE}; font-size:11px; margin-bottom:12px;'>"
    "⚠ Unresolved split vs. \"Below the line\" - both currently show the same "
    "underlying campaign total. Re-check against live report numbers once "
    "Snowflake access is restored.</p>",
    unsafe_allow_html=True,
)

CAMPAIGNS = ["DIGITAL UCONNECT UPSELL"]

render_subscription_billing_page(CAMPAIGNS)
