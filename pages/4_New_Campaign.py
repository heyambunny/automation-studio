# pages/4_New_Campaign.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json
import uuid
import re
from database import SessionLocal
from models import Setting, SMTPProfile, Mapping, MappingEntry, Template, Execution, EmailLog, Schedule
from services.audit_service import log_action
from services.excel_reader import ExcelReader

st.title("🚀 New Campaign")

db = SessionLocal()

if "campaign_step" not in st.session_state:
    st.session_state.campaign_step = 1
if "campaign_config" not in st.session_state:
    st.session_state.campaign_config = {}

steps = ["Send Method", "Mapping & Files", "Content", "Preview", "Action"]
step_index = st.session_state.campaign_step - 1
st.progress(step_index / (len(steps) - 1), text=f"Step {st.session_state.campaign_step} of {len(steps)}: {steps[step_index]}")
st.divider()

setting = db.query(Setting).filter_by(user_id=st.session_state.get("user_id", 1)).first()
default_sheet = setting.default_sheet_name if setting else "Summary"
default_cell = setting.default_starting_cell if setting else "B5"

# ── STEP 1 ──
if st.session_state.campaign_step == 1:
    st.subheader("Step 1: Choose Send Method")
    
    send_method = st.radio("Send Method", ["SMTP"], horizontal=True)
    
    if "SMTP" in send_method:
        if st.session_state.get("user_role") == "admin":
            profiles = db.query(SMTPProfile).all()
        else:
            profiles = db.query(SMTPProfile).filter_by(user_id=st.session_state.get("user_id", 1)).all()
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
    st.subheader("Step 2: Select Mapping & Upload Files")
    
    mapping_option = st.radio("Choose Mapping", ["Use Saved Mapping", "Upload New Mapping"], horizontal=True)
    
    if mapping_option == "Use Saved Mapping":
        if st.session_state.get("user_role") == "admin":
            mappings = db.query(Mapping).all()
        else:
            mappings = db.query(Mapping).filter_by(user_id=st.session_state.get("user_id", 1)).all()
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
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.campaign_step = 1
            st.rerun()
    with col2:
        if st.button("Next →", type="primary"):
            st.session_state.campaign_step = 3
            st.rerun()
    
    st.divider()
    st.subheader("📁 Campaign Files")
    st.caption("Upload all branch Excel/CSV files. File names should match branch names in the mapping.")
    
    campaign_folder_id = st.session_state.campaign_config.get("campaign_folder_id", str(uuid.uuid4())[:8])
    campaign_upload_dir = os.path.join("uploads", "campaigns", campaign_folder_id)
    os.makedirs(campaign_upload_dir, exist_ok=True)
    st.session_state.campaign_config["campaign_folder"] = campaign_upload_dir
    st.session_state.campaign_config["campaign_folder_id"] = campaign_folder_id
    
    existing_files = [f for f in os.listdir(campaign_upload_dir) if f.endswith(('.xlsx', '.csv'))]
    if existing_files:
        st.success(f"📂 {len(existing_files)} files in campaign folder")
        with st.expander("📋 View / Manage Files"):
            for f in existing_files:
                col_f, col_d = st.columns([4, 1])
                with col_f:
                    st.write(f"📎 {f}")
                with col_d:
                    if st.button("🗑️", key=f"del_{f}"):
                        os.remove(os.path.join(campaign_upload_dir, f))
                        st.rerun()
            
            if st.button("🗑️ Clear All Files", type="secondary"):
                for f in existing_files:
                    os.remove(os.path.join(campaign_upload_dir, f))
                st.success("All files cleared")
                st.rerun()
    
    uploaded_files = st.file_uploader(
        "Upload branch files (drag & drop)",
        type=["xlsx", "csv"],
        accept_multiple_files=True,
        key="campaign_files",
        help="Upload all branch Excel files. File names should match branch names in the mapping."
    )
    
    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(campaign_upload_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.success(f"✅ {len(uploaded_files)} files uploaded")
        st.rerun()

# ── STEP 3: Content Settings ──
elif st.session_state.campaign_step == 3:
    st.subheader("Step 3: Content Settings")
    
    saved_vars = st.session_state.campaign_config.get("variables", {})
    
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
    st.session_state.campaign_config["mode"] = "static/static"
    
    st.write("**Subject Line**")
    st.caption("📌 Available variables (click to copy):")
    subj_cols = st.columns(4)
    subj_vars = [group_var_placeholder, "{{ReportType}}", "{{Summary}}", "{{Cell:B2}}"]
    for i, var in enumerate(subj_vars):
        with subj_cols[i]:
            st.code(var, language=None)
    st.caption("💡 Use {{Cell:B2}} to insert a value from cell B2. Use {{Cell:Sheet2!C5}} for another sheet.")
    
    subject = st.text_input(
        "Subject Template",
        value=st.session_state.campaign_config.get("subject", ""),
        placeholder=f"e.g. {{{{ReportType}}}} - {group_var_placeholder}",
        key="subject_input"
    )
    st.session_state.campaign_config["subject"] = subject
    
    st.divider()
    
    report_type = st.text_input(
        "Report Type",
        value=saved_vars.get("ReportType", "Performance Report"),
        placeholder="e.g. Monthly Performance Report",
        key="var_report"
    )
    st.session_state.campaign_config["variables"] = {"ReportType": report_type}
    
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
    
    st.divider()
    attach = st.checkbox("📎 Attach Excel file to email", value=True)
    st.session_state.campaign_config["attach_file"] = attach
    
    # ── Sheet Settings with dropdown ──
    st.subheader("📊 Sheet Settings")
    
    campaign_folder = st.session_state.campaign_config.get("campaign_folder", "")
    sheet_names = []
    
    if campaign_folder and os.path.exists(campaign_folder):
        excel_files = [f for f in os.listdir(campaign_folder) if f.endswith(('.xlsx', '.xlsm'))]
        if excel_files:
            first_file = os.path.join(campaign_folder, excel_files[0])
            try:
                import openpyxl
                wb = openpyxl.load_workbook(first_file, read_only=True)
                sheet_names = wb.sheetnames
                wb.close()
            except:
                sheet_names = []
    
    col1, col2 = st.columns(2)
    with col1:
        if sheet_names:
            default_sheet_index = sheet_names.index(default_sheet) if default_sheet in sheet_names else 0
            sheet_name = st.selectbox("Summary Sheet", sheet_names, index=default_sheet_index)
            st.caption(f"📄 Detected from: {excel_files[0]}")
        else:
            sheet_name = st.text_input("Summary Sheet Name", value=default_sheet)
    with col2:
        start_cell = st.text_input("Starting Cell", value=default_cell)
    
    st.session_state.campaign_config["sheet_name"] = sheet_name
    st.session_state.campaign_config["start_cell"] = start_cell
    
    st.session_state.campaign_config["ai_option"] = ""
    st.session_state.campaign_config["user_context"] = ""
    
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
    
    campaign_folder = st.session_state.campaign_config.get("campaign_folder", "")
    group_var = st.session_state.campaign_config.get("group_var", "BranchName")
    group_var_placeholder = st.session_state.campaign_config.get("group_var_placeholder", "{{BranchName}}")
    
    if not campaign_folder:
        st.error("No files uploaded. Go back to Step 2 and upload files.")
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
                cc_value = e.cc_recipients if hasattr(e, 'cc_recipients') else e.get("CC", "")
                if not cc_value or str(cc_value).lower() == "nan" or pd.isna(cc_value):
                    cc_value = ""
                preview_data.append({
                    group_var: branch_name,
                    "To": e.to_recipients if hasattr(e, 'to_recipients') else e.get("To"),
                    "CC": cc_value,
                    "File": "✅" if file_exists else "❌",
                    "Status": "Ready" if file_exists else "Missing"
                })
            
            st.session_state.campaign_config["preview_data"] = preview_data
            st.caption(f"📧 {len(preview_data)} branches found")
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("👁️ Email Preview")
            
            ready_branches = [d[group_var] for d in preview_data if d["Status"] == "Ready"]
            if ready_branches:
                selected_preview = st.selectbox("Select branch to preview email", ready_branches)
                
                if selected_preview:
                    branch_data = next(d for d in preview_data if d[group_var] == selected_preview)
                    variables = st.session_state.campaign_config.get("variables", {})
                    report_type = variables.get("ReportType", "Performance Report")
                    sender_name = st.session_state.campaign_config.get("sender_name", "Automation Studio")
                    subject_template = st.session_state.campaign_config.get("subject", "")
                    body_template = st.session_state.campaign_config.get("body_template", "")
                    sheet_name = st.session_state.campaign_config.get("sheet_name", "Summary")
                    start_cell = st.session_state.campaign_config.get("start_cell", "B5")
                    
                    file_path = os.path.join(campaign_folder, f"{selected_preview}.xlsx")
                    if not os.path.exists(file_path):
                        file_path = os.path.join(campaign_folder, f"{selected_preview}.csv")
                    
                    summary_html = ""
                    cell_data = {}
                    if os.path.exists(file_path):
                        summary_df = ExcelReader.detect_active_range(file_path, sheet_name, start_cell)
                        summary_html = ExcelReader.dataframe_to_html(summary_df) if summary_df is not None else "<p>No summary data found.</p>"
                        
                        user_template = body_template + " " + subject_template
                        cell_refs = re.findall(r'\{\{Cell:(.*?)\}\}', user_template)
                        for ref in cell_refs:
                            if '!' in ref:
                                s, c = ref.split('!')
                            else:
                                s, c = sheet_name, ref
                            val = ExcelReader.get_cell_value(file_path, s, c)
                            cell_data[f"{s}!{c}"] = val
                            cell_data[ref] = val
                    
                    preview_subject = subject_template.replace(group_var_placeholder, selected_preview)
                    preview_subject = preview_subject.replace("{{ReportType}}", report_type)
                    for ref, val in cell_data.items():
                        preview_subject = preview_subject.replace(f"{{{{Cell:{ref}}}}}", str(val))
                    
                    preview_body = body_template.replace(group_var_placeholder, selected_preview)
                    preview_body = preview_body.replace("{{ReportType}}", report_type)
                    preview_body = preview_body.replace("{{Summary}}", summary_html)
                    preview_body = preview_body.replace("{{SenderName}}", sender_name)
                    for ref, val in cell_data.items():
                        preview_body = preview_body.replace(f"{{{{Cell:{ref}}}}}", str(val))
                    preview_body = preview_body.replace("\n", "<br>")
                    
                    st.markdown(f"""
                    <div style="max-width:640px;margin:0 auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;font-family:'Inter',sans-serif;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                        <div style="background:#f9fafb;padding:16px 20px;border-bottom:1px solid #e5e7eb;">
                            <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">Email Preview</div>
                            <div style="font-size:13px;margin-bottom:4px;"><strong>From:</strong> {sender_name}</div>
                            <div style="font-size:13px;margin-bottom:4px;"><strong>To:</strong> {branch_data['To']}</div>
                            {f'<div style="font-size:13px;margin-bottom:4px;"><strong>CC:</strong> {branch_data["CC"]}</div>' if branch_data.get('CC') and str(branch_data.get('CC')).lower() != 'nan' else ''}
                            <div style="font-size:13px;"><strong>Subject:</strong> {preview_subject}</div>
                        </div>
                        <div style="padding:24px 20px;font-size:14px;color:#1f2937;line-height:1.6;">
                            {preview_body}
                        </div>
                        <div style="background:#f9fafb;padding:12px 20px;border-top:1px solid #e5e7eb;text-align:center;">
                            <span style="font-size:11px;color:#9ca3af;">📎 {os.path.basename(file_path) if os.path.exists(file_path) else 'No attachment'}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No branches with files ready for preview.")
    
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
            recipes_dir = "recipes"
            os.makedirs(recipes_dir, exist_ok=True)
            filename = f"{save_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            config_to_save = st.session_state.campaign_config.copy()
            config_to_save['saved_name'] = save_name
            config_to_save['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            config_to_save['user_id'] = st.session_state.get("user_id", 1)
            with open(os.path.join(recipes_dir, filename), 'w') as f:
                json.dump(config_to_save, f, indent=2)
            st.success(f"Campaign '{save_name}' saved!")
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
                        user_id=st.session_state.get("user_id", 1),
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
                else:
                    execution = Execution(
                        user_id=st.session_state.get("user_id", 1),
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
                            st.balloons()
                        else:
                            status_container.update(label="❌ Campaign Failed!", state="error", expanded=True)
                            st.error(f"Error: {result.get('error', 'Unknown error')}")
                
                st.session_state.campaign_step = 1
                st.session_state.campaign_config = {}
                st.rerun()
        with c2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_execute = False
                st.rerun()

db.close()