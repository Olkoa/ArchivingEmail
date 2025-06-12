"""
Dropdown Filter Component

Creates a true dropdown menu that replaces the expander.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import streamlit.components.v1 as components


class DropdownFilterMenu:
    """Creates a dropdown filter menu that replaces expanders"""
    
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
        Render the dropdown filter menu
        
        Returns:
            Tuple[Dict[str, Any], bool]: (applied_filters, filters_changed)
        """
        
        if not self.should_show_filters():
            return {}, False
        
        # Count active filters
        active_count = self._count_active_filters()
        
        # Create the dropdown menu HTML with embedded form controls
        self._render_dropdown_html(active_count, emails_df, mailbox_options)
        
        # Return current filter state
        applied_filters = self._get_current_filters()
        return applied_filters, False  # We'll handle changes via the HTML form
    
    def _render_dropdown_html(self, active_count: int, emails_df: Optional[pd.DataFrame], mailbox_options: List[str]):
        """Render the complete dropdown menu with HTML form controls"""
        
        # Load CSS and JS
        from .advanced_filter_styles import get_advanced_filter_css, get_filter_js
        css = get_advanced_filter_css()
        js = get_filter_js()
        
        st.markdown(css, unsafe_allow_html=True)
        
        # Create filter options
        enabled_filters = self.filter_configs.get("filters", [])
        current_filters = self._get_current_filters()
        
        # Build form controls HTML
        form_html = self._build_form_html(enabled_filters, current_filters, emails_df, mailbox_options)
        
        badge = f" ({active_count})" if active_count > 0 else ""
        
        dropdown_html = f"""
        <div class="filter-dropdown-overlay"></div>
        <div class="filter-dropdown-container">
            <div class="filter-dropdown-trigger">
                <span>🔧</span>
                <span>Filtres{badge}</span>
                <span style="margin-left: 4px;">▼</span>
            </div>
            <div class="filter-dropdown-menu">
                <div class="filter-dropdown-header">
                    <div class="filter-dropdown-title">
                        <span>⚙️</span>
                        <span>Filtres - {self.page_name}</span>
                    </div>
                    <button class="filter-dropdown-close" type="button">×</button>
                </div>
                <div class="filter-dropdown-content">
                    {form_html}
                    {self._build_status_html(active_count)}
                </div>
            </div>
        </div>
        {js}
        """
        
        st.markdown(dropdown_html, unsafe_allow_html=True)
    
    def _build_form_html(self, enabled_filters: List[str], current_filters: Dict, 
                        emails_df: Optional[pd.DataFrame], mailbox_options: List[str]) -> str:
        """Build the HTML form controls for filters"""
        
        sections = []
        
        # Basic filters section
        if any(f in enabled_filters for f in ["date_range", "mailbox"]):
            section_html = '<div class="filter-section"><div class="filter-section-title">📅 Données de base</div>'
            
            if "mailbox" in enabled_filters and mailbox_options:
                current_mailbox = current_filters.get('mailbox', 'All Mailboxes')
                options_html = ''.join([
                    f'<option value="{option}" {"selected" if option == current_mailbox else ""}>{option}</option>'
                    for option in mailbox_options
                ])
                section_html += f'''
                <div class="filter-control">
                    <label>Boîte mail</label>
                    <select id="filter_mailbox_{self.page_name}" onchange="updateFilter('mailbox', this.value)">
                        {options_html}
                    </select>
                </div>
                '''
            
            section_html += '</div>'
            sections.append(section_html)
        
        # Content filters section
        if any(f in enabled_filters for f in ["direction", "sender", "recipient"]):
            section_html = '<div class="filter-section"><div class="filter-section-title">📧 Contenu des emails</div>'
            
            if "direction" in enabled_filters:
                current_direction = current_filters.get('direction', 'Tous')
                direction_options = ["Tous", "Envoyés", "Reçus"]
                options_html = ''.join([
                    f'<option value="{option}" {"selected" if option == current_direction else ""}>{option}</option>'
                    for option in direction_options
                ])
                section_html += f'''
                <div class="filter-control">
                    <label>Direction</label>
                    <select id="filter_direction_{self.page_name}" onchange="updateFilter('direction', this.value)">
                        {options_html}
                    </select>
                </div>
                '''
            
            if "sender" in enabled_filters:
                sender_options = ["Tous"]
                if emails_df is not None and not emails_df.empty and 'from' in emails_df.columns:
                    unique_senders = sorted(emails_df['from'].dropna().unique().tolist())
                    sender_options.extend(unique_senders[:20])  # Limit for performance
                
                current_sender = current_filters.get('sender', 'Tous')
                options_html = ''.join([
                    f'<option value="{option}" {"selected" if option == current_sender else ""}>{option}</option>'
                    for option in sender_options
                ])
                section_html += f'''
                <div class="filter-control">
                    <label>Expéditeur</label>
                    <select id="filter_sender_{self.page_name}" onchange="updateFilter('sender', this.value)">
                        {options_html}
                    </select>
                </div>
                '''
            
            section_html += '</div>'
            sections.append(section_html)
        
        # Special filters section
        if any(f in enabled_filters for f in ["has_attachments", "contact_filter"]):
            section_html = '<div class="filter-section"><div class="filter-section-title">🔍 Filtres spéciaux</div>'
            
            if "has_attachments" in enabled_filters:
                current_attachments = current_filters.get('has_attachments', False)
                checked = 'checked' if current_attachments else ''
                section_html += f'''
                <div class="filter-control">
                    <label>
                        <input type="checkbox" id="filter_attachments_{self.page_name}" 
                               {checked} onchange="updateFilter('has_attachments', this.checked)">
                        Avec pièces jointes uniquement
                    </label>
                </div>
                '''
            
            if "contact_filter" in enabled_filters:
                current_contact = current_filters.get('contact_filter', '')
                section_html += f'''
                <div class="filter-control">
                    <label>Filtrer par contact</label>
                    <input type="text" id="filter_contact_{self.page_name}" 
                           value="{current_contact}" placeholder="Entrez une adresse email..."
                           onchange="updateFilter('contact_filter', this.value)">
                </div>
                '''
            
            section_html += '</div>'
            sections.append(section_html)
        
        # Add clear filters button if there are active filters
        if self._count_active_filters() > 0:
            sections.append('''
            <button class="clear-filters-btn" onclick="clearAllFilters()">
                🗑️ Effacer tous les filtres
            </button>
            ''')
        
        # Add JavaScript for filter updates
        js_functions = f'''
        <script>
        function updateFilter(filterType, value) {{
            // Store filter in sessionStorage for Streamlit to pick up
            const key = `filter_${{filterType}}_{self.page_name}`;
            if (value === 'Tous' || value === '' || value === false) {{
                sessionStorage.removeItem(key);
            }} else {{
                sessionStorage.setItem(key, JSON.stringify(value));
            }}
            
            // Trigger Streamlit rerun
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: {{ filterType: filterType, value: value }}
            }}, '*');
        }}
        
        function clearAllFilters() {{
            const keys = [
                'filter_date_range_{self.page_name}',
                'filter_mailbox_{self.page_name}',
                'filter_direction_{self.page_name}',
                'filter_sender_{self.page_name}',
                'filter_recipient_{self.page_name}',
                'filter_has_attachments_{self.page_name}',
                'filter_contact_{self.page_name}'
            ];
            
            keys.forEach(key => sessionStorage.removeItem(key));
            
            // Trigger Streamlit rerun
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: {{ action: 'clear_all' }}
            }}, '*');
        }}
        </script>
        '''
        
        return ''.join(sections) + js_functions
    
    def _build_status_html(self, active_count: int) -> str:
        """Build the status section HTML"""
        if active_count > 0:
            return f'''
            <div class="filter-status">
                ✅ {active_count} filtre(s) actif(s)
            </div>
            '''
        else:
            return '''
            <div class="filter-status" style="background: #f8f9fa; color: #6c757d; border-left-color: #dee2e6;">
                ℹ️ Aucun filtre actif
            </div>
            '''
    
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


def create_dropdown_filters(page_name: str, 
                           emails_df: Optional[pd.DataFrame] = None,
                           mailbox_options: List[str] = None,
                           email_filters = None) -> Tuple[Dict[str, Any], bool]:
    """
    Create dropdown filters instead of expander
    
    Args:
        page_name: Name of the current page
        emails_df: DataFrame containing email data (optional)
        mailbox_options: List of available mailbox options
        email_filters: Email filters object (for compatibility)
    
    Returns:
        Tuple[Dict[str, Any], bool]: (applied_filters, filters_changed)
    """
    filter_menu = DropdownFilterMenu(page_name)
    
    if not filter_menu.should_show_filters():
        return {}, False
    
    return filter_menu.render_dropdown_menu(
        emails_df=emails_df,
        mailbox_options=mailbox_options,
        email_filters=email_filters
    )
