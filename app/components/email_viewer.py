"""
Email viewer component for the Olkoa project.

This module provides functions for displaying email content in different formats.
"""

import streamlit as st
import pandas as pd
from typing import Callable, Dict, Any, List, Optional
import os
import sys
import json
# Using native st.dialog instead of streamlit_modal for better reliability
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import quopri
import base64
import re
import email.header
from html import escape

# Add the project root to the path so we can import constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Try to import constants, with a fallback for testing
try:
    from constants import EMAIL_DISPLAY_TYPE
except ImportError:
    # Default for testing
    EMAIL_DISPLAY_TYPE = "MODAL"

# CSS for the email display - enhanced for better modal appearance
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

/* AgGrid styling */
.ag-theme-streamlit {
    --ag-header-background-color: #f0f0f0;
    --ag-header-foreground-color: #333;
    --ag-row-hover-color: #f0f8ff;
    --ag-selected-row-background-color: #e3f2fd;
}

.ag-theme-streamlit .ag-row {
    cursor: pointer;
}

.ag-theme-streamlit .ag-row:hover {
    background-color: #f0f8ff !important;
}

.ag-theme-streamlit .ag-row-selected {
    background-color: #e3f2fd !important;
}

/* Enhanced modal styling for larger size */
div[data-testid="stModal"] {
    width: 95vw !important;
    max-width: 95vw !important;
    height: 90vh !important;
    max-height: 90vh !important;
}

div[data-testid="stModal"] > div {
    width: 100% !important;
    height: 100% !important;
    max-height: 100% !important;
}

/* Improved text area styling with better readability */
.stTextArea textarea {
    font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
    background-color: #ffffff !important;
    border: 1px solid #e1e5e9 !important;
    border-radius: 8px !important;
    padding: 16px !important;
    color: #2d3748 !important;
    font-weight: 400 !important;
    letter-spacing: 0.01em !important;
}

/* Focus state for text areas */
.stTextArea textarea:focus {
    border-color: #007bff !important;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
    outline: none !important;
}

/* Email metadata styling */
.email-metadata {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
    border-left: 4px solid #007bff;
}

.email-field {
    margin-bottom: 8px;
    font-size: 0.95rem;
}

.email-field strong {
    color: #495057;
    margin-right: 8px;
}

/* Email content container */
.email-content {
    background-color: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    overflow: hidden;
}

/* Pagination styling */
.pagination-info {
    text-align: center;
    color: #6c757d;
    font-size: 0.9rem;
    margin: 10px 0;
}

