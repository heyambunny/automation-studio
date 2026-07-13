import streamlit as st
import pandas as pd
from config import IS_WINDOWS
from database import SessionLocal
from models import EmailLog, Execution

st.title("📝 Drafts")

st.markdown("""
<div style="background:#E3F2FD;padding:10px 14px;border-radius:8px;border-left:4px solid #2196F3;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#1565C0;"><strong>📝 Outlook Drafts</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
Drafts saved to your local Outlook from campaigns using the <b>"Save to Outlook Drafts"</b> option.<br>
Available only on Windows with Outlook integration enabled.
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

if not IS_WINDOWS:
    st.warning("Outlook Drafts are only available on Windows.")
else:
    st.caption("Drafts saved to your local Outlook.")
    
    # Get drafts from email logs
    drafts = db.query(EmailLog).filter(EmailLog.status == "draft_saved").order_by(EmailLog.sent_at.desc()).all()
    
    if drafts:
        draft_data = []
        for d in drafts:
            execution = db.query(Execution).filter_by(id=d.execution_id).first()
            draft_data.append({
                "ID": d.id,
                "Campaign": execution.campaign_name if execution else "N/A",
                "Branch": d.branch_name,
                "Recipient": d.recipient_to,
                "Subject": d.subject,
                "Saved At": d.sent_at.strftime("%Y-%m-%d %H:%M") if d.sent_at else ""
            })
        
        df = pd.DataFrame(draft_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total drafts: {len(df)}")
        
        # View draft detail
        selected_draft = st.selectbox("Select draft to view", df["ID"].tolist(), format_func=lambda x: f"Draft #{x}")
        if selected_draft:
            draft = db.query(EmailLog).filter_by(id=selected_draft).first()
            st.subheader(f"📧 {draft.subject}")
            st.write(f"**To:** {draft.recipient_to}")
            if draft.recipient_cc:
                st.write(f"**CC:** {draft.recipient_cc}")
            st.write(f"**Branch:** {draft.branch_name}")
            if draft.error_message:
                st.text_area("Body Preview", draft.error_message, height=200, disabled=True)
    else:
        st.info("No drafts saved yet. Create a campaign and choose 'Save to Outlook Drafts'.")

db.close()