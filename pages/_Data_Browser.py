# pages/_Data_Browser.py
import streamlit as st
import pandas as pd
from database import engine, init_db
from sqlalchemy import inspect

st.set_page_config(page_title="Data Browser", layout="wide")
st.title("🗄️ Data Browser")

st.markdown("""
<div style="background:#ECEFF1;padding:10px 14px;border-radius:8px;border-left:4px solid #607D8B;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#37474F;"><strong>🗄️ Database Viewer</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
View all database tables and records. Includes <b>audit_logs</b> to track all actions performed in the system.<br>
Select a table from the dropdown to browse its data.
</p>
</div>
""", unsafe_allow_html=True)

init_db()

# Get all tables
inspector = inspect(engine)
tables = inspector.get_table_names()

selected_table = st.selectbox("Select Table", tables)

if selected_table:
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
    
    st.subheader(f"📋 {selected_table} ({len(df)} rows)")
    st.dataframe(df, use_container_width=True)