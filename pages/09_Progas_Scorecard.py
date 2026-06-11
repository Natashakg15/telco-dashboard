import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Progas Scorecard | Telco Retail",
    page_icon="🔥",
    layout="wide",
)

render_scorecard({
    "name": "Progas",
    "where_merge": "LOWER(TENANT) LIKE '%progas%'",
    "where_usage": "LOWER(TENANT_NAME) LIKE '%progas%'",
})
