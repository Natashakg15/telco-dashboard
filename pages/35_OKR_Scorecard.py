import streamlit as st
st.set_page_config(page_title="OKR Scorecard | Telco Retail", page_icon="🎯", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "OKR Scorecard", "Strategy",
    kpis=[
        {"label": "OKRs On Track", "source": "OKR tracking table"},
        {"label": "OKRs At Risk", "source": "OKR tracking table"},
        {"label": "OKRs Off Track", "source": "OKR tracking table"},
        {"label": "Completion %", "source": "OKR tracking table"},
    ],
    chart_rows=[
        [
            {"title": "OKR RAG Status — Current Quarter", "source": "OKR tracking table"},
            {"title": "Key Results Progress by Objective", "source": "OKR tracking table"},
        ],
    ],
    note="OKR tracking requires a dedicated source table with targets, owners, and RAG statuses. Not currently available via MCP.",
)
