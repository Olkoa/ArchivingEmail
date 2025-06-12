"""
Filter Manager

Handles the creation and management of the hover-based filter menu system.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple
from .filter_config import FilterConfigManager, FilterType, filter_config_manager


class FilterManager:
    """Manages the filter system for the application"""
    
    def __init__(self, email_filters, project_root, mailbox_options):
        self.email_filters = email_filters
        self.project_root = project_root
        self.mailbox_options = mailbox_options
        self.config_manager = filter_config_manager
        
    def create_hover_menu_css(self) -> str:
        """Create CSS for the hover dropdown menu"""
        return """
        <style>
        .filter-menu-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            font-family: 'Source Sans Pro', sans-serif;
        }
        
        .filter-menu-trigger {
            background: linear-gradient(90deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            border: none;
            outline: none;
        }
        
        .filter-menu-trigger:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(238, 90, 36, 0.4);
            background: linear-gradient(90deg, #ee5a24, #ff6b6b);
        }
        
        .filter-menu-dropdown {
            position: absolute;
            top: 50px;
            right: 0;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            min-width: 320px;
            max-width: 450px;
            max-height: 70vh;
            overflow-y: auto;
            padding: 0;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px);
            transition: all 0.3s ease;
            border: 1px solid #e1e5e9;
        }
        
        .filter-menu-container:hover .filter-menu-dropdown {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }
        
        .filter-menu-header {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 16px 20px;
            border-bottom: 1px solid #dee2e6;
            border-radius: 12px 12px 0 0;
        }
        
        .filter-menu-title {
            font-size: 16px;
            font-weight: 700;
            color: #2c3e50;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .filter-menu-content {
            padding: 20px;
            max-height: 50vh;
            overflow-y: auto;
        }
        
        .filter-section {
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .filter-section:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        
        .filter-section-title {
            font-size: 13px;
            font-weight: 600;
            color: #495057;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .filter-control {
            margin-bottom: 12px;
        }
        
        .filter-label {
            font-size: 14px;
            color: #495057;
            margin-bottom: 6px;
            display: block;
            font-weight: 500;
        }
        
        .filter-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.2s ease;
        }
        
        .filter-input:focus {
            outline: none;
            border-color: #80bdff;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }
        
        .filter-checkbox {
            margin-right: 8px;
        }
        
        .filter-status {
            background: #e3f2fd;
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 13px;
            color: #1565c0;
            border-left: 4px solid #2196f3;
        }
        
        .clear-filters-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            margin-top: 10px;
            transition: background-color 0.2s ease;
        }
        
        .clear-filters-btn:hover {
            background: #c82333;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .filter-menu-container {
                position: fixed;
                top: 10px;
                right: 10px;
                left: 10px;
                width: auto;
            }
            
            .filter-menu-dropdown {
                right: 0;
                left: 0;
                max-width: none;
                margin: 0 10px;
            }
        }
        </style>
        """
    
    def get_current_filters(self, page_name: str) -> Dict[str, Any]:
        """Get current filter values from session state"""
        current_filters = {}
        
        enabled_filters = self.config_manager.get_enabled_filters(page_name)
        
        for filter_config in enabled_filters:
            filter_type = filter_config.filter_type
            
            # Get values from session state with appropriate defaults
            if filter_type == FilterType.DATE_RANGE:
                current_filters['date_range'] = st.session_state.get('filter_date_range', None)
            elif filter_type == FilterType.MAILBOX_SELECTION:
                current_filters['mailbox'] = st.session_state.get('selected_mailbox', 'All Mailboxes')
            elif filter_type == FilterType.DIRECTION:
                current_filters['direction'] = st.session_state.get('filter_direction', 'Tous')
            elif filter_type == FilterType.SENDER:
                current_filters['sender'] = st.session_state.get('filter_sender', 'Tous')
            elif filter_type == FilterType.RECIPIENT:
                current_filters['recipient'] = st.session_state.get('filter_recipient', 'Tous')
            elif filter_type == FilterType.HAS_ATTACHMENTS:
                current_filters['has_attachments'] = st.session_state.get('filter_has_attachments', False)
            elif filter_type == FilterType.MAILING_LIST:
                current_filters['mailing_list'] = st.session_state.get('filter_mailing_list', 'Tous')
            elif filter_type == FilterType.CONTACT_FILTER:
                current_filters['contact_filter'] = st.session_state.get('filter_contact', None)
        
        return current_filters
    
    def count_active_filters(self, current_filters: Dict[str, Any]) -> int:
        """Count how many filters are currently active"""
        active_count = 0
        
        for key, value in current_filters.items():
            if key == 'date_range' and value:
                active_count += 1
            elif key == 'mailbox' and value != 'All Mailboxes':
                active_count += 1
            elif key in ['direction', 'sender', 'recipient', 'mailing_list'] and value != 'Tous':
                active_count += 1
            elif key == 'has_attachments' and value:
                active_count += 1
            elif key == 'contact_filter' and value:
                active_count += 1
                
        return active_count


def create_hover_filter_menu(filter_manager: FilterManager, page_name: str, emails_df: pd.DataFrame = None) -> Tuple[Dict[str, Any], bool]:
    """
    Create a hover-based filter menu for the specified page
    
    Returns:
        Tuple[Dict[str, Any], bool]: (filters_dict, filters_changed)
    """
    
    # Check if filters should be shown for this page
    if not filter_manager.config_manager.should_show_filter_bar(page_name):
        return {}, False
    
    # Get current filter values
    current_filters = filter_manager.get_current_filters(page_name)
    active_count = filter_manager.count_active_filters(current_filters)
    
    # Create CSS
    css = filter_manager.create_hover_menu_css()
    st.markdown(css, unsafe_allow_html=True)
    
    # Create the filter menu HTML structure
    filter_badge = f" ({active_count})" if active_count > 0 else ""
    
    menu_html = f"""
    <div class="filter-menu-container">
        <div class="filter-menu-trigger">
            <span>🔧</span>
            <span>Filtres{filter_badge}</span>
            <span style="margin-left: 4px;">▼</span>
        </div>
        <div class="filter-menu-dropdown">
            <div class="filter-menu-header">
                <h3 class="filter-menu-title">
                    <span>⚙️</span>
                    Filtres - {page_name}
                </h3>
            </div>
            <div class="filter-menu-content">
                <div id="streamlit-filter-content">
                    <!-- Streamlit components will be inserted here -->
                </div>
            </div>
        </div>
    </div>
    """
    
    # Display the menu structure
    st.markdown(menu_html, unsafe_allow_html=True)
    
    # Create a container for the actual Streamlit filter components
    with st.container():
        st.markdown("### 🔧 Filtres")
        
        filters_changed = False
        new_filters = {}
        
        enabled_filters = filter_manager.config_manager.get_enabled_filters(page_name)
        
        # Create sections for different filter types
        if any(f.filter_type in [FilterType.DATE_RANGE, FilterType.MAILBOX_SELECTION] for f in enabled_filters):
            st.markdown("##### 📅 Données de base")
            
            # Date range filter
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.DATE_RANGE):
                # Get date range from data if available
                if emails_df is not None and not emails_df.empty and 'date' in emails_df.columns:
                    min_date = pd.to_datetime(emails_df['date']).min().date()
                    max_date = pd.to_datetime(emails_df['date']).max().date()
                else:
                    min_date = pd.to_datetime("2020-01-01").date()
                    max_date = pd.to_datetime("2025-12-31").date()
                
                new_date_range = st.date_input(
                    "Période",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="filter_date_range_input"
                )
                
                if new_date_range != current_filters.get('date_range'):
                    filters_changed = True
                    st.session_state['filter_date_range'] = new_date_range
                
                new_filters['date_range'] = new_date_range
            
            # Mailbox selection
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.MAILBOX_SELECTION):
                new_mailbox = st.selectbox(
                    "Boîte mail",
                    options=filter_manager.mailbox_options,
                    index=filter_manager.mailbox_options.index(current_filters.get('mailbox', 'All Mailboxes')),
                    key="filter_mailbox_input"
                )
                
                if new_mailbox != current_filters.get('mailbox'):
                    filters_changed = True
                    st.session_state['selected_mailbox'] = new_mailbox
                
                new_filters['mailbox'] = new_mailbox
        
        # Content filters
        content_filters = [FilterType.DIRECTION, FilterType.SENDER, FilterType.RECIPIENT]
        if any(f.filter_type in content_filters for f in enabled_filters):
            st.markdown("##### 📧 Contenu des emails")
            
            # Direction filter
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.DIRECTION):
                direction_options = ["Tous", "Envoyés", "Reçus"]
                new_direction = st.selectbox(
                    "Direction",
                    options=direction_options,
                    index=direction_options.index(current_filters.get('direction', 'Tous')),
                    key="filter_direction_input"
                )
                
                if new_direction != current_filters.get('direction'):
                    filters_changed = True
                    st.session_state['filter_direction'] = new_direction
                
                new_filters['direction'] = new_direction
            
            # Sender filter
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.SENDER):
                # Get unique senders if emails_df is available
                sender_options = ["Tous"]
                if emails_df is not None and not emails_df.empty and 'from' in emails_df.columns:
                    unique_senders = sorted(emails_df['from'].dropna().unique().tolist())
                    sender_options.extend(unique_senders)
                
                current_sender = current_filters.get('sender', 'Tous')
                if current_sender not in sender_options:
                    current_sender = 'Tous'
                
                new_sender = st.selectbox(
                    "Expéditeur",
                    options=sender_options,
                    index=sender_options.index(current_sender),
                    key="filter_sender_input"
                )
                
                if new_sender != current_filters.get('sender'):
                    filters_changed = True
                    st.session_state['filter_sender'] = new_sender
                
                new_filters['sender'] = new_sender
            
            # Recipient filter
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.RECIPIENT):
                recipient_options = ["Tous"]
                if emails_df is not None and not emails_df.empty and 'recipient_email' in emails_df.columns:
                    unique_recipients = set()
                    for recipients in emails_df["recipient_email"].dropna():
                        if isinstance(recipients, str):
                            for recipient in recipients.split(','):
                                recipient = recipient.strip()
                                if recipient:
                                    unique_recipients.add(recipient)
                    recipient_options.extend(sorted(list(unique_recipients)))
                
                current_recipient = current_filters.get('recipient', 'Tous')
                if current_recipient not in recipient_options:
                    current_recipient = 'Tous'
                
                new_recipient = st.selectbox(
                    "Destinataire",
                    options=recipient_options,
                    index=recipient_options.index(current_recipient),
                    key="filter_recipient_input"
                )
                
                if new_recipient != current_filters.get('recipient'):
                    filters_changed = True
                    st.session_state['filter_recipient'] = new_recipient
                
                new_filters['recipient'] = new_recipient
        
        # Special filters
        special_filters = [FilterType.HAS_ATTACHMENTS, FilterType.MAILING_LIST, FilterType.CONTACT_FILTER]
        if any(f.filter_type in special_filters for f in enabled_filters):
            st.markdown("##### 🔍 Filtres spéciaux")
            
            # Has attachments filter
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.HAS_ATTACHMENTS):
                new_has_attachments = st.checkbox(
                    "Avec pièces jointes uniquement",
                    value=current_filters.get('has_attachments', False),
                    key="filter_attachments_input"
                )
                
                if new_has_attachments != current_filters.get('has_attachments'):
                    filters_changed = True
                    st.session_state['filter_has_attachments'] = new_has_attachments
                
                new_filters['has_attachments'] = new_has_attachments
            
            # Mailing list filter
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.MAILING_LIST):
                mailing_list_options = ["Tous", "Listes de diffusion", "Emails individuels"]
                new_mailing_list = st.selectbox(
                    "Type d'email",
                    options=mailing_list_options,
                    index=mailing_list_options.index(current_filters.get('mailing_list', 'Tous')),
                    key="filter_mailing_list_input"
                )
                
                if new_mailing_list != current_filters.get('mailing_list'):
                    filters_changed = True
                    st.session_state['filter_mailing_list'] = new_mailing_list
                
                new_filters['mailing_list'] = new_mailing_list
            
            # Contact filter (for pages that support it)
            if filter_manager.config_manager.is_filter_enabled(page_name, FilterType.CONTACT_FILTER):
                current_contact = current_filters.get('contact_filter', '')
                new_contact = st.text_input(
                    "Filtrer par contact",
                    value=current_contact or '',
                    placeholder="Entrez une adresse email...",
                    key="filter_contact_input"
                )
                
                if new_contact != current_contact:
                    filters_changed = True
                    st.session_state['filter_contact'] = new_contact if new_contact else None
                
                new_filters['contact_filter'] = new_contact if new_contact else None
        
        # Clear filters button
        if active_count > 0:
            if st.button("🗑️ Effacer tous les filtres", key="clear_all_filters"):
                # Clear all filter values from session state
                filter_keys = [
                    'filter_date_range', 'selected_mailbox', 'filter_direction',
                    'filter_sender', 'filter_recipient', 'filter_has_attachments',
                    'filter_mailing_list', 'filter_contact'
                ]
                for key in filter_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                
                filters_changed = True
                st.rerun()
        
        # Filter status
        if active_count > 0:
            st.info(f"✅ {active_count} filtre(s) actif(s)")
        else:
            st.info("ℹ️ Aucun filtre actif")
    
    return new_filters, filters_changed
