import streamlit as st
st.set_page_config(page_title="Pipeline & Provisional Commissions | Telco Retail", page_icon="💼", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Pipeline & Provisional Commissions", "Sales",
    kpis=[
        {"label": "Pipeline Value", "source": "Commission pipeline table"},
        {"label": "Provisional Commission MTD", "source": "Commission pipeline table"},
        {"label": "Confirmed Commission MTD", "source": "Commission pipeline table"},
        {"label": "Payout Due", "source": "Commission pipeline table"},
    ],
    chart_rows=[
        [
            {"title": "Pipeline by Tenant — Monthly", "source": "Commission pipeline table"},
            {"title": "Provisional vs Confirmed Commission", "source": "Commission pipeline table"},
        ],
        [
            {"title": "Commission Trend (13 months)", "source": "Commission pipeline table"},
            {"title": "Top Tenants by Commission", "source": "Commission pipeline table"},
        ],
    ],
    note="Commission and pipeline data is not yet accessible via MCP. Charts will populate once the source table is connected.",
)
