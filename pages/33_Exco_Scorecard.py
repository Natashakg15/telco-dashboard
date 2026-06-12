import streamlit as st
st.set_page_config(page_title="Exco Scorecard | Telco Retail", page_icon="🎯", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Exco Scorecard", "Strategy",
    kpis=[
        {"label": "Total Active SIMs", "source": "VW_SPOT_ACTIVE_CUSTOMERS"},
        {"label": "MoM Growth %", "source": "VW_SPOT_ACTIVE_CUSTOMERS_MONTHLY_SNAPSHOT"},
        {"label": "Revenue MTD", "source": "UCONNECT_MAY_MERGE_REVENUE"},
        {"label": "Gross Margin %", "source": "GL / Income Statement table"},
    ],
    chart_rows=[
        [
            {"title": "Key Metrics Summary — Monthly", "source": "Multiple sources"},
            {"title": "Exco OKR RAG Status", "source": "OKR tracking table"},
        ],
        [
            {"title": "Revenue vs Target", "source": "GL + Budget table"},
            {"title": "Active SIM Growth vs Target", "source": "Budget table + UCONNECT_MAY_MERGE"},
        ],
    ],
    note="Exco Scorecard requires OKR targets and budget data not yet connected. KPIs from available sources will populate once targets are defined.",
)
