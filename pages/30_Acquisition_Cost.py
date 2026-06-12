import streamlit as st
st.set_page_config(page_title="Acquisition Cost Metrics | Telco Retail", page_icon="🎯", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Acquisition Cost Metrics", "Financials",
    kpis=[
        {"label": "Cost per Acquisition (CPA)", "source": "GL / CoS + UCONNECT_MAY_MERGE"},
        {"label": "Marketing Cost per Activation", "source": "GL / marketing spend table"},
        {"label": "Reward Payouts MTD", "source": "UCONNECT_MAY_MERGE_REVENUE (REVENUE_PAID_FOR_REWARDS_VALUE)"},
        {"label": "Reward Cost per Activation", "source": "GL / CoS + activations"},
    ],
    chart_rows=[
        [
            {"title": "CPA Trend (13 months)", "source": "GL / CoS + activations"},
            {"title": "Acquisition Cost by Channel", "source": "GL / CoS table"},
        ],
        [
            {"title": "Reward Payout Trend", "source": "UCONNECT_MAY_MERGE_REVENUE REVENUE_PAID_FOR_REWARDS_VALUE"},
            {"title": "Acquisition Cost vs LTV", "source": "GL / costing + cohort revenue table"},
        ],
    ],
    note="Full CPA requires GL cost data. Reward payout amounts are available in UCONNECT_MAY_MERGE_REVENUE — will populate once GL is connected.",
)
