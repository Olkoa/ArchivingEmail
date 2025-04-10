import streamlit as st
from streamlit_modal import Modal
import pandas as pd

# Set page title
st.title("Email Table with Modal Viewer")

# Sample email data
emails = [
    {
        "from": "john.doe@example.com",
        "to": "jane.smith@example.com",
        "subject": "Project Update - Q1 Report",
        "content": """
Dear Jane,

I'm writing to provide you with the Q1 project update as requested. We've made significant progress on the core deliverables:

1. Database migration completed ahead of schedule
2. User authentication system upgraded to include 2FA
3. Front-end redesign at 75% completion

The team has been working efficiently despite the tight timeline. We anticipate completing all remaining tasks before the end of the month.

Let me know if you need any clarification or have questions about any aspect of the project.

Best regards,
John Doe
        """
    },
    {
        "from": "marketing@company.com",
        "to": "all-staff@company.com",
        "subject": "Upcoming Company Event - Save the Date",
        "content": """
Hello Everyone,

We're excited to announce our annual company retreat will take place on June 15-17 at Mountain View Resort.

This year's theme is "Innovation and Collaboration." The agenda includes:

- Keynote from CEO Sarah Johnson
- Team-building workshops
- Product roadmap presentations
- Evening social events

Please confirm your attendance by May 10th through the HR portal. Transportation and accommodation details will follow in a separate email.

We look forward to seeing you all there!

Regards,
The Marketing Team
        """
    }
]

# Convert to DataFrame for easier handling
df = pd.DataFrame(emails)

# Initialize session state for tracking which email is selected
if 'selected_email' not in st.session_state:
    st.session_state.selected_email = None

# Function to handle row clicks and open modal
def open_email(index):
    st.session_state.selected_email = index

# Create a clean table display
st.write("### Emails")

# Add custom CSS for better styling
st.markdown("""
<style>
    /* Table styling */
    .email-table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 1rem;
    }
    .email-table th {
        background-color: #1E88E5;
        color: white;
        padding: 12px 15px;
        text-align: left;
        font-weight: bold;
    }
    .email-table td, .email-table th {
        border: 1px solid #ddd;
        padding: 8px 12px;
    }
    .email-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .email-table tr:hover {
        background-color: #ddd;
        cursor: pointer;
    }
    
    /* Email content styling */
    .email-content {
        white-space: pre-line;
        font-family: Arial, sans-serif;
        line-height: 1.5;
    }
    
    /* Header details styling */
    .email-header {
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    .email-label {
        font-weight: bold;
        color: #555;
        width: 70px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Create a table header
cols = st.columns([3, 3, 6])
with cols[0]:
    st.write("**From**")
with cols[1]:
    st.write("**To**")
with cols[2]:
    st.write("**Subject**")

# Display each email as a row
for i, email in enumerate(emails):
    # Create a clickable row
    row = st.container()
    row.markdown(f"""
    <div class="email-table-row" onclick="document.getElementById('email-row-{i}').click()">
    </div>
    """, unsafe_allow_html=True)
    
    # Use columns for the table structure
    cols = row.columns([3, 3, 6])
    with cols[0]:
        st.write(email["from"])
    with cols[1]:
        st.write(email["to"])
    with cols[2]:
        # Hidden button to trigger the click event
        if st.button(email["subject"], key=f"email-row-{i}", help="Click to view this email"):
            open_email(i)

# Display modal with email content when an email is selected
if st.session_state.selected_email is not None:
    index = st.session_state.selected_email
    email = emails[index]
    
    # Create the modal
    modal = Modal(
        title=email["subject"],
        key=f"email_modal_{index}"
    )
    
    # Add content to the modal
    with modal.container():
        # Email header details
        st.markdown('<div class="email-header">', unsafe_allow_html=True)
        st.markdown(f'<span class="email-label">From:</span> {email["from"]}', unsafe_allow_html=True)
        st.markdown(f'<span class="email-label">To:</span> {email["to"]}', unsafe_allow_html=True)
        st.markdown(f'<span class="email-label">Subject:</span> {email["subject"]}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Email content
        st.markdown(f'<div class="email-content">{email["content"]}</div>', unsafe_allow_html=True)
        
        # Close button
        if st.button("Close", key=f"close_modal_{index}"):
            st.session_state.selected_email = None
            st.rerun()

# Handle modal X button closing
if 'modal_open' not in st.session_state:
    st.session_state.modal_open = False

# Set modal as open when displaying
if st.session_state.selected_email is not None:
    st.session_state.modal_open = True

# Check if modal was closed with X button
if st.session_state.modal_open and st.session_state.selected_email is not None and 'modal' not in locals():
    st.session_state.selected_email = None
    st.session_state.modal_open = False
    st.rerun()
