import os
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI IT Help Desk Assistant", page_icon="💻", layout="wide")

st.title("AI IT Help Desk Assistant")
st.write("Demo project for authentication-related help desk workflows.")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("Please set your OPENAI_API_KEY in the terminal.")
    st.stop()

client = OpenAI(api_key=api_key)

try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()
except FileNotFoundError:
    st.error("prompt.txt not found. Make sure it exists.")
    st.stop()


def parse_sections(text: str) -> dict:
    headers = [
        "Alert Message (for IT team)",
        "User Notification Message",
        "Issue Summary",
        "Likely Causes",
        "Troubleshooting Steps",
        "Verification Questions",
        "Priority Level",
        "Recommended Next Action",
        "Escalation Decision",
    ]

    sections = {header: "" for header in headers}
    current_header = None

    for line in text.splitlines():
        stripped = line.strip()

        matched_header = None
        for header in headers:
            if stripped.startswith(f"**{header}:**") or stripped.startswith(f"{header}:"):
                matched_header = header
                break

        if matched_header:
            current_header = matched_header
            cleaned = stripped
            cleaned = cleaned.replace(f"**{matched_header}:**", "").replace(f"{matched_header}:", "").strip()
            if cleaned:
                sections[current_header] += cleaned + "\n"
        elif current_header:
            sections[current_header] += line + "\n"

    return {k: v.strip() for k, v in sections.items()}


st.subheader("Enter Issue Details")

col1, col2 = st.columns(2)

with col1:
    issue_type = st.selectbox(
        "Issue Type",
        ["Account Lockout", "Password Reset", "Failed Login Attempts"]
    )

with col2:
    employee_status = st.selectbox(
        "Employee Status",
        ["Active Employee", "Former Employee", "Unknown"]
    )

username = st.text_input("Username or User ID", placeholder="jon.doe")

description = st.text_area(
    "Describe the issue",
    placeholder="Example: User reports they were locked out after multiple failed login attempts while working remotely and need access restored urgently.",
    height=140
)

if st.button("Analyze Issue", use_container_width=False):
    if not description.strip():
        st.error("Please enter a description.")
        st.stop()

    user_input = f"""
Issue Type: {issue_type}
Employee Status: {employee_status}
Username: {username if username else "Not provided"}
Issue Description: {description}

Respond using this format:
- Alert Message (for IT team)
- User Notification Message
- Issue Summary
- Likely Causes
- Troubleshooting Steps
- Verification Questions
- Priority Level
- Recommended Next Action
- Escalation Decision
"""

    with st.spinner("Analyzing issue..."):
        try:
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
            )

            output = response.output_text
            sections = parse_sections(output)

            st.divider()
            st.subheader("Analysis Results")

            priority_text = sections.get("Priority Level", "")
            if "high" in priority_text.lower():
                st.error(f"Priority Level: {priority_text}")
            elif "medium" in priority_text.lower():
                st.warning(f"Priority Level: {priority_text}")
            elif priority_text:
                st.success(f"Priority Level: {priority_text}")

            if sections.get("Alert Message (for IT team)"):
                with st.expander("Alert Message (for IT team)", expanded=True):
                    st.write(sections["Alert Message (for IT team)"])

            if sections.get("User Notification Message"):
                with st.expander("User Notification Message", expanded=True):
                    st.write(sections["User Notification Message"])

            left, right = st.columns(2)

            with left:
                if sections.get("Issue Summary"):
                    st.markdown("### Issue Summary")
                    st.write(sections["Issue Summary"])

                if sections.get("Likely Causes"):
                    st.markdown("### Likely Causes")
                    st.write(sections["Likely Causes"])

                if sections.get("Verification Questions"):
                    st.markdown("### Verification Questions")
                    st.write(sections["Verification Questions"])

            with right:
                if sections.get("Troubleshooting Steps"):
                    st.markdown("### Troubleshooting Steps")
                    st.write(sections["Troubleshooting Steps"])

                if sections.get("Recommended Next Action"):
                    st.markdown("### Recommended Next Action")
                    st.write(sections["Recommended Next Action"])

                if sections.get("Escalation Decision"):
                    st.markdown("### Escalation Decision")
                    st.write(sections["Escalation Decision"])

            with st.expander("Raw AI Response"):
                st.text(output)

        except Exception as e:
            st.error(f"Error: {e}")
