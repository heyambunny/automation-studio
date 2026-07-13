import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Template

st.title("📄 Templates")

st.markdown("""
<div style="background:#E8F5E9;padding:10px 14px;border-radius:8px;border-left:4px solid #4CAF50;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#2E7D32;"><strong>📄 Reusable Templates</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
Save subject lines and email body templates for quick reuse in campaigns.<br>
Use variables like <code>{{BranchName}}</code>, <code>{{ReportType}}</code>, <code>{{Summary}}</code>, <code>{{SenderName}}</code>.
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

tab1, tab2 = st.tabs(["📧 Subject Line Templates", "📝 Email Body Templates"])

# ── Subject Line Templates ──
with tab1:
    st.subheader("Subject Line Templates")
    
    with st.expander("➕ Add New Subject Template"):
        template_name = st.text_input("Template Name", key="subj_name")
        template_text = st.text_input(
            "Subject Template",
            placeholder="e.g. {{ReportType}} - {{BranchName}} - {{Month}} {{Year}}",
            key="subj_text"
        )
        st.caption("Available: {{BranchName}}, {{CurrentDate}}, {{Month}}, {{Year}}, {{ReportType}}")
        
        if st.button("💾 Save Subject Template"):
            if template_name and template_text:
                new_template = Template(
                    template_name=template_name,
                    template_type="subject",
                    content=template_text
                )
                db.add(new_template)
                db.commit()
                st.success(f"Subject template '{template_name}' saved.")
                st.rerun()
            else:
                st.error("Please fill all fields.")
    
    # List saved subject templates
    subject_templates = db.query(Template).filter_by(template_type="subject").all()
    
    if subject_templates:
        st.write("**Saved Subject Templates:**")
        st.dataframe(
            pd.DataFrame([{"Name": t.template_name, "Template": t.content} for t in subject_templates]),
            use_container_width=True,
            hide_index=True
        )
        
        selected_subj = st.selectbox("Manage subject template", [t.template_name for t in subject_templates], key="sel_subj")
        if selected_subj:
            template = db.query(Template).filter_by(template_name=selected_subj, template_type="subject").first()
            if st.button("🗑️ Delete Subject Template", key="del_subj"):
                db.delete(template)
                db.commit()
                st.success(f"Deleted '{selected_subj}'.")
                st.rerun()
    else:
        st.info("No subject templates saved yet.")

st.divider()

# ── Email Body Templates ──
with tab2:
    st.subheader("Email Body Templates")
    
    with st.expander("➕ Add New Body Template"):
        body_name = st.text_input("Template Name", key="body_name")
        body_text = st.text_area(
            "Email Body",
            placeholder="""Dear Team,

Please find attached the {{ReportType}} for {{BranchName}}.

{{Summary}}

Regards,
{{SenderName}}
{{Signature}}""",
            height=200,
            key="body_text"
        )
        st.caption("Available: {{BranchName}}, {{CurrentDate}}, {{Month}}, {{Year}}, {{ReportType}}, {{Summary}}, {{SenderName}}, {{Signature}}")
        
        if st.button("💾 Save Body Template"):
            if body_name and body_text:
                new_template = Template(
                    template_name=body_name,
                    template_type="body",
                    content=body_text
                )
                db.add(new_template)
                db.commit()
                st.success(f"Body template '{body_name}' saved.")
                st.rerun()
            else:
                st.error("Please fill all fields.")
    
    # List saved body templates
    body_templates = db.query(Template).filter_by(template_type="body").all()
    
    if body_templates:
        st.write("**Saved Body Templates:**")
        st.dataframe(
            pd.DataFrame([{"Name": t.template_name, "Content": t.content[:100] + "..." if len(t.content) > 100 else t.content} for t in body_templates]),
            use_container_width=True,
            hide_index=True
        )
        
        selected_body = st.selectbox("Manage body template", [t.template_name for t in body_templates], key="sel_body")
        if selected_body:
            template = db.query(Template).filter_by(template_name=selected_body, template_type="body").first()
            
            with st.expander("📝 View Full Template"):
                st.text(template.content)
            
            if st.button("🗑️ Delete Body Template", key="del_body"):
                db.delete(template)
                db.commit()
                st.success(f"Deleted '{selected_body}'.")
                st.rerun()
    else:
        st.info("No body templates saved yet.")

db.close()