import streamlit as st
st.set_page_config(page_title="Value of New Business | Telco Retail", page_icon="💎", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Value of New Business", "Financials",
    kpis=[
        {"label": "New Business Revenue MTD", "source": "GL / new business cohort table"},
        {"label": "Lifetime Value (LTV) Estimate", "source": "GL / cohort revenue table"},
        {"label": "LTV / CPA Ratio", "source": "GL / costing + cohort table"},
        {"label": "Months to Payback", "source": "GL / cohort revenue table"},
    ],
    chart_rows=[
        [
            {"title": "New Business Value by Cohort", "source": "GL / cohort revenue table"},
            {"title": "LTV Curve by Acquired Month", "source": "GL / cohort revenue table"},
        ],
        [
            {"title": "LTV / CPA Trend", "source": "GL / costing + cohort table"},
            {"title": "Payback Period by Channel", "source": "GL / costing + cohort table"},
        ],
    ],
    note="Value of New Business metrics require cohort revenue and costing data. Not currently available via MCP.",
)
