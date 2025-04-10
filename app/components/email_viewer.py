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
from streamlit_modal import Modal
import quopri
import base64
import re
import email.header

# Add the project root to the path so we can import constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Try to import constants, with a fallback for testing
try:
    from constants import EMAIL_DISPLAY_TYPE
except ImportError:
    # Default for testing
    EMAIL_DISPLAY_TYPE = "MODAL"

# CSS for the email display - optimized for modal positioning and viewport constraints
EMAIL_STYLE_CSS = """
<style>
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

/* Specific targeting for the email modal by key pattern */
div[data-modal-container='true'][key*='_email_modal_'] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    z-index: 999992 !important;
}

/* Critical fix for modal positioning - direct attribute targeting */
div[data-modal-container='true'] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 999992 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* !!! MODAL POSITIONING FIXES !!! */
/* Style for the streamlit-modal library specifically */
.streamlit-modal {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 999999 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    background-color: rgba(0,0,0,0.5) !important;
}

.streamlit-modal .modal-dialog {
    max-width: 95vw !important;
    max-height: 95vh !important;
    width: 650px !important;
    margin: 0 auto !important;
    overflow: visible !important;
    position: relative !important;
}

.streamlit-modal .modal-content {
    max-height: 90vh !important;
    overflow-y: auto !important;
    border-radius: 8px !important;
    box-shadow: 0 0 20px rgba(0,0,0,0.3) !important;
}

/* Fix for the modal inner content margins */
div[data-modal-container='true'] > div:first-child > div:first-child {
    width: unset !important;
    padding: 20px !important;
    margin-top: 0 !important; /* Remove the 40px margin */
}

/* Override any modal dialog to ensure it's visible in the viewport */
div[data-testid="stModal"] {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    max-height: 90vh !important;
    max-width: 95vw !important;
    width: 650px !important;
    z-index: 9999 !important;
}

/* Style the close button to be more visible and prominent */
div[data-testid="baseButton-secondary"] {
    background-color: #e74c3c !important;
    color: white !important;
    border-color: #c0392b !important;
    padding: 0.5rem 1rem !important;
    font-weight: bold !important;
    width: 100% !important;
    margin: 0.5rem 0 !important;
    font-size: 1rem !important;
}

/* Prevent horizontal overflow in email content */
.element-container, .stMarkdown, .stMarkdown p {
    max-width: 100% !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Make text area content more readable */
.stTextArea textarea {
    font-family: monospace !important;
    height: auto !important;
    max-height: 40vh !important;
    font-size: 0.9rem !important;
}

/* Email metadata needs to stay within bounds */
.stMarkdown p, .email-field {
    max-width: 100% !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Ensure there's always space for the button at the bottom */
.modal-footer {
    margin-top: 15px !important;
    text-align: center !important;
    padding-bottom: 15px !important;
}
</style>
"""

def format_email_date(date_obj):
    """Format a datetime object for display."""
    if pd.isna(date_obj):
        return ""
    return date_obj.strftime('%Y-%m-%d %H:%M')

def decode_email_text(text, encoding='utf-8'):
    """
    Decode email text that may be encoded in various formats (quoted-printable, base64, MIME headers)

    Args:
        text: The text to decode
        encoding: The character encoding to use (default: utf-8)

    Returns:
        Decoded text
    """
    if text is None:
        return ""

    # First, check for MIME encoded headers (like =?utf-8?q?text?=)
    mime_pattern = r'=\?[\w-]+\?[QqBb]\?[^?]+\?='
    if isinstance(text, str) and re.search(mime_pattern, text):
        try:
            # Use email.header to decode MIME encoded headers
            decoded_parts = email.header.decode_header(text)
            # Join the decoded parts
            result = ''
            for decoded_text, charset in decoded_parts:
                if isinstance(decoded_text, bytes):
                    if charset is None:
                        charset = encoding
                    result += decoded_text.decode(charset, errors='replace')
                else:
                    result += decoded_text
            return result
        except Exception as e:
            print(f"Error decoding MIME header: {e}")

    # Check if this looks like quoted-printable text
    if isinstance(text, str) and "=C3=" in text:
        try:
            # Convert string to bytes, decode quoted-printable, then decode with specified charset
            text_bytes = text.encode('ascii', errors='ignore')
            decoded_bytes = quopri.decodestring(text_bytes)
            return decoded_bytes.decode(encoding, errors='replace')
        except Exception as e:
            print(f"Error decoding quoted-printable: {e}")
            return text

    # Also try to handle base64 encoded content
    if isinstance(text, str) and "Content-Transfer-Encoding: base64" in text:
        try:
            # Try to extract and decode base64 content
            parts = text.split('\n\n', 1)
            if len(parts) > 1:
                content = parts[1].strip()
                decoded = base64.b64decode(content).decode(encoding, errors='replace')
                return parts[0] + '\n\n' + decoded
        except Exception as e:
            print(f"Error decoding base64: {e}")

    return text

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

    # Decode the text fields for display
    for field in ['from', 'to', 'subject']:
        if field in display_df.columns:
            display_df[field] = display_df[field].apply(decode_email_text)

    if EMAIL_DISPLAY_TYPE == "POPOVER":
        _create_popover_email_table(emails_df, display_df, key_prefix)
    else:  # Default to MODAL
        _create_modal_email_table(emails_df, display_df, key_prefix)

