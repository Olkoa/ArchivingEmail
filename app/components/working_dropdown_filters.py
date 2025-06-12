"""
Working Dropdown Filter Component

Uses Streamlit components properly to create a functional dropdown menu.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional


class WorkingDropdownFilters:
    """Creates a working dropdown filter menu using Streamlit components"""
    
    def __init__(self, page_name: str):
        self.page_name = page_name
        self.filter_configs = self._get_page_filter_config()
    
    def _get_page_filter_config(self) -> Dict[str, Any]:
        """Get filter configuration for the current page"""
        configs = {
            "Dashboard": {
                "show_filters": True,
                "filters": ["date_range", "mailbox", "direction", "has_attachments", "contact_filter"]
            },
            "Email Explorer": {
                "show_filters": True,
                "filters": ["date_range", "mailbox", "direction", "sender", "recipient", "has_attachments"]
            },
            "Graph": {
                "show_filters": False,
                "filters": []
            },
            "Recherche Sémantique": {
                "show_filters": True,
                "filters": ["date_range", "mailbox", "direction", "sender", "recipient", "has_attachments"]
            },
            "Recherche ElasticSearch": {
                "show_filters": True,
                "filters": ["date_range", "mailbox", "direction", "sender", "recipient", "has_attachments"]
            },
            "Chat + RAG": {
                "show_filters": False,
                "filters": []
            },
            "Colbert RAG": {
                "show_filters": False,
                "filters": []
            },
            "Structure de la boîte mail": {
                "show_filters": False,
                "filters": []
            }
        }
        
        return configs.get(self.page_name, {"show_filters": False, "filters": []})
    
    def should_show_filters(self) -> bool:
        """Check if filters should be shown for this page"""
        return self.filter_configs.get("show_filters", False)
    
    def render_dropdown_menu(self, 
                            emails_df: Optional[pd.DataFrame] = None, 
                            mailbox_options: List[str] = None,
                            email_filters = None) -> Tuple[Dict[str, Any], bool]:
        """
        Render the working dropdown filter menu
        
        Returns:
            Tuple[Dict[str, Any], bool]: (applied_filters, filters_changed)
        """
        
        if not self.should_show_filters():
            return {}, False
        
        # Count active filters
        active_count = self._count_active_filters()
        
        # Create the floating button and manage dropdown state
        self._render_floating_button_and_dropdown(active_count, emails_df, mailbox_options)
        
        # Return current filter state
        applied_filters = self._get_current_filters()
        return applied_filters, False
    
    def _render_floating_button_and_dropdown(self, active_count: int, emails_df: Optional[pd.DataFrame], mailbox_options: List[str]):
        """Render the floating button and dropdown using Streamlit session state"""
        
        # Initialize dropdown state
        dropdown_key = f"dropdown_open_{self.page_name}"
        if dropdown_key not in st.session_state:
            st.session_state[dropdown_key] = False
        
        # Create CSS for floating button
        self._inject_working_css()
        
        # Create the floating button using columns to position it
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col3:
            badge = f" ({active_count})" if active_count > 0 else ""
            button_text = f"🔧 Filtres{badge}"
            
            # Toggle button that actually works
            if st.button(button_text, key=f"filter_toggle_{self.page_name}", help="Cliquer pour ouvrir/fermer les filtres"):
                st.session_state[dropdown_key] = not st.session_state[dropdown_key]
        
        # Show dropdown content if open
        if st.session_state[dropdown_key]:
            self._render_dropdown_content(emails_df, mailbox_options)
    
    def _inject_working_css(self):
        """Inject CSS for the working dropdown"""
        css = """
        <style>
        /* Style the filter button */
        div[data-testid="column"]:nth-child(3) button {
            background: linear-gradient(90deg, #ff6b6b, #ee5a24) !important;
            color: white !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 12px 20px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3) !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        
        div[data-testid="column"]:nth-child(3) button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(238, 90, 36, 0.4) !important;
            background: linear-gradient(90deg, #ee5a24, #ff6b6b) !important;
        }
        
        /* Style the dropdown container */
        .filter-dropdown-content {
            position: fixed;
            top: 120px;
            right: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            border: 1px solid #e1e5e9;
            z-index: 999;
            min-width: 350px;
            max-width: 450px;
            max-height: 70vh;
            overflow-y: auto;
        }
        
        .filter-dropdown-header {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 16px 20px;
            border-bottom: 1px solid #dee2e6;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .filter-dropdown-title {
            font-size: 16px;
            font-weight: 700;
            color: #2c3e50;
            margin: 0;
        }
        
        .filter-section-title {
            font-size: 13px;
            font-weight: 600;
            color: #495057;
            margin: 16px 0 8px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .filter-dropdown-content {
                position: relative;
                top: auto;
                right: auto;
                left: 0;
                width: 100%;
                max-width: none;
                margin: 10px 0;
            }
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def _render_dropdown_content(self, emails_df: Optional[pd.DataFrame], mailbox_options: List[str]):
        """Render the dropdown content using Streamlit components"""
        
        # Create a container with custom CSS class
        st.markdown('<div class="filter-dropdown-content">', unsafe_allow_html=True)
        
        # Header
        st.markdown('''
        <div class="filter-dropdown-header">
            <div class="filter-dropdown-title">⚙️ Filtres - {}</div>
        </div>
        '''.format(self.page_name), unsafe_allow_html=True)
        
        # Content
        enabled_filters = self.filter_configs.get("filters", [])
        filters_changed = False
        
        # Basic filters section
        if any(f in enabled_filters for f in ["date_range", "mailbox"]):
            st.markdown('<div class="filter-section-title">📅 Données de base</div>', unsafe_allow_html=True)
            
            # Mailbox filter
            if "mailbox" in enabled_filters and mailbox_options:
                current_mailbox = st.session_state.get(f"filter_mailbox_{self.page_name}", "All Mailboxes")
                new_mailbox = st.selectbox(
                    "Boîte mail",
                    options=mailbox_options,
                    index=mailbox_options.index(current_mailbox) if current_mailbox in mailbox_options else 0,
                    key=f"dropdown_mailbox_{self.page_name}"
                )
                
                if new_mailbox != current_mailbox:
                    st.session_state[f"filter_mailbox_{self.page_name}"] = new_mailbox
                    filters_changed = True
            
            # Date range filter
            if "date_range" in enabled_filters:
                if emails_df is not None and not emails_df.empty and 'date' in emails_df.columns:
                    min_date = pd.to_datetime(emails_df['date']).min().date()
                    max_date = pd.to_datetime(emails_df['date']).max().date()
                else:
                    min_date = pd.to_datetime("2020-01-01").date()
                    max_date = pd.to_datetime("2025-12-31").date()
                
                current_date_range = st.session_state.get(f"filter_date_range_{self.page_name}", (min_date, max_date))
                new_date_range = st.date_input(
                    "Période",
                    value=current_date_range,
                    min_value=min_date,
                    max_value=max_date,
                    key=f"dropdown_date_range_{self.page_name}"
                )
                
                if new_date_range != current_date_range:
                    st.session_state[f"filter_date_range_{self.page_name}"] = new_date_range
                    filters_changed = True
        
        # Content filters section
        if any(f in enabled_filters for f in ["direction", "sender", "recipient"]):
            st.markdown('<div class="filter-section-title">📧 Contenu des emails</div>', unsafe_allow_html=True)
            
            # Direction filter
            if "direction" in enabled_filters:
                direction_options = ["Tous", "Envoyés", "Reçus"]
                current_direction = st.session_state.get(f"filter_direction_{self.page_name}", "Tous")
                new_direction = st.selectbox(
                    "Direction",
                    options=direction_options,
                    index=direction_options.index(current_direction) if current_direction in direction_options else 0,
                    key=f"dropdown_direction_{self.page_name}"
                )
                
                if new_direction != current_direction:
                    st.session_state[f"filter_direction_{self.page_name}"] = new_direction
                    filters_changed = True
            
            # Sender filter
            if "sender" in enabled_filters:
                sender_options = ["Tous"]
                if emails_df is not None and not emails_df.empty and 'from' in emails_df.columns:
                    unique_senders = sorted(emails_df['from'].dropna().unique().tolist())
                    sender_options.extend(unique_senders[:20])  # Limit for performance
                
                current_sender = st.session_state.get(f"filter_sender_{self.page_name}", "Tous")
                new_sender = st.selectbox(
                    "Expéditeur",
                    options=sender_options,
                    index=sender_options.index(current_sender) if current_sender in sender_options else 0,
                    key=f"dropdown_sender_{self.page_name}"
                )
                
                if new_sender != current_sender:
                    st.session_state[f"filter_sender_{self.page_name}"] = new_sender
                    filters_changed = True
            
            # Recipient filter  
            if "recipient" in enabled_filters:
                recipient_options = ["Tous"]
                if emails_df is not None and not emails_df.empty and 'recipient_email' in emails_df.columns:
                    unique_recipients = set()
                    for recipients in emails_df["recipient_email"].dropna():
                        if isinstance(recipients, str):
                            for recipient in recipients.split(','):
                                recipient = recipient.strip()
                                if recipient:
                                    unique_recipients.add(recipient)
                    recipient_options.extend(sorted(list(unique_recipients))[:20])  # Limit for performance
                
                current_recipient = st.session_state.get(f"filter_recipient_{self.page_name}", "Tous")
                new_recipient = st.selectbox(
                    "Destinataire",
                    options=recipient_options,
                    index=recipient_options.index(current_recipient) if current_recipient in recipient_options else 0,
                    key=f"dropdown_recipient_{self.page_name}"
                )
                
                if new_recipient != current_recipient:
                    st.session_state[f"filter_recipient_{self.page_name}"] = new_recipient
                    filters_changed = True
        
        # Special filters section
        if any(f in enabled_filters for f in ["has_attachments", "contact_filter"]):
            st.markdown('<div class="filter-section-title">🔍 Filtres spéciaux</div>', unsafe_allow_html=True)
            
            # Has attachments filter
            if "has_attachments" in enabled_filters:
                current_attachments = st.session_state.get(f"filter_has_attachments_{self.page_name}", False)
                new_attachments = st.checkbox(
                    "Avec pièces jointes uniquement",
                    value=current_attachments,
                    key=f"dropdown_attachments_{self.page_name}"
                )
                
                if new_attachments != current_attachments:
                    st.session_state[f"filter_has_attachments_{self.page_name}"] = new_attachments
                    filters_changed = True
            
            # Contact filter
            if "contact_filter" in enabled_filters:
                current_contact = st.session_state.get(f"filter_contact_{self.page_name}", "")
                new_contact = st.text_input(
                    "Filtrer par contact",
                    value=current_contact,
                    placeholder="Entrez une adresse email...",
                    key=f"dropdown_contact_{self.page_name}"
                )
                
                if new_contact != current_contact:
                    st.session_state[f"filter_contact_{self.page_name}"] = new_contact
                    filters_changed = True
        
        # Status and controls
        active_count = self._count_active_filters()
        if active_count > 0:
            st.success(f"✅ {active_count} filtre(s) actif(s)")
            
            # Clear all button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🗑️ Effacer tous les filtres", key=f"dropdown_clear_{self.page_name}"):
                    self._clear_all_filters()
                    st.rerun()
        else:
            st.info("ℹ️ Aucun filtre actif")
        
        # Close button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("❌ Fermer", key=f"dropdown_close_{self.page_name}"):
                st.session_state[f"dropdown_open_{self.page_name}"] = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-close if filters changed (optional)
        if filters_changed:
            st.rerun()
    
    def _count_active_filters(self) -> int:
        """Count the number of currently active filters"""
        count = 0
        
        if st.session_state.get(f"filter_date_range_{self.page_name}"):
            count += 1
        if st.session_state.get(f"filter_mailbox_{self.page_name}", "All Mailboxes") != "All Mailboxes":
            count += 1
        if st.session_state.get(f"filter_direction_{self.page_name}", "Tous") != "Tous":
            count += 1
        if st.session_state.get(f"filter_sender_{self.page_name}", "Tous") != "Tous":
            count += 1
        if st.session_state.get(f"filter_recipient_{self.page_name}", "Tous") != "Tous":
            count += 1
        if st.session_state.get(f"filter_has_attachments_{self.page_name}", False):
            count += 1
        if st.session_state.get(f"filter_contact_{self.page_name}"):
            count += 1
        
        return count
    
    def _get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values from session state"""
        return {
            'date_range': st.session_state.get(f"filter_date_range_{self.page_name}"),
            'mailbox': st.session_state.get(f"filter_mailbox_{self.page_name}", "All Mailboxes"),
            'direction': st.session_state.get(f"filter_direction_{self.page_name}", "Tous"),
            'sender': st.session_state.get(f"filter_sender_{self.page_name}", "Tous"),
            'recipient': st.session_state.get(f"filter_recipient_{self.page_name}", "Tous"),
            'has_attachments': st.session_state.get(f"filter_has_attachments_{self.page_name}", False),
            'contact_filter': st.session_state.get(f"filter_contact_{self.page_name}", "")
        }
    
    def _clear_all_filters(self):
        """Clear all filters for this page"""
        filter_keys = [
            f"filter_date_range_{self.page_name}",
            f"filter_mailbox_{self.page_name}",
            f"filter_direction_{self.page_name}",
            f"filter_sender_{self.page_name}",
            f"filter_recipient_{self.page_name}",
            f"filter_has_attachments_{self.page_name}",
            f"filter_contact_{self.page_name}"
        ]
        
        for key in filter_keys:
            if key in st.session_state:
                del st.session_state[key]


def create_working_dropdown_filters(page_name: str, 
                                   emails_df: Optional[pd.DataFrame] = None,
                                   mailbox_options: List[str] = None,
                                   email_filters = None) -> Tuple[Dict[str, Any], bool]:
    """
    Create working dropdown filters that actually function
    
    Args:
        page_name: Name of the current page
        emails_df: DataFrame containing email data (optional)
        mailbox_options: List of available mailbox options
        email_filters: Email filters object (for compatibility)
    
    Returns:
        Tuple[Dict[str, Any], bool]: (applied_filters, filters_changed)
    """
    filter_menu = WorkingDropdownFilters(page_name)
    
    if not filter_menu.should_show_filters():
        return {}, False
    
    return filter_menu.render_dropdown_menu(
        emails_df=emails_df,
        mailbox_options=mailbox_options,
        email_filters=email_filters
    )
