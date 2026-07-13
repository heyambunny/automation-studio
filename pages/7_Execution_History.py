# pages/7_Execution_History.py
import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Execution, EmailLog
from models import SMTPProfile, Setting
from datetime import datetime
import os
from services.audit_service import log_action

st.title("📋 Execution History")

st.markdown("""
<div style="background:#FCE4EC;padding:10px 14px;border-radius:8px;border-left:4px solid #E91E63;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#880E4F;"><strong>📊 Track all your campaigns here:</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
• Use <b>filters</b> to find campaigns by status or name<br>
• Click a campaign to see <b>per-branch email logs</b><br>
• <b>Retry</b> failed campaigns to resend only the failed emails
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

# ── Filters ──
col1, col2, col3 = st.columns(3)
with col1:
    all_statuses = ["completed", "in_progress", "queued", "failed", "pending"]
    status_filter = st.multiselect(
        "Status",
        all_statuses,
        default=all_statuses
    )
with col2:
    search = st.text_input("Search Campaign", placeholder="Campaign name...")
with col3:
    st.caption("")

st.divider()

# ── Query ──
query = db.query(Execution)

if status_filter:
    query = query.filter(Execution.status.in_(status_filter))
if search:
    query = query.filter(Execution.campaign_name.ilike(f"%{search}%"))

executions = query.order_by(Execution.created_at.desc()).all()

if executions:
    history_data = []
    for e in executions:
        history_data.append({
            "ID": e.id,
            "Campaign": e.campaign_name or "Unnamed",
            "Date": e.created_at.strftime("%Y-%m-%d %H:%M") if e.created_at else "",
            "Status": e.status.value if e.status else "N/A",
            "Send Method": e.send_method or "",
            "Mode": e.mode or "",
            "Total": e.total_emails,
            "Sent": e.sent_count,
            "Failed": e.failed_count
        })
    
    df = pd.DataFrame(history_data)
    
    def color_status(val):
        colors = {
            "completed": "background-color: #d4edda; color: #155724",
            "in_progress": "background-color: #cce5ff; color: #004085",
            "queued": "background-color: #fff3cd; color: #856404",
            "failed": "background-color: #f8d7da; color: #721c24",
            "pending": "background-color: #e2e3e5; color: #383d41",
        }
        return colors.get(val, "")
    
    styled_df = df.style.applymap(color_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # ── Per-Branch Email Log ──
    st.subheader("🔍 Per-Branch Email Log")
    selected_id = st.selectbox("Select Campaign to View Details", df["ID"].tolist(), format_func=lambda x: f"Campaign #{x}")
    
    if selected_id:
        logs = db.query(EmailLog).filter_by(execution_id=selected_id).all()
        if logs:
            log_data = []
            for l in logs:
                log_data.append({
                    "Branch": l.branch_name,
                    "To": l.recipient_to,
                    "CC": l.recipient_cc,
                    "Subject": l.subject,
                    "Status": l.status,
                    "Sent At": l.sent_at.strftime("%Y-%m-%d %H:%M:%S") if l.sent_at else "",
                    "Error": l.error_message or ""
                })
            st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
        else:
            st.info("No email logs for this campaign.")
    
    # ── Retry Failed ──
    failed_campaigns = [e for e in executions if e.status.value == "failed"]
    if failed_campaigns:
        st.divider()
        st.subheader("🔄 Retry Failed Campaigns")
        st.caption("Retry only the failed emails from a campaign.")
        retry_id = st.selectbox(
            "Select failed campaign to retry", 
            [e.id for e in failed_campaigns], 
            format_func=lambda x: f"#{x} - {next((e.campaign_name for e in failed_campaigns if e.id == x), '')}"
        )
        
        if st.button("🔁 Retry Campaign", type="primary"):
            st.session_state.confirm_retry = retry_id
        
        if st.session_state.get("confirm_retry") == retry_id:
            st.warning("⚠️ Retry this campaign? It will resend only failed emails.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Retry", key="confirm_retry_yes"):
                    from services.campaign_executor import CampaignExecutor
                    from database import SessionLocal as DB
                    import json
                    
                    failed_logs = db.query(EmailLog).filter(
                        EmailLog.execution_id == retry_id,
                        EmailLog.status == "failed"
                    ).all()
                    
                    if failed_logs:
                        st.info(f"Retrying {len(failed_logs)} failed emails...")
                        
                        execution = db.query(Execution).filter_by(id=retry_id).first()
                        execution.status = "in_progress"
                        db.commit()
                        
                        for log in failed_logs:
                            try:
                                branch = log.branch_name
                                setting = db.query(Setting).first()
                                folder_path = setting.folder_path if setting else ""
                                
                                file_path = None
                                for ext in ['.xlsx', '.csv']:
                                    p = os.path.join(folder_path, f"{branch}{ext}")
                                    if os.path.exists(p):
                                        file_path = p
                                        break
                                
                                if file_path:
                                    profile = db.query(SMTPProfile).first()
                                    if profile:
                                        from services.email_sender import EmailSender
                                        sender = EmailSender({
                                            "server": profile.smtp_server,
                                            "port": profile.smtp_port,
                                            "email": profile.sender_email,
                                            "password": profile.password,
                                            "use_tls": profile.use_tls,
                                            "sender_name": profile.sender_name or ""
                                        })
                                        
                                        to_list = [e.strip() for e in log.recipient_to.split(",") if e.strip()]
                                        
                                        result = sender.send_email(
                                            to_recipients=to_list,
                                            subject=log.subject or "Report",
                                            html_body=f"<p>Resending failed email.</p>",
                                            attachments=[file_path]
                                        )
                                        
                                        log.status = "sent" if result["success"] else "failed"
                                        log.error_message = result.get("message", "") if not result["success"] else ""
                                        log.sent_at = datetime.utcnow() if result["success"] else None
                                        db.commit()
                            except Exception as e:
                                log.status = "failed"
                                log.error_message = str(e)
                                db.commit()
                        
                        sent_count = db.query(EmailLog).filter(
                            EmailLog.execution_id == retry_id,
                            EmailLog.status == "sent"
                        ).count()
                        failed_count = db.query(EmailLog).filter(
                            EmailLog.execution_id == retry_id,
                            EmailLog.status == "failed"
                        ).count()
                        
                        execution.sent_count = sent_count
                        execution.failed_count = failed_count
                        execution.status = "completed" if failed_count == 0 else "completed"
                        db.commit()
                        
                        log_action("campaign_retried", "execution", retry_id, f"{sent_count} sent, {failed_count} failed")
                        st.success(f"✅ Retry done! {sent_count} sent, {failed_count} failed")
                        st.rerun()
                    else:
                        st.info("No failed emails found for this campaign.")
                    
                    st.session_state.confirm_retry = None
            with c2:
                if st.button("❌ Cancel", key="confirm_retry_no"):
                    st.session_state.confirm_retry = None
                    st.rerun()

else:
    st.info("No executions found matching your filters. Campaigns will appear here after you send them.")

db.close()