import streamlit as st
from database import SessionLocal, FinalReport, User, AgentOutput, SystemPrompt
import pandas as pd
import json
import re
import streamlit.components.v1 as components
import base64
import requests

# Set page config for a premium look
st.set_page_config(page_title="RCA Data Inspector", layout="wide", page_icon="🔍")

# Premium CSS for high-end feel
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .main { background-color: #0e1117; color: #fafafa; font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1a1c24, #0e1117); }
    
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.2em;
        background: linear-gradient(135deg, #2e7bcf 0%, #1a5fb4 100%);
        color: white; font-weight: 700; border: none; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase; letter-spacing: 1px;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(46, 123, 207, 0.4); }
    
    .inspector-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        margin-top: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .field-label { color: #8892b0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.2rem; }
    .field-value { color: #e6edf3; font-size: 1.1rem; margin-bottom: 1rem; }
    .highlight { color: #2e7bcf; font-weight: 800; }
    
    h1, h2, h3 { color: #ffffff !important; font-weight: 800 !important; }
    
    .json-container {
        background: #0d1117;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #30363d;
        font-family: 'Fira Code', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

def render_mermaid(content):
    # Extract Mermaid diagram if exists
    mermaid_pattern = r"```mermaid\n(.*?)\n```"
    mermaid_match = re.search(mermaid_pattern, content, re.DOTALL)
    
    if mermaid_match:
        mermaid_code = mermaid_match.group(1).strip()
        st.subheader("📊 Root Cause Visualizer")
        
        try:
            # Encode mermaid code for mermaid.ink
            encoded_mermaid = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
            image_url = f"https://mermaid.ink/img/{encoded_mermaid}"
            
            # Display image
            st.image(image_url, caption="Root Cause Flow Diagram", use_container_width=True)
            
            # Download button
            img_resp = requests.get(image_url)
            if img_resp.status_code == 200:
                st.download_button(
                    label="📥 Download Flow Diagram (PNG)",
                    data=img_resp.content,
                    file_name="rca_flow_diagram.png",
                    mime="image/png",
                    key=f"dl_{base64.b64encode(mermaid_code[:20].encode()).decode()}" # Unique key
                )
        except Exception as e:
            st.error(f"Error generating diagram image: {str(e)}")
            with st.expander("View Mermaid Code"):
                st.code(mermaid_code)
        
        # Strip mermaid from text AND any headings that mention Mermaid
        content = re.sub(mermaid_pattern, "", content, flags=re.DOTALL)
        content = re.sub(r'#+\s*\d*\.*\s*.*[Mm]ermaid.*?\n', "", content) 
    
    return content

def get_record_by_id(table_class, record_id):
    db = SessionLocal()
    try:
        return db.query(table_class).filter(table_class.id == record_id).first()
    except Exception as e:
        st.error(f"Database Query Error: {str(e)}")
        return None
    finally:
        db.close()

def main():
    st.title("🔍 Database Record Inspector")
    st.markdown("Fetch and display specific rows from the RCA Intelligence Engine database.")

    # Input Section
    with st.container():
        col_table, col_id, col_btn = st.columns([2, 1, 1])
        
        with col_table:
            table_name = st.selectbox("Select Table", ["FinalReport", "AgentOutput", "User", "SystemPrompt"])
            table_map = {
                "FinalReport": FinalReport,
                "AgentOutput": AgentOutput,
                "User": User,
                "SystemPrompt": SystemPrompt
            }
        
        with col_id:
            record_id = st.number_input("Enter ID", min_value=1, step=1, value=1)
            
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            fetch_triggered = st.button("Fetch Record", type="primary")

    # Fetch on start or on button click
    if fetch_triggered or 'record_data' not in st.session_state or st.session_state.get('last_id') != record_id or st.session_state.get('last_table') != table_name:
        with st.spinner("Accessing vault..."):
            record = get_record_by_id(table_map[table_name], record_id)
            st.session_state.last_id = record_id
            st.session_state.last_table = table_name
            
            if record:
                # Create a dictionary of the record attributes
                record_data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
                st.session_state.record_data = record_data
                st.session_state.record_found = True
            else:
                st.session_state.record_found = False
                st.session_state.record_data = None

    if st.session_state.get('record_found'):
        record_data = st.session_state.record_data
        # We need the original record object for some table specific logic if we want to keep it simple
        # but record_data (dict) is safer for session state.
        
        st.success(f"Displaying record from **{table_name}** with ID: **{record_id}**")
        
        # Display Layout
        tab_pretty, tab_raw = st.tabs(["✨ Formatted View", "💻 JSON Raw"])
        
        with tab_pretty:
            st.markdown('<div class="inspector-card">', unsafe_allow_html=True)
            
            if table_name == "FinalReport":
                st.subheader(f"📊 Report Summary")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f'<div class="field-label">Incident Description</div><div class="field-value">{record_data.get("incident_description", "")[:200]}...</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="field-label">Timestamp</div><div class="field-value">{record_data.get("timestamp")}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="field-label">Total Tokens</div><div class="field-value highlight">{record_data.get("total_tokens")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="field-label">Rating</div><div class="field-value">{"⭐" * (record_data.get("rating") or 0)}</div>', unsafe_allow_html=True)
                
                st.markdown('<hr style="opacity:0.1">', unsafe_allow_html=True)
                
                # Render Mermaid if exists and get cleaned content
                content = record_data.get("final_report", "")
                print(content)
                cleaned_content = render_mermaid(content)
                
                st.markdown('<div class="field-label">Final Report Content</div>', unsafe_allow_html=True)
                st.markdown(cleaned_content)
                
            elif table_name == "User":
                st.subheader(f"👤 User Profile")
                st.markdown(f'<div class="field-label">Username</div><div class="field-value highlight">{record_data.get("username")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="field-label">Email</div><div class="field-value">{record_data.get("email")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="field-label">Created At</div><div class="field-value">{record_data.get("created_at")}</div>', unsafe_allow_html=True)
                
            else:
                # Generic display for other tables
                for key, value in record_data.items():
                    st.markdown(f'<div class="field-label">{key.replace("_", " ")}</div><div class="field-value">{value}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab_raw:
            # Convert datetimes to strings for JSON display
            json_display = {}
            for k, v in record_data.items():
                if hasattr(v, 'isoformat'):
                    json_display[k] = v.isoformat()
                else:
                    json_display[k] = v
            st.json(json_display)
            
    elif st.session_state.get('record_found') == False:
        st.warning(f"No record found in **{table_name}** with ID: {record_id}")

if __name__ == "__main__":
    main()
