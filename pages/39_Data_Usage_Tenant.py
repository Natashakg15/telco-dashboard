import streamlit as st
st.set_page_config(page_title="Data Usage by Tenant | Telco Retail", page_icon="📡", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Data Usage by Tenant", "Strategy",
    kpis=[
        {"label": "Total Data (GB) MTD", "source": "CDR / data usage table"},
        {"label": "Active Data Users", "source": "CDR / data usage table"},
        {"label": "Avg GB per User", "source": "CDR / data usage table"},
        {"label": "Data Revenue MTD", "source": "CDR / revenue table"},
    ],
    chart_rows=[
        [
            {"title": "Data (GB) by Tenant — Monthly", "source": "CDR / data usage table"},
            {"title": "Active Data Users by Tenant", "source": "CDR / data usage table"},
        ],
        [
            {"title": "Data Usage Trend (13 months)", "source": "CDR / data usage table"},
            {"title": "GB per User by Tenant", "source": "CDR / data usage table"},
        ],
    ],
    note="Data usage (GB) requires CDR data. Not currently available via the MCP connection.",
)
