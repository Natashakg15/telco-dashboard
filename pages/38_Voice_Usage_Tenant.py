import streamlit as st
st.set_page_config(page_title="Voice Usage by Tenant | Telco Retail", page_icon="📞", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Voice Usage by Tenant", "Strategy",
    kpis=[
        {"label": "Total Voice Minutes MTD", "source": "CDR / usage table"},
        {"label": "Active Voice Users", "source": "CDR / usage table"},
        {"label": "Avg Minutes per User", "source": "CDR / usage table"},
        {"label": "Voice Revenue MTD", "source": "CDR / revenue table"},
    ],
    chart_rows=[
        [
            {"title": "Voice Minutes by Tenant — Monthly", "source": "CDR / usage table"},
            {"title": "Active Voice Users by Tenant", "source": "CDR / usage table"},
        ],
        [
            {"title": "Voice Usage Trend (13 months)", "source": "CDR / usage table"},
            {"title": "Minutes per User by Tenant", "source": "CDR / usage table"},
        ],
    ],
    note="Voice usage requires CDR (Call Detail Records) data. Not currently available via the MCP connection.",
)
