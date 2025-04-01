"""
Email viewer component for the Okloa project.

This module provides functions for displaying email content in different formats.
"""

import streamlit as st
import pandas as pd
from typing import Callable, Dict, Any, List, Optional
import os
import sys
import json

# Add the project root to the path so we can import constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Try to import constants, with a fallback for testing
try:
    from constants import EMAIL_DISPLAY_TYPE
except ImportError:
    # Default for testing
    EMAIL_DISPLAY_TYPE = "MODAL"

# CSS for the email popover and modal
EMAIL_POPOVER_CSS = """
<style>
.email-row {
    cursor: pointer;
}
.email-popover {
    display: none;
    position: absolute;
    z-index: 100;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 20px;
    max-width: 80%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.email-row:hover .email-popover {
    display: block;
}
.email-header {
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}
.email-content {
    white-space: pre-wrap;
    font-family: monospace;
    background-color: #f9f9f9;
    padding: 10px;
    border-radius: 5px;
}

/* Style for the email modal */
.email-modal {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 20px;
    margin-bottom: 20px;
    background-color: white;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    position: fixed;
    top: 5%;
    left: 10%;
    width: 80%;
    height: 90%;
    z-index: 1000;
    overflow-y: auto;
}

.overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 999;
}

/* Better styling for standard Streamlit tables */
div[data-testid="stTable"] table {
    width: 100%;
}
div[data-testid="stTable"] th {
    background-color: #f0f0f0;
    font-weight: bold;
}
div[data-testid="stTable"] tr:hover {
    background-color: #f0f8ff;
}
</style>
"""

def format_email_date(date_obj):
    """Format a datetime object for display."""
    if pd.isna(date_obj):
        return ""
    return date_obj.strftime('%Y-%m-%d %H:%M')

def create_email_table_with_viewer(
    emails_df: pd.DataFrame,
    key_prefix: str = "email_table"
) -> None:
    """
    Create an interactive email table with content viewer.
    
    Args:
        emails_df: DataFrame containing email data
        key_prefix: Prefix for Streamlit keys to avoid conflicts
        
    Returns:
        None
    """
    if emails_df.empty:
        st.info("Aucun email à afficher.")
        return
    
    # Create a copy with limited columns for display
    display_df = emails_df[['date', 'from', 'to', 'subject']].copy()
    
    # Format date for display
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].apply(format_email_date)
    
    if EMAIL_DISPLAY_TYPE == "POPOVER":
        _create_popover_email_table(emails_df, display_df, key_prefix)
    else:  # Default to MODAL
        _create_simple_modal_email_table(emails_df, display_df, key_prefix)

def _create_popover_email_table(
    emails_df: pd.DataFrame,
    display_df: pd.DataFrame,
    key_prefix: str
) -> None:
    """Create an email table with popover display on hover."""
    # Inject CSS for popover
    st.markdown(EMAIL_POPOVER_CSS, unsafe_allow_html=True)
    
    # Generate HTML for table with popovers
    html_rows = []
    for idx, row in display_df.iterrows():
        email_data = emails_df.iloc[idx]
        
        # Format email data for popover
        popover_content = f"""
        <div class="email-header">
            <p><strong>De:</strong> {email_data['from']}</p>
            <p><strong>À:</strong> {email_data['to']}</p>
            <p><strong>Date:</strong> {format_email_date(email_data['date'])}</p>
            <p><strong>Sujet:</strong> {email_data['subject']}</p>
            {f"<p><strong>Pièces jointes:</strong> {email_data['attachments']}</p>" if email_data.get('has_attachments') else ""}
        </div>
        <div class="email-content">{email_data['body']}</div>
        """
        
        # Create row with popover
        html_row = f"""
        <tr class="email-row">
            <td>{row['date']}</td>
            <td>{row['from']}</td>
            <td>{row['to']}</td>
            <td>{row['subject']}</td>
            <td>
                <div class="email-popover">
                    {popover_content}
                </div>
            </td>
        </tr>
        """
        html_rows.append(html_row)
    
    # Create the complete HTML table
    html_table = f"""
    <table width="100%" border="1" cellspacing="0" cellpadding="5">
        <thead>
            <tr>
                <th>Date</th>
                <th>De</th>
                <th>À</th>
                <th>Sujet</th>
                <th style="display:none;"></th>
            </tr>
        </thead>
        <tbody>
            {"".join(html_rows)}
        </tbody>
    </table>
    """
    
    # Display the HTML table
    st.markdown(html_table, unsafe_allow_html=True)

