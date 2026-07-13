# app.py
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from config import APP_NAME
from services.scheduler_service import scheduler_service

st.set_page_config(page_title=APP_NAME, page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ── Sidebar CSS ──
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #FAFAFA; border-right: 1px solid #E5E5E5; }
    [data-testid="stSidebar"] a { color: #525252 !important; text-decoration: none; font-size: 13px; font-weight: 450; padding: 6px 12px; border-radius: 6px; transition: all 0.1s; }
    [data-testid="stSidebar"] a:hover { background: #F5F5F5; color: #0A0A0A !important; }
    [data-testid="stSidebar"] a[aria-current="page"] { background: #F5F5F5; color: #0A0A0A !important; font-weight: 500; }
    [data-testid="stSidebar"] hr { border-color: #E5E5E5; }
</style>
""", unsafe_allow_html=True)

home_page = st.Page("Home.py", title="◧ Dashboard", default=True)
settings_page = st.Page("pages/1_Settings.py", title="⚙ Settings")
mapping_page = st.Page("pages/2_Mapping_Manager.py", title="⊞ Mapping Manager")
campaign_mgr_page = st.Page("pages/3_Campaign_Manager.py", title="⊟ Campaign Manager")
new_campaign_page = st.Page("pages/4_New_Campaign.py", title="＋ New Campaign")
ai_assistant_page = st.Page("pages/5_AI_Assistant.py", title="⬡ AI Assistant")
drafts_page = st.Page("pages/6_Drafts.py", title="✉ Drafts")
history_page = st.Page("pages/7_Execution_History.py", title="↻ Execution History")
templates_page = st.Page("pages/8_Templates.py", title="□ Templates")
schedules_page = st.Page("pages/9_Schedules.py", title="◷ Schedules")
data_page = st.Page("pages/_Data_Browser.py", title="⊛ Data Browser")

pg = st.navigation([
    home_page, settings_page, mapping_page, campaign_mgr_page,
    new_campaign_page, ai_assistant_page, drafts_page, history_page,
    templates_page, schedules_page, data_page,
])
pg.run()