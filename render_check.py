import re
import streamlit as st

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



st.set_page_config(page_title="RCA Intelligence Engine", layout="wide", page_icon="🔍")

# Read a txt file
file = open("resign.txt", encoding="utf8")
# file = open("finance.txt", encoding="utf8")
content = file.read()
file.close()
render_report_sections(content)
st.markdown("### End of Report")