def _create_simple_modal_email_table(
    emails_df: pd.DataFrame,
    display_df: pd.DataFrame,
    key_prefix: str
) -> None:
    """Create an email table with a simple native Streamlit modal when clicked."""
    
    # Add an internal index column to track selections
    display_df = display_df.copy()
    display_df['_index'] = list(range(len(display_df)))
    
    # Initialize session state variables if not exists
    email_key = f"{key_prefix}_email_open"
    selected_email_key = f"{key_prefix}_selected_idx"
    
    if email_key not in st.session_state:
        st.session_state[email_key] = False
    if selected_email_key not in st.session_state:
        st.session_state[selected_email_key] = None
    
    # Inject CSS for styling
    st.markdown(EMAIL_POPOVER_CSS, unsafe_allow_html=True)
    
    # Display the standard Streamlit table
    st.caption("Utilisez le sélecteur ci-dessous pour voir le contenu d'un email")
    
    # Display simple table using standard Streamlit dataframe
    st.dataframe(
        display_df[['date', 'from', 'to', 'subject']],
        hide_index=True,
        use_container_width=True,
        key=f"{key_prefix}_table"
    )
    
    # Provide a selectbox option for selecting emails
    cols = st.columns([3, 1])
    with cols[0]:
        selected_idx = st.selectbox(
            "Sélectionnez un email à afficher",
            options=list(range(len(display_df))),
            format_func=lambda i: f"{display_df.iloc[i]['date']} - {display_df.iloc[i]['subject'][:40]}...",
            key=f"{key_prefix}_select"
        )
    
    with cols[1]:
        # Button to view the selected email
        if st.button("Voir le contenu", key=f"{key_prefix}_view_btn"):
            st.session_state[selected_email_key] = selected_idx
            st.session_state[email_key] = True
            st.rerun()
    
    # Show email content as a modal overlay if an email is selected
    if st.session_state[email_key] and st.session_state[selected_email_key] is not None:
        try:
            selected_idx = st.session_state[selected_email_key]
            
            # Make sure the index is valid
            if 0 <= selected_idx < len(emails_df):
                selected_email = emails_df.iloc[selected_idx]
                
                # Create overlay effect
                st.markdown("""
                <div class="overlay"></div>
                """, unsafe_allow_html=True)
                
                # Create a styled container for the email content
                st.markdown("""
                <div class="email-modal">
                """, unsafe_allow_html=True)
                
                # Email header (title)
                st.markdown(f"## Email: {selected_email['subject'][:100]}")
                
                # Email metadata
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**De:** {selected_email['from']}")
                    st.markdown(f"**À:** {selected_email['to']}")
                
                with col2:
                    st.markdown(f"**Date:** {format_email_date(selected_email['date'])}")
                    if selected_email.get('has_attachments'):
                        st.markdown(f"**Pièces jointes:** {selected_email['attachments']}")
                
                # Email body
                st.markdown("---")
                st.text_area(
                    "Contenu de l'email", 
                    value=selected_email['body'], 
                    height=400,
                    disabled=True
                )
                
                # Close button
                if st.button("Fermer", key=f"{key_prefix}_close_btn"):
                    st.session_state[email_key] = False
                    st.rerun()
                
                # Close the styled container
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Invalid index
                st.error(f"Index invalide: {selected_idx}")
                st.session_state[email_key] = False
                st.rerun()
        except Exception as e:
            # Log the error and clear the invalid state
            st.error(f"Erreur lors de l'affichage de l'email: {str(e)}")
            st.session_state[email_key] = False
            st.rerun()

if __name__ == "__main__":
    # Test code - this will run when the module is executed directly
    st.title("Email Viewer Test")
    
    # Create sample data
    data = {
        "date": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
        "from": ["sender1@example.com", "sender2@example.com"],
        "to": ["recipient1@example.com", "recipient2@example.com"],
        "subject": ["Test Subject 1", "Test Subject 2"],
        "body": ["This is the body of email 1", "This is the body of email 2"],
        "has_attachments": [False, True],
        "attachments": ["", "file.pdf"]
    }
    
    df = pd.DataFrame(data)
    
    # Display the table
    create_email_table_with_viewer(df)
