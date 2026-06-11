import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Build It Scorecard | Telco Retail",
    page_icon="🔨",
    layout="wide",
)

render_scorecard({
    "name": "Build It",
    "where_merge": "LOWER(TENANT) LIKE '%build it%'",
    "where_usage": "LOWER(TENANT_NAME) LIKE '%build it%'",
})
