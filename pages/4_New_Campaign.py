# pages/3_New_Campaign.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json
from config import IS_WINDOWS
from database import SessionLocal
from models import Setting, SMTPProfile, Mapping, MappingEntry, Template, Execution, EmailLog, Schedule
from services.audit_service import log_action

st.title("🚀 New Campaign")

st.markdown("""
<div style="background:#F3E5F5;padding:10px 14px;border-radius:8px;border-left:4px solid #9C27B0;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#6A1B9A;"><strong>📋 Campaign Wizard — 5 Steps:</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
<b>Step 1:</b> Choose send method (SMTP/Outlook) • 
<b>Step 2:</b> Select mapping &amp; folder • 
<b>Step 3:</b> Configure content (Static or AI) • 
<b>Step 4:</b> Preview emails • 
<b>Step 5:</b> Save, Send, or Schedule
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

if "campaign_step" not in st.session_state:
    st.session_state.campaign_step = 1
if "campaign_config" not in st.session_state:
    st.session_state.campaign_config = {}

steps = ["Send Method", "Mapping", "Content", "Preview", "Action"]
step_index = st.session_state.campaign_step - 1
st.progress(step_index / (len(steps) - 1), text=f"Step {st.session_state.campaign_step} of {len(steps)}: {steps[step_index]}")
st.divider()

setting = db.query(Setting).first()
folder_path = setting.folder_path if setting else ""
default_sheet = setting.default_sheet_name if setting else "Summary"
default_cell = setting.default_starting_cell if setting else "B5"

# ── STEP 1 ──
if st.session_state.campaign_step == 1:
    st.subheader("Step 1: Choose Send Method")
    
    if IS_WINDOWS:
        send_method = st.radio("Send Method", ["Outlook (Send Now)", "Outlook (Save to Drafts)", "SMTP"], horizontal=True)
    else:
        send_method = st.radio("Send Method", ["SMTP"], horizontal=True)
        st.caption("💡 Outlook integration is only available on Windows.")
    
    if "SMTP" in send_method:
        profiles = db.query(SMTPProfile).all()
        if profiles:
            profile_names = [p.profile_name for p in profiles]
            default_profile = next((p.profile_name for p in profiles if p.is_default), profile_names[0])
            selected_profile = st.selectbox("Select SMTP Profile", profile_names, index=profile_names.index(default_profile))
            st.session_state.campaign_config["smtp_profile"] = selected_profile
            profile = db.query(SMTPProfile).filter_by(profile_name=selected_profile).first()
            if profile:
                st.session_state.campaign_config["sender_name"] = profile.sender_name or ""
        else:
            st.warning("No SMTP profiles found. Please add one in Settings.")
    
    st.session_state.campaign_config["send_method"] = send_method
    
    if st.button("Next →", type="primary"):
        st.session_state.campaign_step = 2
        st.rerun()

# ── STEP 2 ──
elif st.session_state.campaign_step == 2:
    st.subheader("Step 2: Select Mapping")
    
    mapping_option = st.radio("Choose Mapping", ["Use Saved Mapping", "Upload New Mapping"], horizontal=True)
    
    if mapping_option == "Use Saved Mapping":
        mappings = db.query(Mapping).all()
        if mappings:
            mapping_names = [m.mapping_name for m in mappings]
            selected_mapping = st.selectbox("Saved Mappings", mapping_names)
            st.session_state.campaign_config["mapping_id"] = next(m.id for m in mappings if m.mapping_name == selected_mapping)
            mapping = db.query(Mapping).filter_by(mapping_name=selected_mapping).first()
            entries = db.query(MappingEntry).filter_by(mapping_id=mapping.id).all()
            if entries:
                preview = [{"BranchName": e.branch_name, "To": e.to_recipients, "CC": e.cc_recipients} for e in entries]
                st.dataframe(pd.DataFrame(preview), use_container_width=True)
        else:
            st.warning("No saved mappings. Please upload one.")
    else:
        uploaded_file = st.file_uploader("Upload Mapping CSV", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df, use_container_width=True)
            st.session_state.campaign_config["temp_mapping"] = df.to_dict("records")
    
    st.divider()
    st.subheader("📁 Campaign Folder (Optional)")
    st.caption("Override the default folder path for this campaign only.")
    
    campaign_folder = st.text_input(
        "Folder path for this campaign",
        value=st.session_state.campaign_config.get("campaign_folder", ""),
        placeholder="Leave empty to use default folder from Settings",
        help="If empty, the default folder from Settings will be used."
    )
    st.session_state.campaign_config["campaign_folder"] = campaign_folder

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.campaign_step = 1
            st.rerun()
    with col2:
        if st.button("Next →", type="primary"):
            st.session_state.campaign_step = 3
            st.rerun()

# ── STEP 3: Content Settings ──
elif st.session_state.campaign_step == 3:
    st.subheader("Step 3: Content Settings")
    
    saved_vars = st.session_state.campaign_config.get("variables", {})
    
    # Detect group variable name from mapping
    mapping_id = st.session_state.campaign_config.get("mapping_id")
    group_var = "BranchName"
    if mapping_id:
        entries = db.query(MappingEntry).filter_by(mapping_id=mapping_id).all()
        if entries:
            group_var = "BranchName"
    elif st.session_state.campaign_config.get("temp_mapping"):
        temp = st.session_state.campaign_config["temp_mapping"]
        if temp and len(temp) > 0:
            keys = [k for k in temp[0].keys() if k.lower() not in ["to", "cc"]]
            if keys:
                group_var = keys[0]
    
    group_var_placeholder = f"{{{{{group_var}}}}}"
    st.session_state.campaign_config["group_var"] = group_var
    st.session_state.campaign_config["group_var_placeholder"] = group_var_placeholder
    
    st.write("**How should the email content be generated?**")
    current_mode = st.session_state.campaign_config.get("mode", "static/static")
    mode = st.radio(
        "Content Generation Mode",
        [
            "✍️ Static — I'll write the subject and body manually",
            "🤖 AI Generated — Let AI create the content from data"
        ],
        key="mode_selection",
        index=0 if current_mode == "static/static" else 1
    )
    
    use_ai = "AI" in mode
    st.session_state.campaign_config["mode"] = "ai/ai" if use_ai else "static/static"
    
    st.divider()
    
    if use_ai:
        st.write("**AI Generation Mode**")
        current_ai = st.session_state.campaign_config.get("ai_option", "auto")
        ai_index = 0 if current_ai == "auto" else (1 if current_ai == "guided" else 2)
        ai_option = st.radio(
            "Choose how AI generates content",
            [
                "🔍 Auto — AI reads the data and generates everything automatically",
                "💬 Guided — I'll provide context to help AI (recommended)",
                "📝 Prompt Only — No data file, just generate from my instructions"
            ],
            key="ai_option",
            index=ai_index
        )
        
        ai_option_map = {
            "🔍 Auto — AI reads the data and generates everything automatically": "auto",
            "💬 Guided — I'll provide context to help AI (recommended)": "guided",
            "📝 Prompt Only — No data file, just generate from my instructions": "prompt_only"
        }
        st.session_state.campaign_config["ai_option"] = ai_option_map[ai_option]
        is_prompt_only = ai_option_map[ai_option] == "prompt_only"
        
        if is_prompt_only:
            st.info("💡 No attachment will be sent. AI will generate content from your instructions only.")
            user_context = st.text_area(
                "Instructions for AI",
                value=st.session_state.campaign_config.get("user_context", ""),
                placeholder="e.g. Send a weekly update to all branches about the new MS Scheme policy changes...",
                height=120
            )
            st.session_state.campaign_config["user_context"] = user_context
            st.session_state.campaign_config["attach_file"] = False
            st.session_state.campaign_config["variables"] = {"ReportType": "", "Month": "", "Year": ""}
        else:
            st.session_state.campaign_config["attach_file"] = True
            
            if ai_option_map[ai_option] == "guided":
                st.write("**📝 Add Context for AI**")
                user_context = st.text_area(
                    "Describe what this report is about",
                    value=st.session_state.campaign_config.get("user_context", ""),
                    placeholder="e.g. This is the monthly MS Scheme performance report showing member scan counts by branch. Focus on high and low performing branches.",
                    height=80
                )
                st.caption("💡 AI will use this context + data to generate subject and body")
                st.session_state.campaign_config["user_context"] = user_context
            else:
                st.session_state.campaign_config["user_context"] = ""
            
            st.session_state.campaign_config["variables"] = {"ReportType": "", "Month": "", "Year": ""}
        
        if not is_prompt_only:
            st.divider()
            st.subheader("📊 Sheet Settings")
            col1, col2 = st.columns(2)
            with col1:
                sheet_name = st.text_input("Summary Sheet Name", value=default_sheet)
            with col2:
                start_cell = st.text_input("Starting Cell", value=default_cell)
            st.session_state.campaign_config["sheet_name"] = sheet_name
            st.session_state.campaign_config["start_cell"] = start_cell
    
    else:
        # ── STATIC MODE ──
        st.session_state.campaign_config["ai_option"] = ""
        st.session_state.campaign_config["user_context"] = ""
        
        # Subject
        st.write("**Subject Line**")
        st.caption("📌 Available variables (click to copy):")
        subj_cols = st.columns(3)
        subj_vars = [group_var_placeholder, "{{ReportType}}", "{{Summary}}"]
        
        for i, var in enumerate(subj_vars):
            with subj_cols[i]:
                st.code(var, language=None)
        
        subject = st.text_input(
            "Subject Template",
            value=st.session_state.campaign_config.get("subject", ""),
            placeholder=f"e.g. {{{{ReportType}}}} - {group_var_placeholder}",
            key="subject_input"
        )
        st.session_state.campaign_config["subject"] = subject
        
        st.divider()
        
        # Report Type
        report_type = st.text_input(
            "Report Type",
            value=saved_vars.get("ReportType", "Performance Report"),
            placeholder="e.g. Monthly Performance Report",
            key="var_report"
        )
        st.session_state.campaign_config["variables"] = {"Month": "", "Year": "", "ReportType": report_type}
        
                # Body
        st.write("**Email Body**")
        
        body = st.text_area(
            "Email Body Template",
            value=st.session_state.campaign_config.get("body_template", ""),
            placeholder=f"Dear {group_var_placeholder} Team,\n\nPlease find attached the {{{{ReportType}}}} for your branch.\n\n{{{{Summary}}}}\n\nThanks & Regards,\n{{{{SenderName}}}}",
            height=200,
            key="custom_body"
        )
        st.session_state.campaign_config["body_template"] = body
        
        body_templates = db.query(Template).filter_by(template_type="body").all()
        if body_templates:
            selected_body = st.selectbox("Or pick saved body template", ["Custom"] + [t.template_name for t in body_templates])
            if selected_body != "Custom":
                template = db.query(Template).filter_by(template_name=selected_body, template_type="body").first()
                if template:
                    st.session_state.campaign_config["body_template"] = template.content
                    st.rerun()
        
        # Attachment toggle
        st.divider()
        attach = st.checkbox("📎 Attach Excel file to email", value=st.session_state.campaign_config.get("attach_file", True))
        st.session_state.campaign_config["attach_file"] = attach
        
        if attach:
            st.subheader("📊 Sheet Settings")
            col1, col2 = st.columns(2)
            with col1:
                sheet_name = st.text_input("Summary Sheet Name", value=default_sheet)
            with col2:
                start_cell = st.text_input("Starting Cell", value=default_cell)
            st.session_state.campaign_config["sheet_name"] = sheet_name
            st.session_state.campaign_config["start_cell"] = start_cell
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.campaign_step = 2
            st.rerun()
    with col2:
        if st.button("Next →", type="primary"):
            st.session_state.campaign_step = 4
            st.rerun()

# ── STEP 4: Mail Merge Preview ──
elif st.session_state.campaign_step == 4:
    st.subheader("Step 4: Mail Merge Preview")
    
    # Use campaign-specific folder or fallback to default
    campaign_folder = st.session_state.campaign_config.get("campaign_folder", "") or folder_path
    
    is_prompt_only = st.session_state.campaign_config.get("ai_option") == "prompt_only"
    group_var = st.session_state.campaign_config.get("group_var", "BranchName")
    group_var_placeholder = st.session_state.campaign_config.get("group_var_placeholder", "{{BranchName}}")
    
    if is_prompt_only:
        mapping_id = st.session_state.campaign_config.get("mapping_id")
        if mapping_id:
            entries = db.query(MappingEntry).filter_by(mapping_id=mapping_id).all()
        elif st.session_state.campaign_config.get("temp_mapping"):
            entries = st.session_state.campaign_config["temp_mapping"]
        else:
            entries = []
        
        if entries:
            preview_data = []
            for e in entries:
                branch_name = e.branch_name if hasattr(e, 'branch_name') else e.get(group_var, e.get("BranchName", ""))
                preview_data.append({
                    group_var: branch_name,
                    "To": e.to_recipients if hasattr(e, 'to_recipients') else e.get("To"),
                    "CC": e.cc_recipients if hasattr(e, 'cc_recipients') else e.get("CC", ""),
                    "File": "N/A",
                    "Status": "Ready (No attachment)"
                })
            st.caption(f"📧 {len(preview_data)} emails ready (no attachments)")
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
            st.session_state.campaign_config["preview_data"] = preview_data
    
    elif not campaign_folder:
        st.error("No folder configured. Set it in Settings or upload a file in Step 2.")
    else:
        mapping_id = st.session_state.campaign_config.get("mapping_id")
        if mapping_id:
            entries = db.query(MappingEntry).filter_by(mapping_id=mapping_id).all()
        elif st.session_state.campaign_config.get("temp_mapping"):
            entries = st.session_state.campaign_config["temp_mapping"]
        else:
            entries = []
        
        if entries:
            preview_data = []
            for e in entries:
                branch_name = e.branch_name if hasattr(e, 'branch_name') else e.get(group_var, e.get("BranchName", ""))
                file_exists = os.path.exists(os.path.join(campaign_folder, f"{branch_name}.xlsx")) or \
                             os.path.exists(os.path.join(campaign_folder, f"{branch_name}.csv"))
                preview_data.append({
                    group_var: branch_name,
                    "To": e.to_recipients if hasattr(e, 'to_recipients') else e.get("To"),
                    "CC": e.cc_recipients if hasattr(e, 'cc_recipients') else e.get("CC", ""),
                    "File": "✅" if file_exists else "❌",
                    "Status": "Ready" if file_exists else "Missing"
                })
            
            st.session_state.campaign_config["preview_data"] = preview_data
            st.caption(f"📧 {len(preview_data)} branches found")
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
            
            # Email preview
            st.divider()
            st.subheader("📧 Email Preview")
            
            ready_branches = [d[group_var] for d in preview_data if d["Status"] == "Ready"]
            if ready_branches:
                selected_branch = st.selectbox("Select branch to preview", ready_branches)
                
                if selected_branch:
                    branch_data = next(d for d in preview_data if d[group_var] == selected_branch)
                    mode = st.session_state.campaign_config.get("mode", "static/static")
                    variables = st.session_state.campaign_config.get("variables", {})
                    report_type = variables.get("ReportType", "Performance Report")
                    sender_name = st.session_state.campaign_config.get("sender_name", "Automation Studio")
                    
                    if mode == "static/static":
                        subject_template = st.session_state.campaign_config.get("subject", "")
                        body_template = st.session_state.campaign_config.get("body_template", "")
                        preview_subject = subject_template.replace(group_var_placeholder, selected_branch)
                        preview_subject = preview_subject.replace("{{ReportType}}", report_type)
                        preview_subject = preview_subject.replace("{{Summary}}", "[Summary from file]")
                        preview_body = body_template.replace(group_var_placeholder, selected_branch)
                        preview_body = preview_body.replace("{{ReportType}}", report_type)
                        preview_body = preview_body.replace("{{Summary}}", "[Summary from file]")
                        preview_body = preview_body.replace("{{SenderName}}", sender_name)
                        preview_body = preview_body.replace("\n", "<br>")
                    else:
                        preview_subject = f"[AI Generated] - {selected_branch}"
                        preview_body = f"""<p>Dear <strong>{selected_branch}</strong> Team,</p>
<div style="background-color:#f5f5f5;padding:10px;border-radius:5px;margin:8px 0;">
<p style="color:#666;">🤖 AI will generate content based on the data in the file.</p>
</div>
<p>Thanks &amp; Regards,<br><strong>{sender_name}</strong></p>"""
                    
                    st.markdown(f"**📌 Subject:** {preview_subject}")
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style="border:1px solid #ddd;border-radius:8px;padding:20px;max-width:600px;">
                            <p style="margin:0 0 5px 0;"><strong>To:</strong> {branch_data['To']}</p>
                            {f'<p style="margin:0 0 10px 0;"><strong>CC:</strong> {branch_data["CC"]}</p>' if branch_data.get('CC') else ''}
                            <p style="margin:0 0 10px 0;"><strong>Subject:</strong> {preview_subject}</p>
                            <hr style="margin:10px 0;">
                            {preview_body}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show attachment if exists
                    file_path = os.path.join(campaign_folder, f"{selected_branch}.xlsx")
                    if not os.path.exists(file_path):
                        file_path = os.path.join(campaign_folder, f"{selected_branch}.csv")
                    if os.path.exists(file_path):
                        st.caption(f"📎 Attachment: {os.path.basename(file_path)}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.campaign_step = 3
            st.rerun()
    with col2:
        if st.button("Next →", type="primary"):
            st.session_state.campaign_step = 5
            st.rerun()

# ── STEP 5: Action ──
elif st.session_state.campaign_step == 5:
    st.subheader("Step 5: Choose Action")
    
    if IS_WINDOWS:
        action = st.radio("Action", ["📨 Send Now", "📝 Save to Outlook Drafts", "⏰ Schedule One-Time", "🔁 Schedule Multiple"])
    else:
        action = st.radio("Action", ["📨 Send Now", "⏰ Schedule One-Time", "🔁 Schedule Multiple"])
    
    st.session_state.campaign_config["action"] = action
    
    if "Schedule" in action:
        if "Multiple" in action:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "custom"])
            st.session_state.campaign_config["frequency"] = frequency
            if frequency == "custom":
                cron = st.text_input("Cron Expression", placeholder="0 9 * * 1")
                st.session_state.campaign_config["cron"] = cron
        else:
            st.session_state.campaign_config["frequency"] = "once"
            st.session_state.campaign_config["schedule_date"] = str(st.date_input("Date"))
            st.session_state.campaign_config["schedule_time"] = str(st.time_input("Time"))
    
    st.divider()

    st.subheader("💾 Save Campaign for Reuse")
    save_name = st.text_input("Campaign Name", placeholder="e.g. Monthly MS Scheme Report", key="save_campaign_name")
    if st.button("💾 Save Campaign", use_container_width=True):
        if save_name:
            import json
            recipes_dir = "recipes"
            os.makedirs(recipes_dir, exist_ok=True)
            filename = f"{save_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            config_to_save = st.session_state.campaign_config.copy()
            config_to_save['saved_name'] = save_name
            config_to_save['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(os.path.join(recipes_dir, filename), 'w') as f:
                json.dump(config_to_save, f, indent=2)
            st.success(f"Campaign '{save_name}' saved!")
            log_action("campaign_saved", "campaign_recipe", None, save_name)
        else:
            st.error("Please enter a campaign name.")

    st.divider()        
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.campaign_step = 4
            st.rerun()
    with col2:
        if st.button("🚀 Execute Campaign", type="primary"):
            st.session_state.confirm_execute = True
            st.rerun()
    
    # ── Confirmation Dialog ──
    if st.session_state.get("confirm_execute"):
        st.warning("⚠️ Are you sure you want to send all emails?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, Send Now", type="primary"):
                st.session_state.confirm_execute = False
                
                from services.campaign_executor import CampaignExecutor
                from services.scheduler_service import scheduler_service
                from database import SessionLocal as DB
                
                config = st.session_state.campaign_config
                action_type = config.get("action", "Send Now")
                
                if "Schedule" in action_type:
                    schedule = Schedule(
                        user_id=1,
                        schedule_name=f"{config.get('variables', {}).get('ReportType', 'Campaign')}",
                        campaign_config=json.dumps(config),
                        frequency=config.get("frequency", "once"),
                        cron_expression=config.get("cron", ""),
                        enabled=True
                    )
                    db.add(schedule)
                    db.commit()
                    scheduler_service.add_schedule(schedule.id, config, config.get("frequency", "once"), config.get("schedule_date"), config.get("schedule_time"), config.get("cron"))
                    st.success("✅ Campaign scheduled!")
                    log_action("campaign_scheduled", "schedule", schedule.id, schedule.schedule_name)
                else:
                    execution = Execution(
                        user_id=1,
                        campaign_name=f"{config.get('variables', {}).get('ReportType', 'Campaign')}",
                        status="queued",
                        send_method=config.get("send_method", ""),
                        mode=config.get("mode", ""),
                        total_emails=len(config.get("preview_data", [])),
                        sent_count=0,
                        failed_count=0
                    )
                    db.add(execution)
                    db.commit()
                    
                    with st.status("🚀 Executing Campaign...", expanded=True) as status_container:
                        st.write("⏳ Preparing to send emails...")
                        import time
                        start_time = time.time()
                        executor_db = DB()
                        executor = CampaignExecutor(execution.id, config, executor_db)
                        result = executor.execute()
                        executor_db.close()
                        elapsed = time.time() - start_time
                        
                        if result["success"]:
                            db.refresh(execution)
                            status_container.update(label="✅ Campaign Completed!", state="complete", expanded=True)
                            st.write(f"📧 **{execution.sent_count}** emails sent successfully")
                            st.write(f"❌ **{execution.failed_count}** failed")
                            st.write(f"⏱️ Time taken: **{elapsed:.1f}** seconds")
                            log_action("campaign_executed", "execution", execution.id, 
                                      f"{execution.campaign_name} - {execution.sent_count} sent, {execution.failed_count} failed")
                            st.balloons()
                        else:
                            status_container.update(label="❌ Campaign Failed!", state="error", expanded=True)
                            st.error(f"Error: {result.get('error', 'Unknown error')}")
                            log_action("campaign_failed", "execution", execution.id, 
                                      f"{execution.campaign_name} - {result.get('error', '')}")
                
                st.session_state.campaign_step = 1
                st.session_state.campaign_config = {}
                st.rerun()
        with c2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_execute = False
                st.rerun()

db.close()