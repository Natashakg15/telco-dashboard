import streamlit as st
st.set_page_config(page_title="Cost of Sale Metrics | Telco Retail", page_icon="💸", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Cost of Sale Metrics", "Financials",
    kpis=[
        {"label": "Total CoS MTD", "source": "GL / CoS table"},
        {"label": "CoS as % of Revenue", "source": "GL / CoS table"},
        {"label": "SIM Cost per Activation", "source": "GL / CoS table"},
        {"label": "Airtime CoS", "source": "GL / CoS table"},
    ],
    chart_rows=[
        [
            {"title": "CoS Components — Monthly", "source": "GL / CoS table"},
            {"title": "CoS % of Revenue Trend", "source": "GL / CoS table"},
        ],
        [
            {"title": "SIM Cost per Activation Trend", "source": "GL / CoS table"},
            {"title": "Airtime CoS Breakdown", "source": "GL / CoS table"},
        ],
    ],
    note="Cost of Sale data requires the GL / costing source. Not currently available via MCP.",
)
