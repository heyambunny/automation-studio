# pages/5_AI_Assistant.py
import streamlit as st
import json
import os
import requests
from datetime import datetime
from database import SessionLocal
from models import Setting, SMTPProfile, Execution, EmailLog
from services.excel_reader import ExcelReader
from services.email_sender import EmailSender
from services.audit_service import log_action

st.title("🤖 AI Assistant")
st.markdown("""
<div style="margin-top:-30px;margin-bottom:10px;">
    <span style="background:#FEF2F2;border:1px solid #FECACA;border-radius:4px;padding:2px 10px;font-size:11px;font-weight:600;color:#DC2626;">BETA</span>
</div>
""", unsafe_allow_html=True)
st.caption("Type a command. AI handles everything.")

db = SessionLocal()

# Quick Ollama check
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=3)
    if r.status_code != 200:
        st.error("Ollama not responding.")
        st.stop()
except:
    st.error("Ollama not running.")
    st.stop()

setting = db.query(Setting).first()
folder = setting.folder_path if setting else ""
profiles = db.query(SMTPProfile).all()

branches = []
if os.path.exists(folder):
    for f in os.listdir(folder):
        if f.endswith(('.xlsx', '.csv')):
            branches.append(os.path.splitext(f)[0])

# Instructions
st.markdown("""
<div style="background:#E8F4FD;padding:10px 14px;border-radius:8px;border-left:4px solid #2196F3;margin-bottom:10px;">
<p style="margin:0;font-size:13px;color:#1565C0;"><strong>💡 How to use:</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#444;">
<b>Send:</b> <code>Send Ranchi IMP report to test@mail.com from sheet Summary cell A1</code><br>
<b>Custom:</b> <code>Email Mumbai Q1 data from cell C3 to manager@co.com, subject Q1 Results</code>
</p>
</div>
""", unsafe_allow_html=True)

command = st.text_area(
    "Your command",
    placeholder="Send Ranchi report to himanshub@evolvebrands.com from sheet Summary cell A1, subject IMP milestone",
    height=60
)

