import streamlit as st
st.set_page_config(page_title="Spot Connect Book | Telco Retail", page_icon="📖", layout="wide")
from utils.page_helpers import placeholder_page
placeholder_page(
    "Spot Connect Book", "Strategy",
    kpis=[
        {"label": "Total SIMs Sold (Cumulative)", "source": "UCONNECT_MAY_MERGE"},
        {"label": "Active SIMs", "source": "VW_SPOT_ACTIVE_CUSTOMERS"},
        {"label": "Active Subscribers", "source": "VW_SPOT_SUBSCRIPTIONS"},
        {"label": "Total Revenue (LTM)", "source": "UCONNECT_MAY_MERGE_REVENUE"},
    ],
    chart_rows=[
        [
            {"title": "Business Overview Snapshot", "source": "Multiple Snowflake sources"},
            {"title": "Key Performance Indicators — YTD", "source": "Multiple Snowflake sources"},
        ],
        [
            {"title": "Geographic / Tenant Footprint", "source": "UCONNECT_RETAIL_GROUPS"},
            {"title": "Product Mix", "source": "UCONNECT_MAY_MERGE (PRODUCT column)"},
        ],
    ],
    note="The Spot Connect Book is a curated strategy summary page. Content will be designed in collaboration with the Business Custodian.",
)
