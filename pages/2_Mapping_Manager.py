# pages/2_Mapping_Manager.py
import streamlit as st
import pandas as pd
import os
from database import SessionLocal
from models import Mapping, MappingEntry
from services.audit_service import log_action

UPLOAD_DIR = "uploads/mappings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("🗺️ Mapping Manager")

st.markdown("""
<div style="background:#E8F5E9;padding:10px 14px;border-radius:8px;border-left:4px solid #4CAF50;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#2E7D32;"><strong>💡 What is a Mapping?</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
A mapping file links <b>branch names</b> to <b>email addresses</b>. The system uses it to know which file goes to which recipient.<br>
Download the sample CSV, fill in your branches, and upload it.
</p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()

tab1, tab2 = st.tabs(["📤 Upload New Mapping", "📋 Saved Mappings"])

with tab1:
    st.subheader("Upload Mapping CSV")
    st.caption("CSV must have columns: BranchName, To, CC")
    
    sample_csv = (
        "BranchName,To,CC\n"
        "Mumbai,mumbai.manager@company.com;mumbai.assistant@company.com,regional.head@company.com\n"
        "Delhi,delhi.manager@company.com,regional.head@company.com;director@company.com\n"
        "Bangalore,bangalore.manager@company.com,\n"
    )
    
    st.download_button(
        label="📥 Download Sample CSV",
        data=sample_csv,
        file_name="sample_mapping.csv",
        mime="text/csv"
    )
    
    st.caption("💡 Use **semicolon (;)** to separate multiple recipients in To or CC fields.")
    
    mapping_name = st.text_input("Mapping Name", placeholder="e.g. Branch Mapping Q1 2026")
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("**Preview:**")
        st.dataframe(df, use_container_width=True)
        
        required_cols = ["BranchName", "To", "CC"]
        if all(col in df.columns for col in required_cols):
            if st.button("💾 Save Mapping", type="primary"):
                file_path = os.path.join(UPLOAD_DIR, f"{mapping_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
                df.to_csv(file_path, index=False)
                
                mapping = Mapping(
                    user_id=1,
                    mapping_name=mapping_name,
                    file_path=file_path
                )
                db.add(mapping)
                db.flush()
                
                for _, row in df.iterrows():
                    entry = MappingEntry(
                        mapping_id=mapping.id,
                        branch_name=str(row["BranchName"]),
                        to_recipients=str(row["To"]),
                        cc_recipients=str(row["CC"])
                    )
                    db.add(entry)
                
                db.commit()
                log_action("mapping_created", "mapping", mapping.id, mapping_name)
                st.success(f"Mapping '{mapping_name}' saved with {len(df)} branches.")
                st.rerun()
        else:
            st.error(f"CSV must contain columns: {', '.join(required_cols)}")

with tab2:
    st.subheader("Saved Mappings")
    
    mappings = db.query(Mapping).all()
    
    if mappings:
        mapping_list = []
        for m in mappings:
            entry_count = db.query(MappingEntry).filter_by(mapping_id=m.id).count()
            mapping_list.append({
                "ID": m.id,
                "Name": m.mapping_name,
                "Branches": entry_count,
                "Created": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else ""
            })
        
        mapping_df = pd.DataFrame(mapping_list)
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)
        
        st.divider()
        selected_mapping = st.selectbox("Select mapping to view or delete", [m.mapping_name for m in mappings])
        
        if selected_mapping:
            mapping = db.query(Mapping).filter_by(mapping_name=selected_mapping).first()
            entries = db.query(MappingEntry).filter_by(mapping_id=mapping.id).all()
            
            if entries:
                entry_data = []
                for e in entries:
                    entry_data.append({
                        "Branch Name": e.branch_name,
                        "To": e.to_recipients,
                        "CC": e.cc_recipients
                    })
                st.dataframe(pd.DataFrame(entry_data), use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete Mapping", type="secondary"):
                    st.session_state.confirm_delete_mapping = selected_mapping
            
            if st.session_state.get("confirm_delete_mapping") == selected_mapping:
                st.error(f"⚠️ Delete mapping '{selected_mapping}'? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, Delete", key="confirm_del_map"):
                        log_action("mapping_deleted", "mapping", mapping.id, selected_mapping)
                        db.delete(mapping)
                        db.commit()
                        st.session_state.confirm_delete_mapping = None
                        st.success(f"Mapping '{selected_mapping}' deleted.")
                        st.rerun()
                with c2:
                    if st.button("❌ Cancel", key="cancel_del_map"):
                        st.session_state.confirm_delete_mapping = None
                        st.rerun()
    else:
        st.info("No saved mappings yet. Upload one from the 'Upload New Mapping' tab.")

db.close()