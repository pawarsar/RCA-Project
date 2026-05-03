import streamlit as st
import uuid
import pandas as pd
from database import init_db, save_final_report, SessionLocal, AgentOutput, FinalReport
from samples import INCIDENTS
from agents import run_rca_workflow
from docx import Document
from io import BytesIO
import re

def render_report_sections(content):
    # Split by major headings: "# 1.", "## 1.", or "1. Title"
    # We use a regex that looks for numbers at the start of a line or after markdown header markers
    pattern = (
        r'(?s)^---\s*\n'        # opening ---
        r'#\s+(.+?)\s*\n'       # capture TITLE text only (no #)
        r'(?:.*?\n)?'           # optional metadata lines
        r'---\s*\n?'            # closing ---
    )
    match = re.search(pattern, content)

    if match:
        title = match.group(1).strip()
        content = re.sub(pattern, '', content, count=1)
    else:
        title = None
    st.markdown(f"### {title}" if title else "### Final Root Cause Analysis (RCA) Report")

    # sections = re.split(r'\n(?=#{1,3}\s(?:\d+\.)?|^\d+\.)', content, flags=re.MULTILINE)
    sections = re.split(r'\n(?=##\s\d+\.\s.+)', content, flags=re.MULTILINE)
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        lines = section.split('\n')
        first_line = lines[0].strip()
        
        # Clean the title (remove # markers but keep the numbers)
        clean_title = re.sub(r'^#{1,3}\s*', '', first_line)
        body = '\n'.join(lines[1:]).strip()
        
        # We want everything to be in an expander if it has a body
        if body:
            with st.expander(f"**{clean_title}**", expanded=True):
                st.markdown(body)
        else:
            # If it's just a title (like the main report title), show as header
            st.markdown(f"### {clean_title}")


def create_docx(content):
    doc = Document()
    doc.add_heading('Root Cause Analysis Report', 0)
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line[0:1].isdigit() and line[1:2] == '.':
            doc.add_paragraph(line[3:], style='List Number')
        else:
            doc.add_paragraph(line)
            
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# Initialize Database
init_db()

st.set_page_config(page_title="RCA Intelligence Engine", layout="wide", page_icon="🔍")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stApp {
        background: radial-gradient(circle at top right, #1a1c24, #0e1117);
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background: linear-gradient(90deg, #2e7bcf, #1a5fb4);
        color: white;
        font-weight: 700;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(46, 123, 207, 0.4);
    }
    .report-card {
        background-color: #161b22;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #30363d;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        line-height: 1.6;
    }
    .agent-header {
        font-weight: 800;
        color: #2e7bcf;
        margin-bottom: 10px;
    }
    .status-box {
        background: rgba(46, 123, 207, 0.1);
        border-left: 4px solid #2e7bcf;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🔍 RCA Assistant")
    st.markdown("---")
    st.subheader("Sample Scenarios")
    selected_sample = st.selectbox("Select a pre-defined incident:", ["None"] + [s["title"] for s in INCIDENTS])
    
    st.markdown("---")
    st.info("This system uses a Multi-Agent architecture to perform structured Root Cause Analysis.")
    
    if st.button("Clear History"):
        st.session_state.clear()
        st.rerun()

# Main Header
st.title("🚀 RCA Intelligence Engine")
st.caption("Structured Reasoning • Multi-Agent Validation • Actionable Insights")

# Input Section
input_desc = ""
if selected_sample != "None":
    input_desc = next(s["description"] for s in INCIDENTS if s["title"] == selected_sample)

incident_input = st.text_area("Describe the incident in detail...", value=input_desc, height=150)

col_run, col_empty = st.columns([1, 4])
with col_run:
    analyze_btn = st.button("Run Intelligence Engine", type="primary")

if analyze_btn:
    if not incident_input:
        st.error("Please provide an incident description.")
    else:
        session_id = str(uuid.uuid4())
        st.session_state.session_id = session_id
        
        # UI Elements for Progress
        progress_container = st.empty()
        log_container = st.empty()
        
        agent_steps = {
            "Incident_Analyst": (0.25, "🔍 Analyst is refining the problem statement..."),
            "Root_Cause_Identifier": (0.50, "🕵️ Identifier is searching for root causes..."),
            "Mitigation_Agent": (0.75, "🛠️ Mitigator is drafting the action plan..."),
            "Validator_Agent": (1.00, "⚖️ Validator is reviewing the final report...")
        }
        
        def update_progress(agent_name):
            if agent_name in agent_steps:
                progress, text = agent_steps[agent_name]
                with progress_container.container():
                    st.markdown(f'<div class="status-box">Current Phase: <b>{agent_name.replace("_", " ")}</b></div>', unsafe_allow_html=True)
                    st.progress(progress, text=text)

        with st.spinner("Collaborating agents are working..."):
            messages = run_rca_workflow(incident_input, session_id, progress_cb=update_progress)
        
        progress_container.empty()
        st.success("✅ Root Cause Analysis Complete!")
        
        # Process messages to find the final report
        final_msg = ""
        for m in reversed(messages):
            content = m.get("content", "")
            if content and "TERMINATE" in content:
                cleaned = content.replace("TERMINATE", "").strip()
                if cleaned:
                    final_msg = cleaned
                    break
        
        if not final_msg:
            for m in reversed(messages):
                content = m.get("content", "")
                if content and "TERMINATE" not in content and m.get("name") != "User_Proxy":
                    final_msg = content
                    break
        
        if not final_msg and messages:
             final_msg = messages[-1].get("content", "")

        # Save Final Report
        save_final_report(session_id, incident_input, final_msg)
        st.session_state.final_report = final_msg
        st.session_state.messages = messages

# Results Section
if "final_report" in st.session_state:
    # st.markdown("---")
    
    # Using Tabs for cleaner UI
    tab_summary, tab_logs = st.tabs(["📋 Final Report", "🕵️ Reasoning Logs"])
    
    with tab_summary:
        with st.container():
            render_report_sections(st.session_state.final_report)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # render_report_sections(st.session_state.final_report)
        _, col_md, col_docx = st.columns([5, 1, 1])
        with col_md:
            st.download_button(
                label="Download Markdown",
                data=st.session_state.final_report,
                file_name=f"RCA_Report_{st.session_state.session_id}.md",
                mime="text/markdown"
            )
        with col_docx:
            docx_data = create_docx(st.session_state.final_report)
            st.download_button(
                label="Download Word Doc",
                data=docx_data,
                file_name=f"RCA_Report_{st.session_state.session_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    with tab_logs:
        st.subheader("Agent Collaboration History")
        for msg in st.session_state.messages:
            role = msg.get("name", "System")
            content = msg.get("content", "")
            if role != "User_Proxy" and content:
                with st.chat_message(role, avatar="🤖" if role != "User_Proxy" else "👤"):
                    st.markdown(f"**{role.replace('_', ' ')}**")
                    st.markdown(content)

# Data Explorer (Optional)
# st.markdown("---")
# if st.checkbox("Show Database Entries"):
#     db = SessionLocal()
#     # ... (code omitted for brevity but remains in your repo if uncommented)
#     db.close()