/* Responsive design for modal content */
@media (max-width: 768px) {
    div[data-testid="stModal"] {
        width: 98vw !important;
        height: 95vh !important;
    }
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

    if isinstance(text, str):
        try:
            text = text.encode('utf-8', 'replace').decode('utf-8')
        except Exception:
            # Fallback: replace surrogates manually
            text = text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

        # Heal common mojibake patterns (e.g., 'Ã©', 'Â ') caused by double-decoding
        suspicious_sequences = ('Ã', 'Â', 'â€™', 'â€œ', 'â€', 'â€“', 'â€”', 'â€¢', 'â€˜', 'â€¢')
        if any(seq in text for seq in suspicious_sequences):
            try:
                recovered = text.encode('latin-1', 'ignore').decode('utf-8', 'ignore')
                if recovered:
                    text = recovered
            except Exception:
                pass

    return text

def clear_email_selection(key_prefix: str) -> None:
    """Clear the selected email for a given key prefix. Useful when search or filters change."""
    selected_email_key = f"{key_prefix}_selected_idx"
    if selected_email_key in st.session_state:
        st.session_state[selected_email_key] = None

def _clean_html_artifacts(text: str) -> str:
    """Remove leading/trailing HTML remnants such as stray </div> tags."""
    if not text or not isinstance(text, str):
        return text
    text = re.sub(r'^(</?(div|p|span)[^>]*>\s*)+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(</?(div|p|span)[^>]*>\s*)+$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(?mi)^\s*</?(div|p|span)[^>]*>\s*$\n?', '', text)
    return text.strip()

def parse_email_thread(email_body: str) -> list:
    """Parse an email thread to separate individual messages.
    
    Returns a list of dictionaries, each containing:
    - 'content': the message content
    - 'is_reply': whether this is a reply (True) or the main message (False)
    - 'sender': extracted sender if found
    - 'recipient': extracted recipient if found
    - 'date': extracted date if found
    - 'subject': extracted subject if found
    """
    if not email_body or not isinstance(email_body, str):
        return [{'content': email_body or '', 'is_reply': False, 'sender': None, 'recipient': None, 'date': None, 'subject': None}]
    
    # Common delimiters that indicate start of previous message
    reply_patterns = [
        # French Outlook format patterns
        r'De\s*:\s*.+?(?=Envoyé\s*:|\n\n|$)',  # "De: ... Envoyé:" or end
        r'From\s*:\s*.+?(?=Sent\s*:|\n\n|$)',     # "From: ... Sent:" or end

        # Standard reply patterns
        r'Le[ \t]+[\S\s]{0,120}?a écrit\s*:',  # Robust French pattern tolerating line breaks before "a écrit:"
        r'On .+ at .+, .+ wrote\s*:',    # English: "On [date] at [time], [sender] wrote:"
        r'Le .+ <.+> a écrit\s*:',      # "Le [date] <email> a écrit :"

        # Forward delimiters
        r'‐‐‐‐‐‐‐ Original Message ‐‐‐‐‐‐‐',
        r'-----Original Message-----',
        
        # Signature-like patterns that often precede quoted messages
        r'_{20,}',  # Very long underscores
        r'={20,}',  # Very long equals signs
    ]
    
    import re
    
    # Find all delimiter positions
    delimiters = []
    for pattern in reply_patterns:
        matches = list(re.finditer(pattern, email_body, re.MULTILINE | re.IGNORECASE | re.DOTALL))
        for match in matches:
            delimiters.append((match.start(), pattern, match.group()))
    
    # Sort delimiters by position
    delimiters.sort(key=lambda x: x[0])
    
    if not delimiters:
        # No delimiters found, return as single message
        return [{'content': email_body.strip(), 'is_reply': False, 'sender': None, 'recipient': None, 'date': None, 'subject': None}]
    
    # Split by ALL delimiters to create multiple messages
    messages = []
    last_pos = 0
    
    for i, (pos, pattern, delimiter_text) in enumerate(delimiters):
        # Add the content before this delimiter as a message
        if pos > last_pos:
            content = email_body[last_pos:pos].strip()
            if content:
                messages.append({
                    'content': content,
                    'is_reply': i > 0,  # First segment is main message
                    'sender': None,
                    'recipient': None,
                    'date': None,
                    'subject': None
                })
        
        # Find the start of the next segment
        if i < len(delimiters) - 1:
            next_pos = delimiters[i + 1][0]
        else:
            next_pos = len(email_body)
        
        # Extract the full segment including delimiter for metadata
        reply_segment = email_body[pos:next_pos]
        reply_content = reply_segment.strip()

        if reply_content.strip().lower() == "</div>":
            last_pos = next_pos
            continue

        if reply_content:
            # Extract metadata from the reply content (including delimiter/header)
            metadata = extract_email_metadata(reply_content)

            # Remove the delimiter text from the content shown to the user
            content_start = pos + len(delimiter_text)
            message_body = email_body[content_start:next_pos].strip()

            # Clean leading/trailing HTML artifacts that may remain from the split
            message_body = _clean_html_artifacts(message_body)
            if not message_body:
                message_body = _clean_html_artifacts(reply_content)

            has_metadata = any(metadata.get(key) for key in ('sender', 'recipient', 'date', 'subject'))
            if not message_body and not has_metadata:
                last_pos = next_pos
                continue

            # print(message_body)

            messages.append({
                'content': message_body,
                'is_reply': True,
                'sender': metadata.get('sender'),
                'recipient': metadata.get('recipient'),
                'date': metadata.get('date'),
                'subject': metadata.get('subject')
            })
        
        last_pos = next_pos
    
    # If no messages were created, return the original as single message
    if not messages:
        return [{'content': email_body.strip(), 'is_reply': False, 'sender': None, 'recipient': None, 'date': None, 'subject': None}]
    
    return messages

def extract_email_metadata(email_text: str) -> dict:
    """Extract sender, recipient, date, and subject from email text."""
    import re
    
    metadata = {'sender': None, 'recipient': None, 'date': None, 'subject': None}
    
    # Extract sender patterns
    sender_patterns = [
        r'De\s*:\s*(.+?)(?=\n|Envoyé|$)',  # French Outlook "De: sender"
        r'From\s*:\s*(.+?)(?=\n|Sent|$)',     # English Outlook "From: sender"
        r'Le .+, (.+) a écrit',              # French format name
    ]
    
    for pattern in sender_patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
        if match:
            sender = match.group(1).strip()
            # Clean up sender (remove <> brackets if present)
            sender = re.sub(r'[<>]', '', sender).strip()
            # If it contains both name and email, prefer the email part
            email_match = re.search(r'([\w\.-]+@[\w\.-]+)', sender)
            if email_match:
                metadata['sender'] = email_match.group(1)
            else:
                metadata['sender'] = sender
            break
    
    # Extract recipient patterns
    recipient_patterns = [
        r'À\s*:\s*(.+?)(?=\n|Cc|Objet|$)',    # French "\u00c0: recipient"
        r'To\s*:\s*(.+?)(?=\n|Cc|Subject|$)',   # English "To: recipient"
    ]
    
    for pattern in recipient_patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
        if match:
            recipient = match.group(1).strip()
            # Extract first email if multiple recipients
            email_match = re.search(r'([\w\.-]+@[\w\.-]+)', recipient)
            if email_match:
                metadata['recipient'] = email_match.group(1)
            else:
                # If no email found, take first part before semicolon
                first_recipient = recipient.split(';')[0].strip()
                metadata['recipient'] = first_recipient
            break
    
    # Extract date patterns
    date_patterns = [
        r'Envoyé\s*:\s*(.+?)(?=\n|À|$)',     # French "Envoyé: date"
        r'Sent\s*:\s*(.+?)(?=\n|To|$)',        # English "Sent: date"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata['date'] = match.group(1).strip()
            break
    
    # Extract subject patterns
    subject_patterns = [
        r'Objet\s*:\s*(.+?)(?=\n|$)',          # French "Objet: subject"
        r'Subject\s*:\s*(.+?)(?=\n|$)',        # English "Subject: subject"
    ]
    
    for pattern in subject_patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata['subject'] = match.group(1).strip()
            break
    
    return metadata

def apply_contact_filter(emails_df: pd.DataFrame, contact_email: str) -> pd.DataFrame:
    """Filter emails to show only those involving a specific contact (as sender or recipient).
    Only searches in 'from' and 'recipient_email' fields, not in body or subject.
    """
    if contact_email and not emails_df.empty:
        # Clean the contact email (remove any whitespace)
        contact_email = contact_email.strip()
        
        # Filter emails where the contact is either sender or in recipients
        # For sender: exact match (case-insensitive)
        sender_mask = emails_df['from'].fillna('').str.lower() == contact_email.lower()
        
        # For recipients: check if contact email appears in the recipient list
        # Split by comma and check each recipient
        recipient_mask = emails_df['recipient_email'].fillna('').apply(
            lambda recipients: any(
                recipient.strip().lower() == contact_email.lower() 
                for recipient in str(recipients).split(',') 
                if recipient.strip()
            )
        )
        
        # Combine both conditions
        mask = sender_mask | recipient_mask
        
        return emails_df[mask]
    return emails_df

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

    print(emails_df.columns)
    # Create a copy with limited columns for display
    display_df = emails_df[['date', 'from', 'recipient_email', 'subject']].copy() # to = recipient_email

    # Format date for display
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].apply(format_email_date)

    # Decode the text fields for display
    for field in ['from', 'recipient_email', 'subject']:
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
    """Create an email table with AgGrid and modal display when row is clicked."""

    # Add an internal index column to track selections
    display_df = display_df.copy()
    display_df['_index'] = list(range(len(display_df)))

    # Pagination settings
    ITEMS_PER_PAGE = 50
    total_items = len(display_df)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE  # Ceiling division
    
    # Session state management for pagination and selection
    selected_email_key = f"{key_prefix}_selected_idx"
    current_page_key = f"{key_prefix}_current_page"
    data_hash_key = f"{key_prefix}_data_hash"
    
    # Calculate a simple hash of the current data to detect changes
    current_data_hash = hash(str(len(display_df)) + str(display_df.iloc[0].to_dict()) if len(display_df) > 0 else "empty")
    
    if selected_email_key not in st.session_state:
        st.session_state[selected_email_key] = None
    if current_page_key not in st.session_state:
        st.session_state[current_page_key] = 1
    if data_hash_key not in st.session_state:
        st.session_state[data_hash_key] = current_data_hash
    
    # Clear selection if data has changed (e.g., from search/filtering)
    if st.session_state[data_hash_key] != current_data_hash:
        st.session_state[selected_email_key] = None
        st.session_state[current_page_key] = 1  # Reset to first page
        st.session_state[data_hash_key] = current_data_hash
        # Also clear previous selection tracking
        if f"{key_prefix}_prev_selection" in st.session_state:
            st.session_state[f"{key_prefix}_prev_selection"] = None
        # Reset number input tracking
        if f"{key_prefix}_prev_target_page" in st.session_state:
            st.session_state[f"{key_prefix}_prev_target_page"] = 1
        if f"{key_prefix}_number_input_changed" in st.session_state:
            st.session_state[f"{key_prefix}_number_input_changed"] = False

    # Ensure current page is within bounds
    if st.session_state[current_page_key] < 1:
        st.session_state[current_page_key] = 1
    elif st.session_state[current_page_key] > total_pages:
        st.session_state[current_page_key] = total_pages
    
    current_page = st.session_state[current_page_key]

    # Calculate pagination slice
    start_idx = (current_page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
    
    # Get the current page data
    paginated_display_df = display_df.iloc[start_idx:end_idx].copy()

    # Inject CSS for styling the table and modal
    st.markdown(EMAIL_STYLE_CSS, unsafe_allow_html=True)

    # Display instruction and pagination info
    if total_pages > 1:
        st.caption(f"Cliquez sur une ligne du tableau pour voir le contenu de l'email | Page {current_page} sur {total_pages} | Affichage des emails {start_idx + 1}-{end_idx} sur {total_items}")
    else:
        st.caption(f"Cliquez sur une ligne du tableau pour voir le contenu de l'email | Affichage de {total_items} emails")

    # Configure AgGrid options for paginated data
    gb = GridOptionsBuilder.from_dataframe(paginated_display_df[['date', 'from', 'recipient_email', 'subject']])
    
    # Configure grid selection with more restrictive settings
    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False,
        pre_selected_rows=[],
        rowMultiSelectWithClick=False,
        suppressRowClickSelection=False
    )
    
    # Configure columns
    gb.configure_column("date", header_name="Date", width=120)
    gb.configure_column("from", header_name="De", width=200)
    gb.configure_column("recipient_email", header_name="À", width=200)
    gb.configure_column("subject", header_name="Sujet", flex=1)
    
    # Make rows clickable but more controlled
    gb.configure_grid_options(
        onRowClicked="function(params) { params.api.selectNode(params.node, true); }",
        suppressRowDeselection=True,
        suppressCellSelection=True,
        suppressMultiSort=True,
        animateRows=False
    )
    
    grid_options = gb.build()

    # Display the AgGrid with paginated data
    grid_key = f"{key_prefix}_aggrid_{current_data_hash}_page_{current_page}"

    grid_response = AgGrid(
        paginated_display_df[['date', 'from', 'recipient_email', 'subject']],
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        key=grid_key,  # Include data hash + page to avoid stale renders
        reload_data=False,  # Prevent unnecessary reloads
        height=420
    )

    # Store the previous selection state to detect actual changes
    prev_selection_key = f"{key_prefix}_prev_selection"
    if prev_selection_key not in st.session_state:
        st.session_state[prev_selection_key] = None

    # Pagination controls (only show if more than one page)
    if total_pages > 1:
        st.markdown("---")
        
        # Create pagination layout
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1.5, 1.5, 1])
        
        with col1:
            if st.button("⏮️ Premier", key=f"{key_prefix}_first_page", disabled=(current_page == 1)):
                st.session_state[current_page_key] = 1
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.session_state[f"{key_prefix}_prev_selection"] = None  # Clear selection tracking
                st.rerun()
        
        with col2:
            if st.button("⏪ Précédent", key=f"{key_prefix}_prev_page", disabled=(current_page == 1)):
                st.session_state[current_page_key] = current_page - 1
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.session_state[f"{key_prefix}_prev_selection"] = None  # Clear selection tracking
                st.rerun()
        
        with col3:
            if st.button("Suivant ⏩", key=f"{key_prefix}_next_page", disabled=(current_page == total_pages)):
                st.session_state[current_page_key] = current_page + 1
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.session_state[f"{key_prefix}_prev_selection"] = None  # Clear selection tracking
                st.rerun()
        
        with col4:
            if st.button("⏭️ Dernier", key=f"{key_prefix}_last_page", disabled=(current_page == total_pages)):
                st.session_state[current_page_key] = total_pages
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.session_state[f"{key_prefix}_prev_selection"] = None  # Clear selection tracking
                st.rerun()
        
        with col5:
            st.markdown(f"<div style='text-align: center; padding-top: 8px;'><strong>Page {current_page}/{total_pages}</strong></div>", unsafe_allow_html=True)
        
        with col6:
            # Store the number input value from the previous run
            prev_target_page = st.session_state.get(f"{key_prefix}_prev_target_page", current_page)
            
            # Page jump input
            target_page = st.number_input(
                "Aller à la page:",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                key=f"{key_prefix}_page_input",
                label_visibility="collapsed"
            )
            
            # Detect if the number input changed (including +/-, arrow keys, Enter)
            number_input_changed = (target_page != prev_target_page)
            if number_input_changed:
                st.session_state[f"{key_prefix}_prev_target_page"] = target_page
                # Set flag to prevent modal opening on this run
                st.session_state[f"{key_prefix}_number_input_changed"] = True
                # Clear any selection when number input changes
                st.session_state[selected_email_key] = None
                st.session_state[f"{key_prefix}_prev_selection"] = None
        
        with col7:
            if st.button("Aller", key=f"{key_prefix}_go_page"):
                if 1 <= target_page <= total_pages:
                    st.session_state[current_page_key] = target_page
                    st.session_state[selected_email_key] = None  # Clear selection on page change
                    st.session_state[f"{key_prefix}_prev_selection"] = None  # Clear selection tracking
                    st.rerun()

    # Handle row selection with improved detection
    current_selection = None
    
    # Get the number input change status (if pagination is shown)
    number_input_changed = False
    if total_pages > 1:
        number_input_changed = st.session_state.get(f"{key_prefix}_number_input_changed", False)
        # Clear the flag after checking
        if number_input_changed:
            st.session_state[f"{key_prefix}_number_input_changed"] = False
    
    if (hasattr(grid_response, '__getitem__') and 
        'selected_rows' in grid_response and 
        grid_response['selected_rows'] is not None and 
        len(grid_response['selected_rows']) > 0):
        
        try:
            selected_rows_data = grid_response['selected_rows']
            
            # Get the first selected row
            if hasattr(selected_rows_data, 'iloc'):
                # It's a DataFrame
                selected_row = selected_rows_data.iloc[0]
            elif isinstance(selected_rows_data, list) and len(selected_rows_data) > 0:
                # It's a list of dictionaries
                selected_row = selected_rows_data[0]
            else:
                selected_row = None
            
            if selected_row is not None:
                # Create a unique identifier for this selection
                if hasattr(selected_row, 'get'):
                    # Dictionary access
                    current_selection = f"{selected_row.get('date', '')}_{selected_row.get('from', '')}_{selected_row.get('subject', '')}"
                else:
                    # Series access
                    current_selection = f"{selected_row['date']}_{selected_row['from']}_{selected_row['subject']}"
                
        except Exception as e:
            current_selection = None
    
    # Only process selection if:
    # 1. It's different from the previous one
    # 2. The number input wasn't just changed
    # This prevents false triggers from button clicks and other interactions
    if (current_selection is not None and 
        current_selection != st.session_state[prev_selection_key] and
        not number_input_changed):
        
        # Update the previous selection
        st.session_state[prev_selection_key] = current_selection
        
        # Find the corresponding email in the original dataframe
        try:
            selected_rows_data = grid_response['selected_rows']
            
            # Get the first selected row
            if hasattr(selected_rows_data, 'iloc'):
                selected_row = selected_rows_data.iloc[0]
            elif isinstance(selected_rows_data, list) and len(selected_rows_data) > 0:
                selected_row = selected_rows_data[0]
            else:
                selected_row = None
            
            if selected_row is not None:
                # Find the corresponding index in the original paginated dataframe
                for idx, row in paginated_display_df.iterrows():
                    try:
                        # Handle both dict and Series access
                        if hasattr(selected_row, 'get'):
                            # Dictionary access
                            if (str(row['date']) == str(selected_row.get('date', '')) and 
                                str(row['from']) == str(selected_row.get('from', '')) and 
                                str(row['subject']) == str(selected_row.get('subject', ''))):
                                # Convert paginated index to original dataframe index
                                original_idx = start_idx + (idx - paginated_display_df.index[0])
                                st.session_state[selected_email_key] = original_idx
                                break
                        else:
                            # Series access
                            if (str(row['date']) == str(selected_row['date']) and 
                                str(row['from']) == str(selected_row['from']) and 
                                str(row['subject']) == str(selected_row['subject'])):
                                # Convert paginated index to original dataframe index
                                original_idx = start_idx + (idx - paginated_display_df.index[0])
                                st.session_state[selected_email_key] = original_idx
                                break
                    except Exception as e:
                        continue
        except Exception as e:
            pass
    elif current_selection is None:
        # No selection, clear the previous selection tracking
        st.session_state[prev_selection_key] = None

    # Show email content in a dialog if an email is selected
    if st.session_state[selected_email_key] is not None:
        # Get the index of the person whose details should be shown
        selected_idx = st.session_state[selected_email_key]

        # Make sure the index is valid for the original dataframe
        if 0 <= selected_idx < len(emails_df):
            selected_email = emails_df.iloc[selected_idx]

            # Decode the subject and body
            decoded_subject = decode_email_text(selected_email['subject'])

            # Use st.dialog for modal display with larger size
            @st.dialog(f"Email: {decoded_subject[:40] if len(decoded_subject) > 40 else decoded_subject}", width="large")
            def show_email_dialog():
                # Email metadata in a styled container
                decoded_from = decode_email_text(selected_email['from'])
                decoded_to = decode_email_text(selected_email['recipient_email'])

                # Create a styled metadata section
                st.markdown(
                    f"""
                    <div class="email-metadata">
                        <div class="email-field"><strong>De:</strong> {decoded_from}</div>
                        <div class="email-field"><strong>À:</strong> {decoded_to}</div>
                        <div class="email-field"><strong>Date:</strong> {format_email_date(selected_email['date'])}</div>
                        {f'<div class="email-field"><strong>Pièces jointes:</strong> {decode_email_text(selected_email["attachments"])}</div>' if selected_email.get('has_attachments') else ''}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

                # Email body with thread parsing
                st.markdown('<div class="email-content">', unsafe_allow_html=True)
                
                # Decode the email body for proper display
                decoded_body = decode_email_text(selected_email['body'])

                # Parse the email thread
                thread_messages = parse_email_thread(decoded_body)
                thread_messages = [
                    msg for msg in thread_messages
                    if msg.get('content', '').strip().lower() not in {'</div>', '<div>', ''}
                ]

                print("thread_messages:", thread_messages)
                
                if len(thread_messages) > 1:
                    # Display as threaded conversation
                    st.markdown("### 💬 Conversation Thread")
                    
                    for i, message in enumerate(thread_messages):
                        if message['is_reply']:
                            # Display as a reply block
                            with st.container():
                                # Create metadata string
                                metadata_parts = []
                                if message['sender']:
                                    metadata_parts.append(f"de {message['sender']}")
                                if message['recipient']:
                                    metadata_parts.append(f"à {message['recipient']}")
                                if message['date']:
                                    metadata_parts.append(f"le {message['date']}")
                                
                                metadata_str = ' • '.join(metadata_parts) if metadata_parts else ''
                                
                                # Create a visual separator for replies
                                panel_metadata = escape(metadata_str) if metadata_str else ""
                                reply_subject = escape(message.get("subject") or "")

                                header_text = "📧 **Message précédent**"
                                if panel_metadata:
                                    header_text += f" ({panel_metadata})"

                                st.markdown(header_text)
                                if reply_subject:
                                    st.caption(f"Objet : {reply_subject}")

                                reply_content = _clean_html_artifacts(message['content'])
                                # print("reply_content:", reply_content)

                                # Calculate height for this message
                                message_height = max(min(len(reply_content.splitlines()) * 16, 250), 100)

                                st.text_area(
                                    "Message",
                                    value=reply_content,
                                    height=message_height,
                                    disabled=True,
                                    key=f"thread_message_{selected_idx}_{i}",
                                    label_visibility="collapsed"
                                )
                        else:
                            # Display as main message
                            if i == 0:
                                st.markdown("**📝 Message principal:**")

                            main_content = _clean_html_artifacts(message['content'])

                            # Calculate height for main message
                            main_height = max(min(len(main_content.splitlines()) * 20, 300), 150)

                            st.text_area(
                                "Message principal",
                                value=main_content,
                                height=main_height,
                                disabled=True,
                                key=f"main_message_{selected_idx}_{i}",
                                label_visibility="collapsed"
                            )
                else:
                    # Single message - display normally
                    cleaned_body = _clean_html_artifacts(decoded_body)
                    content_height = max(min(len(cleaned_body.splitlines()) * 20, 500), 200)
                    
                    st.text_area(
                        "Contenu de l'email",
                        value=cleaned_body,
                        height=content_height,
                        disabled=True,
                        key=f"dialog_textarea_{selected_idx}",
                        label_visibility="collapsed"
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)

                # Dialog closes automatically with native Streamlit controls
            
            # Show the dialog
            show_email_dialog()
                
        else:
            # Invalid index
            st.session_state[selected_email_key] = None

if __name__ == "__main__":
    # Test code - this will run when the module is executed directly
    st.title("Email Viewer Test")

    # Create sample data
    data = {
        "date": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
        "from": ["sender1@example.com", "sender2@example.com"],
        "recipient_email": ["recipient1@example.com", "recipient2@example.com"],
        "subject": ["Test Subject 1", "Test Subject 2"],
        "body": ["This is the body of email 1", "This is the body of email 2"],
        "has_attachments": [False, True],
        "attachments": ["", "file.pdf"]
    }

    df = pd.DataFrame(data)

    # Display the table
    create_email_table_with_viewer(df)
