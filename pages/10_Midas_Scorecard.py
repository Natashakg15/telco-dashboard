import streamlit as st
from utils.scorecard import render_scorecard

st.set_page_config(
    page_title="Midas Scorecard | Telco Retail",
    page_icon="⚙️",
    layout="wide",
)

render_scorecard({
    "name": "Midas",
    "where_merge": """
        (LOWER(TENANT) LIKE '%midas%'
         OR LOWER(TENANT) LIKE '%kr motor%'
         OR LOWER(TENANT) LIKE '%aca auto%')
    """,
    "where_usage": """
        (LOWER(TENANT_NAME) LIKE '%midas%'
         OR LOWER(TENANT_NAME) LIKE '%kr motor%'
         OR LOWER(TENANT_NAME) LIKE '%aca auto%')
    """,
})