def _create_popover_email_table(
    emails_df: pd.DataFrame,
    display_df: pd.DataFrame,
    key_prefix: str
) -> None:
    """Create an email table with popover display on hover."""
    st.write("Popover not implemented in this version.")
    # Implementation would go here if needed

def _create_modal_email_table(
    emails_df: pd.DataFrame,
    display_df: pd.DataFrame,
    key_prefix: str
) -> None:
    """Create an email table with a modal using streamlit_modal library when clicked."""

    # Add an internal index column to track selections
    display_df = display_df.copy()
    display_df['_index'] = list(range(len(display_df)))

    # Initialize session state variables if not exists
    selected_email_key = f"{key_prefix}_selected_idx"
    if selected_email_key not in st.session_state:
        st.session_state[selected_email_key] = None

    # Inject CSS for styling the table and modal
    st.markdown(EMAIL_STYLE_CSS, unsafe_allow_html=True)

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
            st.rerun()

    # Show email content in a modal if an email is selected
    if st.session_state[selected_email_key] is not None:
        # Get the index of the person whose details should be shown
        selected_idx = st.session_state[selected_email_key]

        # Make sure the index is valid
        if 0 <= selected_idx < len(emails_df):
            selected_email = emails_df.iloc[selected_idx]

            # Decode the subject and body
            decoded_subject = decode_email_text(selected_email['subject'])

            # Create and configure the Modal with viewport-centered positioning
            modal = Modal(
                title=f"Email: {decoded_subject[:40] if len(decoded_subject) > 40 else decoded_subject}",
                key=f"{key_prefix}_email_modal_{selected_idx}",
                max_width=650  # Slightly smaller to ensure it fits
            )

            print(f"{key_prefix}_email_modal_{selected_idx}")

            # Inject modal-specific CSS that targets the specific modal
            st.markdown(f"""
            <style>
            /* Target this specific modal */
            div[data-modal-container='true'][key="{key_prefix}_email_modal_{selected_idx}"] {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                z-index: 999992 !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }}

            /* Target the inner content div with the unwanted margin */
            div[data-modal-container='true'][key="{key_prefix}_email_modal_{selected_idx}"] > div:first-child > div:first-child {{
                width: unset !important;
                padding: 20px !important;
                margin-top: 0 !important; /* Remove the 40px margin */
            }}

            /* Target modal content wrapper */
            div[data-modal-container='true'] .stModal {{
                max-width: 95vw !important;
                width: 650px !important;
                max-height: 90vh !important;
                overflow: auto !important;
            }}
            </style>
            """, unsafe_allow_html=True)


            # Code to hide the native "X" close button in the modal
            # This is a workaround to ensure the modal is closed only through the custom button sadly.
            st.markdown(f"""
            <style>
                /* Hide the native "X" close button in the modal */
                [class*="st-key-explorer_email_modal_0-close"] {{
                    display: none !important;
                }}
            </style>
            """, unsafe_allow_html=True)

            # Modal content
            with modal.container():
                # Email metadata with text wrapping for long values - properly decoded
                decoded_from = decode_email_text(selected_email['from'])
                decoded_to = decode_email_text(selected_email['to'])

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div class='email-field'><strong>De:</strong> {decoded_from}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='email-field'><strong>À:</strong> {decoded_to}</div>", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"<div class='email-field'><strong>Date:</strong> {format_email_date(selected_email['date'])}</div>", unsafe_allow_html=True)
                    if selected_email.get('has_attachments'):
                        decoded_attachments = decode_email_text(selected_email['attachments'])
                        st.markdown(f"<div class='email-field'><strong>Pièces jointes:</strong> {decoded_attachments}</div>", unsafe_allow_html=True)

                # Email body with smaller height to ensure modal fits
                st.markdown("---")

                # Decode the email body for proper display
                decoded_body = decode_email_text(selected_email['body'])

                st.text_area(
                    "Contenu de l'email",
                    value=decoded_body,
                    height=min(len(decoded_body.splitlines()) * 16, 180),  # Even more constrained height
                    disabled=True,
                    key=f"textarea_{selected_idx}"
                )

                # Close button in footer section
                st.markdown("<div class='modal-footer'>", unsafe_allow_html=True)
                close_col1, close_col2, close_col3 = st.columns([1, 1, 1])
                with close_col2:
                    if st.button("Fermer", key=f"{key_prefix}_close_btn_{selected_idx}", use_container_width=True):
                        st.session_state[selected_email_key] = None
                        st.rerun()


                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Invalid index
            st.error(f"Index invalide: {selected_idx}")
            st.session_state[selected_email_key] = None

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
