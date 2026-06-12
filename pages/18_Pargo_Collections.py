import streamlit as st
st.set_page_config(page_title="Pargo Collections | Telco Retail", page_icon="📦", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Pargo Collections", "Commercial",
    kpis=[
        {"label": "Parcels Sent MTD", "source": "Pargo integration / logistics table"},
        {"label": "Parcels Collected MTD", "source": "Pargo integration / logistics table"},
        {"label": "Collection Rate %", "source": "Pargo integration / logistics table"},
        {"label": "Avg Days to Collect", "source": "Pargo integration / logistics table"},
    ],
    chart_rows=[
        [
            {"title": "Monthly Collections Trend", "source": "Pargo API / logistics table"},
            {"title": "Sent vs Collected — by Month", "source": "Pargo API / logistics table"},
        ],
        [
            {"title": "Collections by Tenant", "source": "Pargo API / logistics table"},
            {"title": "Aged Uncollected Parcels", "source": "Pargo API / logistics table"},
        ],
    ],
    note="Pargo logistics data is not available via the current MCP connection. Charts will populate once integrated.",
)
