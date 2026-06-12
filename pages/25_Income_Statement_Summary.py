import streamlit as st
st.set_page_config(page_title="Income Statement Summary | Telco Retail", page_icon="💰", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Income Statement Summary", "Financials",
    kpis=[
        {"label": "YTD Revenue", "source": "GL / Income Statement table"},
        {"label": "YTD Gross Profit", "source": "GL / Income Statement table"},
        {"label": "YTD EBITDA", "source": "GL / Income Statement table"},
        {"label": "YTD Net Profit", "source": "GL / Income Statement table"},
    ],
    chart_rows=[
        [
            {"title": "YTD P&L Summary", "source": "GL / Income Statement table"},
            {"title": "Budget vs Actual", "source": "GL + Budget table"},
        ],
    ],
    note="Income Statement Summary requires GL / financial reporting data. Not currently available via MCP.",
)
