# pages/3_Campaign_Manager.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from services.audit_service import log_action

RECIPES_DIR = "recipes"
os.makedirs(RECIPES_DIR, exist_ok=True)

st.title("📋 Campaign Manager")

st.markdown("""
<div style="background:#E3F2FD;padding:10px 14px;border-radius:8px;border-left:4px solid #2196F3;margin-bottom:15px;">
<p style="margin:0;font-size:13px;color:#1565C0;"><strong>💡 What are Saved Campaigns?</strong></p>
<p style="margin:3px 0 0 0;font-size:12px;color:#555;">
Save your campaign setup (mapping, folder, mode, templates) as a reusable recipe.<br>
Next time, just load it and execute — no need to configure everything again.
</p>
</div>
""", unsafe_allow_html=True)

def load_campaigns():
    campaigns = []
    if os.path.exists(RECIPES_DIR):
        for f in os.listdir(RECIPES_DIR):
            if f.endswith('.json'):
                with open(os.path.join(RECIPES_DIR, f), 'r') as file:
                    data = json.load(file)
                    data['filename'] = f
                    campaigns.append(data)
    return campaigns

def save_campaign(name, config):
    filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    config['saved_name'] = name
    config['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(os.path.join(RECIPES_DIR, filename), 'w') as f:
        json.dump(config, f, indent=2)
    return filename

def delete_campaign(filename):
    os.remove(os.path.join(RECIPES_DIR, filename))

campaigns = load_campaigns()

tab1, tab2 = st.tabs(["📂 Saved Campaigns", "💾 Save Current Campaign"])

with tab1:
    if campaigns:
        campaign_data = []
        for c in campaigns:
            campaign_data.append({
                "Name": c.get('saved_name', 'Unnamed'),
                "Mode": c.get('mode', ''),
                "Saved At": c.get('saved_at', ''),
                "File": c.get('filename', '')
            })
        
        df = pd.DataFrame(campaign_data)
        st.dataframe(df[["Name", "Mode", "Saved At"]], use_container_width=True, hide_index=True)
        
        st.divider()
        selected_name = st.selectbox("Select campaign", [c['saved_name'] for c in campaigns])
        
        if selected_name:
            campaign = next(c for c in campaigns if c['saved_name'] == selected_name)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Details**")
                st.write(f"Mode: {campaign.get('mode', 'N/A')}")
                st.write(f"Send Method: {campaign.get('send_method', 'N/A')}")
                st.write(f"Folder: {campaign.get('campaign_folder', campaign.get('folder_path', 'Default'))}")
            
            with col2:
                st.write("**Mapping**")
                mapping_id = campaign.get('mapping_id')
                st.write(f"Mapping ID: {mapping_id if mapping_id else 'Uploaded on run'}")
            
            with col3:
                st.write("**Variables**")
                vars_data = campaign.get('variables', {})
                st.write(f"Report Type: {vars_data.get('ReportType', 'N/A')}")
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🚀 Execute Now", type="primary", use_container_width=True):
                    st.session_state.confirm_execute = selected_name
            with c2:
                if st.button("✏️ Edit", use_container_width=True):
                    st.session_state.campaign_config = campaign
                    st.session_state.campaign_step = 1
                    st.switch_page("pages/4_New_Campaign.py")
            with c3:
                if st.button("🗑️ Delete", use_container_width=True):
                    st.session_state.confirm_delete = selected_name
            
            # Confirm Execute
            if st.session_state.get("confirm_execute") == selected_name:
                st.warning(f"⚠️ Execute '{selected_name}'? This will send all emails.")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Yes, Execute", type="primary", key="exec_yes"):
                        log_action("campaign_executed_from_manager", "campaign_recipe", None, selected_name)
                        st.session_state.campaign_config = campaign
                        st.session_state.campaign_step = 5
                        st.session_state.confirm_execute = None
                        st.switch_page("pages/4_New_Campaign.py")
                with col_b:
                    if st.button("❌ Cancel", key="exec_no"):
                        st.session_state.confirm_execute = None
                        st.rerun()
            
            # Confirm Delete
            if st.session_state.get("confirm_delete") == selected_name:
                st.error(f"⚠️ Delete '{selected_name}'? This cannot be undone.")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Yes, Delete", type="primary", key="del_yes"):
                        log_action("campaign_deleted", "campaign_recipe", None, selected_name)
                        delete_campaign(campaign['filename'])
                        st.session_state.confirm_delete = None
                        st.success(f"Deleted '{selected_name}'")
                        st.rerun()
                with col_b:
                    if st.button("❌ Cancel", key="del_no"):
                        st.session_state.confirm_delete = None
                        st.rerun()
    else:
        st.info("""
        No saved campaigns yet.
        
        **How to save:**
        1. Go to 🚀 **New Campaign**
        2. Complete all steps
        3. In Step 5, enter a name and click **Save Campaign**
        4. Come back here to view, edit, execute, or delete
        """)

with tab2:
    st.subheader("Save Campaign Configuration")
    st.caption("Save the current campaign setup for future use.")
    
    campaign_name = st.text_input("Campaign Name", placeholder="e.g. Monthly MS Scheme Report")
    
    if st.button("💾 Save Campaign", type="primary"):
        config = st.session_state.get("campaign_config", {})
        if config and campaign_name:
            filename = save_campaign(campaign_name, config)
            log_action("campaign_saved", "campaign_recipe", None, campaign_name)
            st.success(f"Campaign '{campaign_name}' saved!")
            st.rerun()
        elif not campaign_name:
            st.error("Please enter a campaign name.")
        else:
            st.warning("No campaign configuration found. Create a campaign first in 'New Campaign'.")