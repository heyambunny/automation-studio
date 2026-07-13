# pages/1_Settings.py
import streamlit as st
import pandas as pd
import os
from config import IS_WINDOWS
from database import SessionLocal
from models import Setting, SMTPProfile
from services.audit_service import log_action

st.title("⚙️ Settings")

st.markdown("""
<div style="background:#FFF3E0;padding:10px 14px;border-radius:8px;border-left:4px solid #FF9800;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#E65100;"><strong>⚡ Quick Setup Guide:</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
1️⃣ Set your <b>reports folder</b> where all branch Excel files are stored<br>
2️⃣ Configure at least one <b>SMTP profile</b> to send emails<br>
3️⃣ Set default <b>sheet name</b> and <b>starting cell</b> for summary data
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

# ── Folder Path ──
st.subheader("📁 Default Reports Folder")

existing_setting = db.query(Setting).first()
current_folder = existing_setting.folder_path if existing_setting else ""

if current_folder and os.path.exists(current_folder):
    st.success(f"📁 **{current_folder}**")
    files = [f for f in os.listdir(current_folder) if f.endswith(('.xlsx', '.csv'))]
    if files:
        st.caption(f"📂 {len(files)} files found")
    else:
        st.warning("No Excel/CSV files in this folder.")
elif current_folder:
    st.error(f"❌ Folder not found: {current_folder}")

st.caption("---")
uploaded = st.file_uploader(
    "📤 Upload any file from your reports folder to help locate it",
    type=["xlsx", "csv"],
    key="settings_folder_picker",
    help="Pick any Excel/CSV file from the folder where all branch reports are stored."
)

if uploaded:
    st.info(f"📄 File selected: **{uploaded.name}**")
    st.caption("Now enter the folder path where this file is located:")

folder_path = st.text_input(
    "Folder path",
    value=current_folder,
    placeholder="e.g. /Users/username/Reports or C:\\Reports",
    help="💡 Tip: Drag your folder into Terminal to copy the path, then paste here."
)

if folder_path:
    if os.path.exists(folder_path):
        st.success("✅ Folder exists")
        files = [f for f in os.listdir(folder_path) if f.endswith(('.xlsx', '.csv'))]
        if files:
            st.caption(f"📂 {len(files)} Excel/CSV files found: {', '.join(files[:5])}{'...' if len(files) > 5 else ''}")
    else:
        st.error("❌ Folder not found")

if st.button("💾 Save Folder Path"):
    if folder_path and os.path.exists(folder_path):
        if existing_setting:
            existing_setting.folder_path = folder_path
        else:
            new_setting = Setting(user_id=1, folder_path=folder_path)
            db.add(new_setting)
        db.commit()
        log_action("folder_path_updated", "setting", existing_setting.id if existing_setting else None, folder_path)
        st.success("✅ Folder path saved!")
        st.rerun()
    elif folder_path:
        st.error("Folder does not exist. Check the path.")

st.divider()

# ── Logo ──
st.subheader("🖼️ App Logo")

LOGO_DIR = "assets"
os.makedirs(LOGO_DIR, exist_ok=True)
LOGO_PATH = os.path.join(LOGO_DIR, "logo.png")

if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=120)

uploaded_logo = st.file_uploader("Upload logo (PNG recommended)", type=["png", "jpg", "jpeg"], key="logo_upload")

if uploaded_logo:
    with open(LOGO_PATH, "wb") as f:
        f.write(uploaded_logo.getbuffer())
    st.success("Logo updated!")
    st.rerun()

st.divider()

# ── Default Sheet Settings ──
st.subheader("📊 Default Sheet Settings")

current_sheet = existing_setting.default_sheet_name if existing_setting else ""
current_cell = existing_setting.default_starting_cell if existing_setting else ""

default_sheet = st.text_input("Default Summary Sheet Name", value=current_sheet, placeholder="e.g. Summary")
default_cell = st.text_input("Default Starting Cell", value=current_cell, placeholder="e.g. B5")

if st.button("💾 Save Sheet Settings"):
    if existing_setting:
        existing_setting.default_sheet_name = default_sheet
        existing_setting.default_starting_cell = default_cell
    else:
        new_setting = Setting(
            user_id=1,
            default_sheet_name=default_sheet,
            default_starting_cell=default_cell
        )
        db.add(new_setting)
    db.commit()
    log_action("sheet_settings_updated", "setting", existing_setting.id if existing_setting else None)
    st.success("Sheet settings saved.")
    st.rerun()

st.divider()

# ── Outlook Integration ──
st.subheader("📨 Outlook Integration")

if IS_WINDOWS:
    outlook_enabled = existing_setting.outlook_enabled if existing_setting else False
    new_outlook = st.toggle("Enable Outlook Integration", value=outlook_enabled)
    
    if new_outlook != outlook_enabled:
        if existing_setting:
            existing_setting.outlook_enabled = new_outlook
        else:
            new_setting = Setting(user_id=1, outlook_enabled=new_outlook)
            db.add(new_setting)
        db.commit()
        if new_outlook:
            st.success("Outlook integration enabled.")
        else:
            st.info("Outlook integration disabled.")
        st.rerun()
else:
    st.warning("Outlook integration is only available on Windows.")

st.divider()

# ── SMTP Profiles ──
st.subheader("📧 SMTP Profiles")

profiles = db.query(SMTPProfile).all()

if profiles:
    profile_data = []
    for p in profiles:
        profile_data.append({
            "ID": p.id,
            "Name": p.profile_name,
            "Server": p.smtp_server,
            "Port": p.smtp_port,
            "Sender": p.sender_email,
            "TLS": p.use_tls,
            "Default": "⭐" if p.is_default else ""
        })
    st.dataframe(pd.DataFrame(profile_data), use_container_width=True, hide_index=True)
else:
    st.info("No SMTP profiles saved yet.")

with st.expander("➕ Add New SMTP Profile"):
    profile_name = st.text_input("Profile Name", key="new_name")
    smtp_server = st.text_input("SMTP Server", key="new_server", placeholder="smtp.gmail.com")
    smtp_port = st.number_input("Port", value=587, key="new_port")
    sender_email = st.text_input("Sender Email", key="new_email")
    sender_name = st.text_input("Sender Name", key="new_sname")
    password = st.text_input("Password / App Password", type="password", key="new_pass")
    use_tls = st.checkbox("Use TLS", value=True, key="new_tls")
    is_default = st.checkbox("Set as default", key="new_default")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔌 Test Connection"):
            from services.email_sender import EmailSender
            
            test_config = {
                "server": smtp_server,
                "port": smtp_port,
                "email": sender_email,
                "password": password,
                "use_tls": use_tls,
                "sender_name": sender_name
            }
            
            tester = EmailSender(test_config)
            result = tester.test_connection()
            
            if result["success"]:
                st.success(result["message"])
                log_action("smtp_test_success", "smtp_profile", None, smtp_server)
            else:
                st.error(f"Connection failed: {result['message']}")
                log_action("smtp_test_failed", "smtp_profile", None, f"{smtp_server}: {result['message']}")
    with col2:
        if st.button("💾 Save Profile"):
            if profile_name and smtp_server and sender_email and password:
                if is_default:
                    db.query(SMTPProfile).filter(SMTPProfile.is_default == True).update({"is_default": False})
                
                new_profile = SMTPProfile(
                    user_id=1,
                    profile_name=profile_name,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    sender_email=sender_email,
                    sender_name=sender_name,
                    password=password,
                    use_tls=use_tls,
                    is_default=is_default
                )
                db.add(new_profile)
                db.commit()
                log_action("smtp_profile_created", "smtp_profile", new_profile.id, profile_name)
                st.success(f"Profile '{profile_name}' saved.")
                st.rerun()
            else:
                st.error("Please fill all required fields.")

if profiles:
    st.subheader("🗑️ Manage Profiles")
    selected_profile = st.selectbox("Select profile to delete", [p.profile_name for p in profiles])
    
    if selected_profile:
        if st.button("🗑️ Delete Profile", type="secondary"):
            st.session_state.confirm_delete_profile = selected_profile
        
        if st.session_state.get("confirm_delete_profile") == selected_profile:
            st.error(f"⚠️ Delete profile '{selected_profile}'?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Delete", key="confirm_del"):
                    profile = db.query(SMTPProfile).filter_by(profile_name=selected_profile).first()
                    log_action("smtp_profile_deleted", "smtp_profile", profile.id, selected_profile)
                    db.delete(profile)
                    db.commit()
                    st.session_state.confirm_delete_profile = None
                    st.success(f"Profile '{selected_profile}' deleted.")
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", key="cancel_del"):
                    st.session_state.confirm_delete_profile = None
                    st.rerun()

db.close()