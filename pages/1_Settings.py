# pages/1_Settings.py
import streamlit as st
import pandas as pd
import os
import time
from database import SessionLocal
from models import Setting, SMTPProfile, User, UserRole
from services.audit_service import log_action

st.title("⚙️ Settings")

st.markdown("""
<div style="background:#FFF3E0;padding:10px 14px;border-radius:8px;border-left:4px solid #FF9800;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#E65100;"><strong>⚡ Quick Setup:</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
Configure at least one <b>SMTP profile</b> to start sending emails.
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
uid = st.session_state.get("user_id", 1)
role = st.session_state.get("user_role", "manager")

existing_setting = db.query(Setting).filter_by(user_id=uid).first()

# ── Success message after rerun ──
if st.session_state.get("profile_saved"):
    st.success(st.session_state["profile_saved"])
    del st.session_state["profile_saved"]

# ── Form counter for widget reset ──
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0

# ── User Management (Admin Only) ──
if role == "admin":
    st.subheader("👥 User Management")
    st.caption("Create, view, and remove users.")
    
    with st.expander("➕ Add New User"):
        new_email = st.text_input("Email", key=f"new_user_email_{st.session_state.form_counter}", placeholder="user@company.com")
        new_password = st.text_input("Password", type="password", key=f"new_user_pass_{st.session_state.form_counter}")
        new_name = st.text_input("Full Name", key=f"new_user_name_{st.session_state.form_counter}", placeholder="John Doe")
        new_role = st.selectbox("Role", ["manager", "admin"], key=f"new_user_role_{st.session_state.form_counter}")
        
        if st.button("💾 Create User", key="create_user_btn"):
            if new_email and new_password and new_name:
                existing_user = db.query(User).filter_by(email=new_email).first()
                if existing_user:
                    st.error("User with this email already exists.")
                else:
                    user_role = UserRole.ADMIN if new_role == "admin" else UserRole.MANAGER
                    new_user = User(
                        email=new_email,
                        password_hash=User.hash_password(new_password),
                        full_name=new_name,
                        role=user_role
                    )
                    db.add(new_user)
                    db.commit()
                    
                    new_setting = Setting(user_id=new_user.id)
                    db.add(new_setting)
                    db.commit()
                    
                    log_action("user_created", "user", new_user.id, new_email)
                    st.session_state.form_counter += 1
                    st.session_state.user_saved = f"User '{new_email}' created!"
                    st.rerun()
            else:
                st.error("Please fill all fields.")
    
    if st.session_state.get("user_saved"):
        st.success(st.session_state["user_saved"])
        del st.session_state["user_saved"]
    
    users = db.query(User).all()
    if users:
        user_data = []
        for u in users:
            user_data.append({
                "ID": u.id,
                "Name": u.full_name,
                "Email": u.email,
                "Role": u.role.value if u.role else "N/A",
                "Active": u.is_active or "Y",
                "Created": u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
            })
        st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
        
        st.divider()
        selected_user = st.selectbox("Select user to remove", [u.email for u in users if u.id != uid])
        
        if selected_user:
            if st.button("🗑️ Remove User", type="secondary", key="remove_user_btn"):
                st.session_state.confirm_remove_user = selected_user
            
            if st.session_state.get("confirm_remove_user") == selected_user:
                st.error(f"⚠️ Remove user '{selected_user}'? This will delete their data too.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, Remove", key="confirm_remove_yes"):
                        user_to_remove = db.query(User).filter_by(email=selected_user).first()
                        if user_to_remove:
                            log_action("user_removed", "user", user_to_remove.id, selected_user)
                            db.delete(user_to_remove)
                            db.commit()
                        st.session_state.confirm_remove_user = None
                        st.success(f"User '{selected_user}' removed.")
                        time.sleep(1)
                        st.rerun()
                with c2:
                    if st.button("❌ Cancel", key="confirm_remove_no"):
                        st.session_state.confirm_remove_user = None
                        st.rerun()
    
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
    time.sleep(1)
    st.rerun()

st.divider()

# ── SMTP Profiles ──
st.subheader("📧 SMTP Profiles")

if role == "admin":
    profiles = db.query(SMTPProfile).all()
else:
    profiles = db.query(SMTPProfile).filter_by(user_id=uid).all()

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
    profile_name = st.text_input("Profile Name", key=f"new_name_{st.session_state.form_counter}")
    smtp_server = st.text_input("SMTP Server", key=f"new_server_{st.session_state.form_counter}", placeholder="smtp.gmail.com")
    smtp_port = st.number_input("Port", value=587, key=f"new_port_{st.session_state.form_counter}")
    sender_email = st.text_input("Sender Email", key=f"new_email_{st.session_state.form_counter}")
    sender_name = st.text_input("Sender Name", key=f"new_sname_{st.session_state.form_counter}")
    password = st.text_input("Password / App Password", type="password", key=f"new_pass_{st.session_state.form_counter}")
    use_tls = st.checkbox("Use TLS", value=True, key=f"new_tls_{st.session_state.form_counter}")
    is_default = st.checkbox("Set as default", key=f"new_default_{st.session_state.form_counter}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔌 Test Connection"):
            from services.email_sender import EmailSender
            
            test_config = {
                "server": smtp_server, "port": smtp_port,
                "email": sender_email, "password": password,
                "use_tls": use_tls, "sender_name": sender_name
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
                    db.query(SMTPProfile).filter_by(user_id=uid, is_default=True).update({"is_default": False})
                
                new_profile = SMTPProfile(
                    user_id=uid,
                    profile_name=profile_name, smtp_server=smtp_server,
                    smtp_port=smtp_port, sender_email=sender_email,
                    sender_name=sender_name, password=password,
                    use_tls=use_tls, is_default=is_default
                )
                db.add(new_profile)
                db.commit()
                log_action("smtp_profile_created", "smtp_profile", new_profile.id, profile_name)
                
                st.session_state.form_counter += 1
                st.session_state.profile_saved = f"Profile '{profile_name}' saved!"
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
                    profile = db.query(SMTPProfile).filter_by(profile_name=selected_profile, user_id=uid).first()
                    if profile:
                        log_action("smtp_profile_deleted", "smtp_profile", profile.id, selected_profile)
                        db.delete(profile)
                        db.commit()
                    st.session_state.confirm_delete_profile = None
                    st.success(f"Profile '{selected_profile}' deleted.")
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", key="cancel_del"):
                    st.session_state.confirm_delete_profile = None
                    st.rerun()

db.close()