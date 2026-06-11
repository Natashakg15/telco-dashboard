import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Aheers Scorecard | Telco Retail",
    page_icon="🏬",
    layout="wide",
)

render_scorecard({
    "name": "Aheers",
    "where_merge": "LOWER(TENANT) LIKE '%aheers%'",
    "where_usage": "LOWER(TENANT_NAME) LIKE '%aheers%'",
})
