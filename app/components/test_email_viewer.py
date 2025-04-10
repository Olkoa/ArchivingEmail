"""
Test page for the email viewer component.

Run this script directly to test the email viewer:
streamlit run test_email_viewer.py
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Add necessary paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the email viewer component
from components.email_viewer import create_email_table_with_viewer

# Set up the page
st.set_page_config(
    page_title="Email Viewer Test",
    page_icon="📧",
    layout="wide"
)

st.title("Email Viewer Test")

# Create switch for display mode
display_mode = st.selectbox(
    "Display Mode:", 
    ["MODAL", "POPOVER"], 
    index=0
)

# Set display mode in module
import components.email_viewer as email_viewer
email_viewer.EMAIL_DISPLAY_TYPE = display_mode

# Create sample data
sample_size = st.slider("Number of Sample Emails:", min_value=1, max_value=20, value=5)

# Generate sample data
data = {
    "message_id": [f"msg{i}" for i in range(sample_size)],
    "date": [pd.Timestamp(f"2023-{i%12+1:02d}-{i%28+1:02d}") for i in range(sample_size)],
    "from": [f"sender{i}@example.com" for i in range(sample_size)],
    "to": [f"recipient{i}@example.com" for i in range(sample_size)],
    "cc": ["" for _ in range(sample_size)],
    "subject": [f"Test Subject {i+1}" for i in range(sample_size)],
    "body": [f"This is the body of email {i+1}\n\nIt contains multiple lines of text.\n\nRegards,\nSender {i+1}" for i in range(sample_size)],
    "attachments": ["" if i % 3 != 0 else "file.pdf" for i in range(sample_size)],
    "has_attachments": [i % 3 == 0 for i in range(sample_size)],
    "direction": ["sent" if i % 2 == 0 else "received" for i in range(sample_size)],
    "mailbox": ["test" for _ in range(sample_size)]
}

df = pd.DataFrame(data)

# Display the table with the selected display mode
st.write(f"Using {display_mode} display mode")

create_email_table_with_viewer(df, key_prefix="test")

st.info("""
Depending on the selected display mode:
- MODAL: Either click on a row in the table or use the selector and "Voir le contenu" button
- POPOVER: Hover over a row to view the email content
""")

if __name__ == "__main__":
    print("Run this script with: streamlit run test_email_viewer.py")
