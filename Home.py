# Home.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from config import APP_NAME, APP_VERSION
from database import SessionLocal
from models import Execution, EmailLog, Schedule, Setting
from datetime import datetime, timedelta

st.set_page_config(page_title=APP_NAME, page_icon="⚡", layout="wide")

# ── Minimal CSS ──
st.markdown("""
<style>
    * { font-family: 'Inter', -apple-system, sans-serif; }
    
    .main-header { padding: 0 0 8px 0; border-bottom: 1px solid #E5E5E5; margin-bottom: 24px; }
    .main-header h1 { font-size: 24px; font-weight: 600; color: #0A0A0A; margin: 0; letter-spacing: -0.5px; }
    .main-header p { color: #737373; margin: 4px 0 0 0; font-size: 13px; }
    
    .stat-card { background: #FAFAFA; border: 1px solid #E5E5E5; border-radius: 8px; padding: 16px; text-align: center; }
    .stat-value { font-size: 24px; font-weight: 600; color: #0A0A0A; line-height: 1.2; }
    .stat-label { font-size: 11px; color: #737373; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
    
    .section-title { font-size: 14px; font-weight: 600; color: #0A0A0A; margin-bottom: 10px; letter-spacing: -0.2px; }
    
    .empty-state { text-align: center; padding: 24px; color: #A3A3A3; font-size: 13px; border: 1px dashed #E5E5E5; border-radius: 8px; }
    
    .stButton > button { 
        border-radius: 6px; font-weight: 500; font-size: 13px; 
        border: 1px solid #D4D4D4; background: white; color: #0A0A0A;
        padding: 8px 16px; transition: all 0.15s;
    }
    .stButton > button:hover { background: #FAFAFA; border-color: #A3A3A3; }
    .stButton > button[kind="primary"] { background: #0A0A0A; color: white; border: 1px solid #0A0A0A; }
    .stButton > button[kind="primary"]:hover { background: #262626; }
    
    hr { border-color: #E5E5E5; }
    
    .info-box { padding: 10px 14px; border-radius: 8px; border-left: 4px solid #2196F3; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

db = SessionLocal()
setting = db.query(Setting).first()

# ── Header ──
st.markdown(f"""
<div class="main-header">
    <h1>Automation Studio</h1>
    <p>Dashboard · {datetime.now().strftime('%d %B %Y')}</p>
</div>
""", unsafe_allow_html=True)

# ── Branding Row ──
col_brand, col_info = st.columns([1, 3])

with col_brand:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)
    else:
        st.markdown("""
        <div style="border:1px solid #E5E5E5;border-radius:12px;padding:20px;text-align:center;background:white;">
            <div style="font-size:40px;">⚡</div>
            <div style="font-size:13px;font-weight:600;color:#0A0A0A;margin-top:6px;">Automation Studio</div>
        </div>
        """, unsafe_allow_html=True)

with col_info:
    st.markdown("""
    <div style="border:1px solid #E5E5E5;border-radius:12px;padding:20px;background:white;">
        <p style="font-size:14px;color:#0A0A0A;margin:0 0 10px 0;line-height:1.6;">
            <strong>Automation Studio</strong> eliminates repetitive Excel-based reporting by automating 
            data extraction, AI-powered summaries, email composition, and scheduled delivery.
        </p>
        <div style="padding-top:10px;border-top:1px solid #F5F5F5;">
            <span style="font-size:11px;color:#A3A3A3;">Built by <strong>Himanshu Banyal</strong> · Internal Tool · v1.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Welcome ──
total_campaigns = db.query(Execution).count()
if total_campaigns == 0:
    st.markdown("""
    <div class="info-box" style="background:#E3F2FD;border-left-color:#2196F3;">
        <p style="margin:0;font-size:13px;color:#1565C0;"><strong>👋 Welcome!</strong></p>
        <p style="margin:3px 0 0 0;font-size:12px;color:#555;">
        Get started: ⚙️ <b>Settings</b> → 🗺️ <b>Mapping Manager</b> → 🚀 <b>New Campaign</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Stats Row ──
total_campaigns = db.query(Execution).count()
completed = db.query(Execution).filter(Execution.status == "completed").count()
in_progress = db.query(Execution).filter(Execution.status == "in_progress").count()
failed = db.query(Execution).filter(Execution.status == "failed").count()
sent_emails = db.query(EmailLog).filter(EmailLog.status == "sent").count()
total_emails = db.query(EmailLog).count()
success_rate = f"{(sent_emails / total_emails * 100):.0f}%" if total_emails > 0 else "—"

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{total_campaigns}</div><div class="stat-label">Campaigns</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{completed}</div><div class="stat-label">Completed</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{in_progress}</div><div class="stat-label">Running</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{failed}</div><div class="stat-label">Failed</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{sent_emails}</div><div class="stat-label">Sent</div></div>', unsafe_allow_html=True)
with c6:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{success_rate}</div><div class="stat-label">Success Rate</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ──
col1, col2 = st.columns(2)

with col1:
    st.markdown('<p class="section-title">Campaign Status</p>', unsafe_allow_html=True)
    status_data = pd.DataFrame({
        "Status": ["Completed", "Running", "Queued", "Failed", "Pending"],
        "Count": [completed, in_progress,
                  db.query(Execution).filter(Execution.status == "queued").count(),
                  failed,
                  db.query(Execution).filter(Execution.status == "pending").count()]
    })
    status_data = status_data[status_data["Count"] > 0]
    if not status_data.empty:
        fig = px.pie(status_data, values="Count", names="Status", hole=0.5,
                     color_discrete_sequence=["#D4D4D4", "#A3A3A3", "#737373", "#525252", "#E5E5E5"])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=260, paper_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(width=0)), textfont=dict(size=11, color='#525252'))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown('<div class="empty-state">No data yet</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<p class="section-title">Emails Sent — Last 7 Days</p>', unsafe_allow_html=True)
    last_7 = datetime.now() - timedelta(days=7)
    recent_logs = db.query(EmailLog).filter(EmailLog.sent_at >= last_7, EmailLog.status == "sent").all()
    
    if recent_logs:
        daily_counts = {}
        for i in range(7):
            daily_counts[(datetime.now() - timedelta(days=6-i)).strftime("%a")] = 0
        for log in recent_logs:
            day = log.sent_at.strftime("%a") if log.sent_at else ""
            if day in daily_counts:
                daily_counts[day] += 1
        
        chart_data = pd.DataFrame({"Day": list(daily_counts.keys()), "Emails": list(daily_counts.values())})
        fig = px.bar(chart_data, x="Day", y="Emails", color="Emails", color_continuous_scale=["#E5E5E5", "#0A0A0A"])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=260, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        fig.update_traces(marker=dict(line=dict(width=0), cornerradius=4))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#F5F5F5')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown('<div class="empty-state">No emails in last 7 days</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent & Upcoming ──
col1, col2 = st.columns(2)

with col1:
    st.markdown('<p class="section-title">Recent Executions</p>', unsafe_allow_html=True)
    recent = db.query(Execution).order_by(Execution.created_at.desc()).limit(10).all()
    
    if recent:
        rows = []
        for r in recent:
            emoji = {"completed": "✅", "in_progress": "🔄", "queued": "⏳", "failed": "❌", "pending": "📝"}
            rows.append({
                "Status": emoji.get(r.status.value, "📝"),
                "Campaign": r.campaign_name or "Unnamed",
                "Date": r.created_at.strftime('%d %b, %H:%M') if r.created_at else "",
                "Sent": f"{r.sent_count}/{r.total_emails}",
                "Mode": r.mode or ""
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220)
    else:
        st.markdown('<div class="empty-state">No executions yet</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<p class="section-title">Upcoming Scheduled</p>', unsafe_allow_html=True)
    upcoming = db.query(Schedule).filter(Schedule.enabled == True).order_by(Schedule.next_run).limit(10).all()
    
    if upcoming:
        rows = []
        for s in upcoming:
            rows.append({
                "Schedule": s.schedule_name or "Unnamed",
                "Frequency": s.frequency,
                "Next Run": s.next_run.strftime('%d %b, %H:%M') if s.next_run else "N/A"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220)
    else:
        st.markdown('<div class="empty-state">No scheduled jobs</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick Actions ──
st.markdown('<p class="section-title">Quick Actions</p>', unsafe_allow_html=True)
qc1, qc2, qc3, qc4 = st.columns(4)
with qc1:
    if st.button("New Campaign", use_container_width=True, type="primary"):
        st.switch_page("pages/4_New_Campaign.py")
with qc2:
    if st.button("AI Assistant", use_container_width=True):
        st.switch_page("pages/5_AI_Assistant.py")
with qc3:
    if st.button("Execution History", use_container_width=True):
        st.switch_page("pages/7_Execution_History.py")
with qc4:
    if st.button("Settings", use_container_width=True):
        st.switch_page("pages/1_Settings.py")

db.close()