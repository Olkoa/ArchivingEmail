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
# Using native st.dialog instead of streamlit_modal for better reliability
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
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

/* Make text area content more readable with better styling */
.stTextArea textarea {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    background-color: #ffffff !important;
    border: 1px solid #ddd !important;
    border-radius: 6px !important;
    padding: 12px !important;
    color: #333 !important;
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

    return text

def clear_email_selection(key_prefix: str) -> None:
    """Clear the selected email for a given key prefix. Useful when search or filters change."""
    selected_email_key = f"{key_prefix}_selected_idx"
    if selected_email_key in st.session_state:
        st.session_state[selected_email_key] = None

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
    
    # Configure grid selection
    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False,
        pre_selected_rows=[]
    )
    
    # Configure columns
    gb.configure_column("date", header_name="Date", width=120)
    gb.configure_column("from", header_name="De", width=200)
    gb.configure_column("recipient_email", header_name="À", width=200)
    gb.configure_column("subject", header_name="Sujet", flex=1)
    
    # Make rows clickable
    gb.configure_grid_options(
        onRowClicked="function(params) { params.api.selectNode(params.node, true); }",
        suppressRowDeselection=True
    )
    
    grid_options = gb.build()

    # Display the AgGrid with paginated data
    grid_response = AgGrid(
        paginated_display_df[['date', 'from', 'recipient_email', 'subject']],
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        key=f"{key_prefix}_aggrid_page_{current_page}"  # Include page in key to avoid conflicts
    )

    # Pagination controls (only show if more than one page)
    if total_pages > 1:
        st.markdown("---")
        
        # Create pagination layout
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1.5, 1.5, 1])
        
        with col1:
            if st.button("⏮️ Premier", key=f"{key_prefix}_first_page", disabled=(current_page == 1)):
                st.session_state[current_page_key] = 1
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.rerun()
        
        with col2:
            if st.button("⏪ Précédent", key=f"{key_prefix}_prev_page", disabled=(current_page == 1)):
                st.session_state[current_page_key] = current_page - 1
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.rerun()
        
        with col3:
            if st.button("Suivant ⏩", key=f"{key_prefix}_next_page", disabled=(current_page == total_pages)):
                st.session_state[current_page_key] = current_page + 1
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.rerun()
        
        with col4:
            if st.button("⏭️ Dernier", key=f"{key_prefix}_last_page", disabled=(current_page == total_pages)):
                st.session_state[current_page_key] = total_pages
                st.session_state[selected_email_key] = None  # Clear selection on page change
                st.rerun()
        
        with col5:
            st.markdown(f"<div style='text-align: center; padding-top: 8px;'><strong>Page {current_page}/{total_pages}</strong></div>", unsafe_allow_html=True)
        
        with col6:
            # Page jump input
            target_page = st.number_input(
                "Aller à la page:",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                key=f"{key_prefix}_page_input",
                label_visibility="collapsed"
            )
        
        with col7:
            if st.button("Aller", key=f"{key_prefix}_go_page"):
                if 1 <= target_page <= total_pages:
                    st.session_state[current_page_key] = target_page
                    st.session_state[selected_email_key] = None  # Clear selection on page change
                    st.rerun()

    # Check if a row was selected
    try:
        # AgGrid returns a dictionary with 'selected_rows' key
        if (hasattr(grid_response, '__getitem__') and 
            'selected_rows' in grid_response and 
            grid_response['selected_rows'] is not None and 
            len(grid_response['selected_rows']) > 0):
            
            selected_rows_data = grid_response['selected_rows']
            
            # Get the first selected row
            if hasattr(selected_rows_data, 'iloc'):
                # It's a DataFrame
                selected_row = selected_rows_data.iloc[0]
            elif isinstance(selected_rows_data, list) and len(selected_rows_data) > 0:
                # It's a list of dictionaries
                selected_row = selected_rows_data[0]
            else:
                return
            
            # Find the corresponding index in the original paginated dataframe
            # We need to match based on the data since AgGrid might reorder
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

                # Email body in a styled container
                st.markdown('<div class="email-content">', unsafe_allow_html=True)
                
                # Decode the email body for proper display
                decoded_body = decode_email_text(selected_email['body'])

                # Calculate height more generously for larger modal
                content_height = max(min(len(decoded_body.splitlines()) * 20, 500), 200)  # Larger min/max heights

                st.text_area(
                    "Contenu de l'email",
                    value=decoded_body,
                    height=content_height,
                    disabled=True,
                    key=f"dialog_textarea_{selected_idx}",
                    label_visibility="collapsed"  # Hide the label for cleaner look
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
