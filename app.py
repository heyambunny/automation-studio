# app.py
import streamlit as st
from config import APP_NAME
from services.scheduler_service import scheduler_service

st.set_page_config(page_title=APP_NAME, page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# ── Hide sidebar when not authenticated ──
if not st.session_state.get("authenticated", False):
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stSidebarCollapsedControl"] { display: none; }
        .stApp { margin-left: 0 !important; }
        [data-testid="collapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)
    
    from pages._login import login_page
    login_page()
    st.stop()

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

# ── Sidebar User Info ──
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_name}**")
    st.markdown(f"*{st.session_state.user_role}*")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    st.divider()

# ── Pages ──
home_page = st.Page("Home.py", title="◧ Dashboard", default=True)
settings_page = st.Page("pages/1_Settings.py", title="⚙ Settings")
mapping_page = st.Page("pages/2_Mapping_Manager.py", title="⊞ Mapping Manager")
campaign_mgr_page = st.Page("pages/3_Campaign_Manager.py", title="⊟ Campaign Manager")
new_campaign_page = st.Page("pages/4_New_Campaign.py", title="＋ New Campaign")
# drafts_page = st.Page("pages/6_Drafts.py", title="✉ Drafts")
history_page = st.Page("pages/7_Execution_History.py", title="↻ Execution History")
templates_page = st.Page("pages/8_Templates.py", title="□ Templates")
schedules_page = st.Page("pages/9_Schedules.py", title="◷ Schedules")
data_page = st.Page("pages/_Data_Browser.py", title="⊛ Data Browser")

pages = [home_page, settings_page, mapping_page, campaign_mgr_page,
         new_campaign_page, history_page,
         templates_page, schedules_page]

if st.session_state.user_role == "admin":
    pages.append(data_page)

pg = st.navigation(pages)
pg.run()