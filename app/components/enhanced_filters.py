"""
Enhanced Filter Component

A new filter system that can be used as a dropdown menu on hover
instead of sidebar filters, with per-page configuration.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional


class FilterDropdown:
    """Creates a configurable filter dropdown menu"""
    
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
                "show_filters": True,  # Now has the filter menu
                "filters": ["date_range", "mailbox", "direction", "sender", "recipient", "has_attachments"]
            },
            "Chat + RAG": {
                "show_filters": False,  # No filters for chat
                "filters": []
            },
            "Colbert RAG": {
                "show_filters": False,  # No filters for chat
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
    
    def render_filter_menu(self, 
                          emails_df: Optional[pd.DataFrame] = None, 
                          mailbox_options: List[str] = None,
                          email_filters = None) -> Tuple[Dict[str, Any], bool]:
        """
        Render the filter dropdown menu
        
        Returns:
            Tuple[Dict[str, Any], bool]: (applied_filters, filters_changed)
        """
        
        if not self.should_show_filters():
            return {}, False
        
        # Load CSS
        self._inject_filter_css()
        
        # Count active filters
        active_filters = self._count_active_filters()
        
        # Create the hover menu HTML
        self._render_hover_menu_html(active_filters)
        
        # Create the actual filter controls in a collapsible section
        filters_changed = False
        applied_filters = {}
        
        with st.expander(f"🔧 Filtres {self.page_name} ({active_filters} actifs)", expanded=False):
            
            enabled_filters = self.filter_configs.get("filters", [])
            
            # Basic filters section
            if any(f in enabled_filters for f in ["date_range", "mailbox"]):
                st.markdown("##### 📅 Données de base")
                
                # Date range filter
                if "date_range" in enabled_filters:
                    date_range, date_changed = self._render_date_range_filter(emails_df)
                    applied_filters["date_range"] = date_range
                    if date_changed:
                        filters_changed = True
                
                # Mailbox filter
                if "mailbox" in enabled_filters and mailbox_options:
                    mailbox, mailbox_changed = self._render_mailbox_filter(mailbox_options)
                    applied_filters["mailbox"] = mailbox
                    if mailbox_changed:
                        filters_changed = True
            
            # Content filters section
            if any(f in enabled_filters for f in ["direction", "sender", "recipient"]):
                st.markdown("##### 📧 Contenu des emails")
                
                # Direction filter
                if "direction" in enabled_filters:
                    direction, direction_changed = self._render_direction_filter()
                    applied_filters["direction"] = direction
                    if direction_changed:
                        filters_changed = True
                
                # Sender filter
                if "sender" in enabled_filters:
                    sender, sender_changed = self._render_sender_filter(emails_df)
                    applied_filters["sender"] = sender
                    if sender_changed:
                        filters_changed = True
                
                # Recipient filter
                if "recipient" in enabled_filters:
                    recipient, recipient_changed = self._render_recipient_filter(emails_df)
                    applied_filters["recipient"] = recipient
                    if recipient_changed:
                        filters_changed = True
            
            # Special filters section
            if any(f in enabled_filters for f in ["has_attachments", "contact_filter"]):
                st.markdown("##### 🔍 Filtres spéciaux")
                
                # Has attachments filter
                if "has_attachments" in enabled_filters:
                    has_attachments, attachments_changed = self._render_attachments_filter()
                    applied_filters["has_attachments"] = has_attachments
                    if attachments_changed:
                        filters_changed = True
                
                # Contact filter
                if "contact_filter" in enabled_filters:
                    contact_filter, contact_changed = self._render_contact_filter()
                    applied_filters["contact_filter"] = contact_filter
                    if contact_changed:
                        filters_changed = True
            
            # Clear filters button
            if active_filters > 0:
                if st.button("🗑️ Effacer tous les filtres", key=f"clear_filters_{self.page_name}"):
                    self._clear_all_filters()
                    filters_changed = True
                    st.rerun()
            
            # Show filter status
            if active_filters > 0:
                st.success(f"✅ {active_filters} filtre(s) actif(s)")
            else:
                st.info("ℹ️ Aucun filtre actif")
        
        return applied_filters, filters_changed
    
    def _inject_filter_css(self):
        """Load CSS from external file"""
        try:
            from .filter_styles import get_filter_css
            css = get_filter_css()
            st.markdown(css, unsafe_allow_html=True)
        except ImportError:
            # Fallback basic CSS
            basic_css = """
            <style>
            .filter-hover-menu {
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
            }
            .filter-trigger {
                background: #ff6b6b;
                color: white;
                padding: 12px 20px;
                border-radius: 25px;
                cursor: pointer;
            }
            </style>
            """
            st.markdown(basic_css, unsafe_allow_html=True)
    
    def _render_hover_menu_html(self, active_count: int):
        """Render the hover menu HTML trigger"""
        badge = f" ({active_count})" if active_count > 0 else ""
        
        hover_html = f"""
        <div class="filter-hover-menu">
            <div class="filter-trigger" onclick="document.querySelector('details[data-testid=\"expander\"]').click()">
                <span>🔧</span>
                <span>Filtres{badge}</span>
                <span style="margin-left: 4px;">▼</span>
            </div>
        </div>
        """
        
        st.markdown(hover_html, unsafe_allow_html=True)
    
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
    
    def _render_date_range_filter(self, emails_df: Optional[pd.DataFrame]) -> Tuple[Any, bool]:
        """Render date range filter"""
        if emails_df is not None and not emails_df.empty and 'date' in emails_df.columns:
            min_date = pd.to_datetime(emails_df['date']).min().date()
            max_date = pd.to_datetime(emails_df['date']).max().date()
        else:
            min_date = pd.to_datetime("2020-01-01").date()
            max_date = pd.to_datetime("2025-12-31").date()
        
        current_value = st.session_state.get(f"filter_date_range_{self.page_name}", (min_date, max_date))
        
        new_value = st.date_input(
            "Période",
            value=current_value,
            min_value=min_date,
            max_value=max_date,
            key=f"filter_date_range_{self.page_name}"
        )
        
        changed = new_value != current_value
        return new_value, changed
    
    def _render_mailbox_filter(self, mailbox_options: List[str]) -> Tuple[str, bool]:
        """Render mailbox selection filter"""
        current_value = st.session_state.get(f"filter_mailbox_{self.page_name}", "All Mailboxes")
        
        if current_value not in mailbox_options:
            current_value = "All Mailboxes"
        
        new_value = st.selectbox(
            "Boîte mail",
            options=mailbox_options,
            index=mailbox_options.index(current_value),
            key=f"filter_mailbox_{self.page_name}"
        )
        
        changed = new_value != current_value
        return new_value, changed
    
    def _render_direction_filter(self) -> Tuple[str, bool]:
        """Render direction filter"""
        options = ["Tous", "Envoyés", "Reçus"]
        current_value = st.session_state.get(f"filter_direction_{self.page_name}", "Tous")
        
        new_value = st.selectbox(
            "Direction",
            options=options,
            index=options.index(current_value),
            key=f"filter_direction_{self.page_name}"
        )
        
        changed = new_value != current_value
        return new_value, changed
    
    def _render_sender_filter(self, emails_df: Optional[pd.DataFrame]) -> Tuple[str, bool]:
        """Render sender filter"""
        options = ["Tous"]
        if emails_df is not None and not emails_df.empty and 'from' in emails_df.columns:
            unique_senders = sorted(emails_df['from'].dropna().unique().tolist())
            options.extend(unique_senders)
        
        current_value = st.session_state.get(f"filter_sender_{self.page_name}", "Tous")
        if current_value not in options:
            current_value = "Tous"
        
        new_value = st.selectbox(
            "Expéditeur",
            options=options,
            index=options.index(current_value),
            key=f"filter_sender_{self.page_name}"
        )
        
        changed = new_value != current_value
        return new_value, changed
    
    def _render_recipient_filter(self, emails_df: Optional[pd.DataFrame]) -> Tuple[str, bool]:
        """Render recipient filter"""
        options = ["Tous"]
        if emails_df is not None and not emails_df.empty and 'recipient_email' in emails_df.columns:
            unique_recipients = set()
            for recipients in emails_df["recipient_email"].dropna():
                if isinstance(recipients, str):
                    for recipient in recipients.split(','):
                        recipient = recipient.strip()
                        if recipient:
                            unique_recipients.add(recipient)
            options.extend(sorted(list(unique_recipients)))
        
        current_value = st.session_state.get(f"filter_recipient_{self.page_name}", "Tous")
        if current_value not in options:
            current_value = "Tous"
        
        new_value = st.selectbox(
            "Destinataire",
            options=options,
            index=options.index(current_value),
            key=f"filter_recipient_{self.page_name}"
        )
        
        changed = new_value != current_value
        return new_value, changed
    
    def _render_attachments_filter(self) -> Tuple[bool, bool]:
        """Render has attachments filter"""
        current_value = st.session_state.get(f"filter_has_attachments_{self.page_name}", False)
        
        new_value = st.checkbox(
            "Avec pièces jointes uniquement",
            value=current_value,
            key=f"filter_has_attachments_{self.page_name}"
        )
        
        changed = new_value != current_value
        return new_value, changed
    
    def _render_contact_filter(self) -> Tuple[Optional[str], bool]:
        """Render contact filter"""
        current_value = st.session_state.get(f"filter_contact_{self.page_name}", "")
        
        new_value = st.text_input(
            "Filtrer par contact",
            value=current_value,
            placeholder="Entrez une adresse email...",
            key=f"filter_contact_{self.page_name}"
        )
        
        changed = new_value != current_value
        result = new_value if new_value else None
        return result, changed
    
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
    
    def get_applied_filters_dict(self) -> Dict[str, Any]:
        """Get currently applied filters as a dictionary for data filtering"""
        filters = {}
        
        # Date range
        date_range = st.session_state.get(f"filter_date_range_{self.page_name}")
        if date_range:
            filters['date_range'] = date_range
        
        # Mailbox
        mailbox = st.session_state.get(f"filter_mailbox_{self.page_name}", "All Mailboxes")
        if mailbox != "All Mailboxes":
            filters['mailbox'] = mailbox
        
        # Direction
        direction = st.session_state.get(f"filter_direction_{self.page_name}", "Tous")
        if direction != "Tous":
            direction_map = {"Envoyés": "sent", "Reçus": "received"}
            filters['direction'] = direction_map.get(direction, direction)
        
        # Sender
        sender = st.session_state.get(f"filter_sender_{self.page_name}", "Tous")
        if sender != "Tous":
            filters['sender'] = sender
        
        # Recipient
        recipient = st.session_state.get(f"filter_recipient_{self.page_name}", "Tous")
        if recipient != "Tous":
            filters['recipient'] = recipient
        
        # Has attachments
        has_attachments = st.session_state.get(f"filter_has_attachments_{self.page_name}", False)
        if has_attachments:
            filters['has_attachments'] = True
        
        # Contact filter
        contact = st.session_state.get(f"filter_contact_{self.page_name}")
        if contact:
            filters['contact_filter'] = contact
        
        return filters


def create_page_filters(page_name: str, 
                       emails_df: Optional[pd.DataFrame] = None,
                       mailbox_options: List[str] = None,
                       email_filters = None) -> Tuple[Dict[str, Any], bool]:
    """
    Convenience function to create and render page filters
    
    Args:
        page_name: Name of the current page
        emails_df: DataFrame containing email data (optional)
        mailbox_options: List of available mailbox options
        email_filters: Email filters object (for compatibility)
    
    Returns:
        Tuple[Dict[str, Any], bool]: (applied_filters, filters_changed)
    """
    filter_dropdown = FilterDropdown(page_name)
    
    if not filter_dropdown.should_show_filters():
        return {}, False
    
    return filter_dropdown.render_filter_menu(
        emails_df=emails_df,
        mailbox_options=mailbox_options,
        email_filters=email_filters
    )
