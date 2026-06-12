import streamlit as st
st.set_page_config(page_title="Opex Metrics | Telco Retail", page_icon="🏦", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Opex Metrics", "Financials",
    kpis=[
        {"label": "Total Opex MTD", "source": "GL / Opex table"},
        {"label": "Opex as % of Revenue", "source": "GL / Opex table"},
        {"label": "Staff Costs", "source": "GL / Opex table"},
        {"label": "Marketing Spend", "source": "GL / Opex table"},
    ],
    chart_rows=[
        [
            {"title": "Opex by Category — Monthly", "source": "GL / Opex table"},
            {"title": "Opex Trend (13 months)", "source": "GL / Opex table"},
        ],
        [
            {"title": "Opex % of Revenue", "source": "GL / Opex table"},
            {"title": "Budget vs Actual Opex", "source": "GL + Budget table"},
        ],
    ],
    note="Opex data requires the GL / expense source. Not currently available via MCP.",
)