if command:
    st.divider()
    
    with st.spinner("🤔 Processing..."):
        prompt = f"""Extract JSON from this command. Available branches: {', '.join(branches[:10]) if branches else 'none'}

Command: "{command}"

Return ONLY: {{"branch":"x","recipient":"x","subject":"x","cell":"A1","sheet":"Summary"}}"""
        
        try:
            resp = requests.post(
                "http://host.docker.internal:11434/api/generate",
                json={"model": "qwen3:latest", "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.1, "max_tokens": 100}},
                timeout=60
            )
            
            if resp.status_code == 200:
                raw = resp.json().get("response", "").strip()
                
                # Extract JSON
                if "{" in raw and "}" in raw:
                    start = raw.index("{")
                    end = raw.index("}") + 1
                    data = json.loads(raw[start:end])
                else:
                    st.error("Could not parse. Try rephrasing.")
                    st.stop()
                
                branch = data.get("branch", "")
                recipient = data.get("recipient", "")
                subject = data.get("subject", "Report")
                cell = data.get("cell", "A1")
                sheet = data.get("sheet", "Summary")
                
                # Display
                st.markdown(f"""
                <div style="background:#F5F7FA;padding:10px 14px;border-radius:8px;border:1px solid #E0E0E0;">
                <table style="width:100%;font-size:13px;">
                <tr><td style="color:#666;width:80px;">📁 Branch</td><td><b>{branch}</b></td>
                <td style="color:#666;width:80px;">📧 To</td><td><b>{recipient}</b></td></tr>
                <tr><td style="color:#666;">📌 Subject</td><td><b>{subject}</b></td>
                <td style="color:#666;">📊 Cell</td><td><b>{sheet}!{cell}</b></td></tr>
                </table></div>""", unsafe_allow_html=True)
                
                if st.button("🚀 Send Now", type="primary", use_container_width=True):
                    if not recipient or not branch:
                        st.error("Missing branch or recipient.")
                    elif not profiles:
                        st.error("No SMTP profile.")
                    else:
                        file_path = None
                        for ext in ['.xlsx', '.csv']:
                            p = os.path.join(folder, f"{branch}{ext}")
                            if os.path.exists(p):
                                file_path = p
                                break
                        
                        if not file_path:
                            st.error(f"File not found: {branch}")
                        else:
                            profile = profiles[0]
                            sender = EmailSender({
                                "server": profile.smtp_server, "port": profile.smtp_port,
                                "email": profile.sender_email, "password": profile.password,
                                "use_tls": profile.use_tls, "sender_name": profile.sender_name or ""
                            })
                            
                            df = ExcelReader.detect_active_range(file_path, sheet, cell)
                            
                            if df is not None and not df.empty:
                                summary_text = ExcelReader.dataframe_to_text(df)
                                summary_html = ExcelReader.dataframe_to_html(df)
                                
                                with st.spinner("🤖 Generating..."):
                                    resp2 = requests.post(
                                        "http://host.docker.internal:11434/api/generate",
                                        json={"model": "qwen3:latest", "prompt": f"Summarize this data in 3-5 bullet points:\n{summary_text[:2000]}", "stream": False,
                                              "options": {"temperature": 0.3, "max_tokens": 300}},
                                        timeout=90
                                    )
                                    if resp2.status_code == 200:
                                        ai_body = resp2.json().get("response", "")
                                        # Format markdown to HTML
                                        import re
                                        ai_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_body)
                                        ai_body = ai_body.replace('\n', '<br>')
                                        # Convert bullet points
                                        ai_body = re.sub(r'<br>- ', '<br>• ', ai_body)
                                    else:
                                        ai_body = summary_html
                            else:
                                ai_body = "<p>No data found at the specified cell.</p>"
                            
                            body = f"""<p>Dear <strong>{branch}</strong> Team,</p>
<p>Please find below the <strong>{subject}</strong>.</p>
<div style="background:#f5f5f5;padding:10px 15px;border-radius:5px;margin:10px 0;">
<h4 style="margin:0 0 5px 0;">📊 Summary</h4>
{ai_body}
</div>
<p>Thanks &amp; Regards,<br><strong>{profile.sender_name}</strong></p>"""
                            
                            to_list = [r.strip() for r in recipient.split(",") if r.strip()]
                            
                            # Create execution record
                            execution = Execution(
                                user_id=1,
                                campaign_name=f"AI: {subject} - {branch}",
                                status="in_progress",
                                send_method="SMTP",
                                mode="ai/ai",
                                total_emails=1,
                                sent_count=0,
                                failed_count=0,
                                started_at=datetime.utcnow()
                            )
                            db.add(execution)
                            db.commit()
                            
                            with st.status("📧 Sending...", expanded=True) as s:
                                result = sender.send_email(to_list, subject, body, attachments=[file_path])
                                
                                # Log result
                                email_log = EmailLog(
                                    execution_id=execution.id,
                                    branch_name=branch,
                                    recipient_to=", ".join(to_list),
                                    subject=subject,
                                    status="sent" if result["success"] else "failed",
                                    error_message=result.get("message", "") if not result["success"] else "",
                                    sent_at=datetime.utcnow() if result["success"] else None
                                )
                                db.add(email_log)
                                
                                execution.status = "completed" if result["success"] else "failed"
                                execution.sent_count = 1 if result["success"] else 0
                                execution.failed_count = 0 if result["success"] else 1
                                execution.completed_at = datetime.utcnow()
                                db.commit()
                                
                                if result["success"]:
                                    s.update(label="✅ Sent!", state="complete")
                                    log_action("ai_assistant_sent", "execution", execution.id, f"{branch} - {subject}")
                                    st.balloons()
                                else:
                                    s.update(label="❌ Failed", state="error")
                                    st.error(result["message"])
                                    log_action("ai_assistant_failed", "execution", execution.id, f"{branch} - {result.get('message', '')}")
            else:
                st.error(f"Ollama error: {resp.status_code}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

db.close()