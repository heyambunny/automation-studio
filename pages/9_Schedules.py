import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Schedule
from services.scheduler_service import scheduler_service

st.title("⏰ Scheduled Campaigns")

st.markdown("""
<div style="background:#FFF8E1;padding:10px 14px;border-radius:8px;border-left:4px solid #FFC107;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#F57F17;"><strong>⏰ Scheduled Campaigns</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
View and manage all your scheduled campaigns here.<br>
Campaigns are created from <b>New Campaign → Step 5 → Schedule</b>.
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

# Load schedules
schedules = db.query(Schedule).order_by(Schedule.next_run).all()

if schedules:
    schedule_data = []
    for s in schedules:
        schedule_data.append({
            "ID": s.id,
            "Name": s.schedule_name,
            "Frequency": s.frequency,
            "Next Run": s.next_run.strftime("%Y-%m-%d %H:%M") if s.next_run else "N/A",
            "Status": "🟢 Active" if s.enabled else "🔴 Disabled",
            "Created": s.created_at.strftime("%Y-%m-%d") if s.created_at else ""
        })
    
    df = pd.DataFrame(schedule_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Cancel schedule
    st.subheader("🗑️ Cancel Schedule")
    selected_id = st.selectbox("Select schedule to cancel", [s.id for s in schedules], 
                                format_func=lambda x: f"#{x} - {next((s.schedule_name for s in schedules if s.id == x), '')}")
    
    if st.button("❌ Cancel Schedule", type="secondary"):
        scheduler_service.remove_schedule(selected_id)
        st.success(f"Schedule #{selected_id} cancelled.")
        st.rerun()
    
    # View job status
    st.divider()
    st.subheader("📊 Active Jobs in Scheduler")
    jobs = scheduler_service.get_jobs()
    if jobs:
        st.dataframe(pd.DataFrame(jobs), use_container_width=True, hide_index=True)
    else:
        st.info("No active jobs in the scheduler.")

else:
    st.info("No scheduled campaigns yet. Create a campaign and choose 'Schedule' in Step 6.")

db.close()