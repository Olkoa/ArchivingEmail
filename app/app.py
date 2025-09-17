"""
Okloa - Main Streamlit Application

This is the entry point for the Okloa application, providing an interface
for exploring and analyzing archived email data.
"""

import streamlit as st
import pandas as pd
import os
import sys
import time
from bs4 import BeautifulSoup
import json

import plotly.express as px
from collections import Counter

# imports for graph
import email
from email.policy import default
import streamlit.components.v1 as components
import duckdb
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# Import project constants and elasticsearch enhanced search functionality
from constants import EMAIL_DISPLAY_TYPE, SIDEBAR_STATE, ACTIVE_PROJECT
from src.features.elasticsearch_enhanced import enhanced_search_emails
from src.features.decodeml import decode_unicode_escape , getBody
from components.logins import make_hashed_password, verify_password, add_user, initialize_users_db

# Set page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Okloa - Email Archive Analytics",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state=SIDEBAR_STATE,
)

# Import application components - using relative import
sys.path.append(os.path.dirname(__file__))
from components.email_viewer import create_email_table_with_viewer, apply_contact_filter, clear_email_selection
from components.working_dropdown_filters import create_working_dropdown_filters

from src.data.loading import load_mailboxes
from src.data.email_analyzer import EmailAnalyzer
from src.features.embeddings import generate_embeddings
from src.visualization.email_network import create_network_graph
from src.visualization.timeline import create_timeline
from src.rag.initialization import initialize_rag_system
from src.rag.retrieval import get_rag_answer
from src.features.search import search_emails
from src.filters.email_filters import EmailFilters, create_sidebar_filters

print("app getting started...")

# Initialize user session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "users_db" not in st.session_state:
    st.session_state.users_db = initialize_users_db()

# Login form
def show_login_form():
    st.title("Okloa - Email Archive Analytics")
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if verify_password(username, password, st.session_state.users_db):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    # Display demo credentials for testing
    # st.info("""Demo credentials:\n- Username: admin, Password: admin123\n- Username: user, Password: user123""")

    # # Add "Admin Panel" section for creating new users
    # st.subheader("Admin Panel")
    # with st.expander("Create New User"):
    #     with st.form("create_user_form"):
    #         admin_username = st.text_input("Admin Username")
    #         admin_password = st.text_input("Admin Password", type="password")
    #         new_username = st.text_input("New Username")
    #         new_password = st.text_input("New Password", type="password")
    #         confirm_password = st.text_input("Confirm Password", type="password")

    #         create_button = st.form_submit_button("Create User")

    #         if create_button:
    #             # Verify admin credentials
    #             if verify_password(admin_username, admin_password, st.session_state.users_db):
    #                 # Check if passwords match
    #                 if new_password == confirm_password:
    #                     # Add new user
    #                     st.session_state.users_db = add_user(new_username, new_password)
    #                     st.success(f"User '{new_username}' created successfully!")
    #                 else:
    #                     st.error("Passwords do not match!")
    #             else:
    #                 st.error("Invalid admin credentials")

# Page configuration is already set at the top of the file

# Check if authenticated
if not st.session_state.authenticated:
    show_login_form()
else:
    # Application title and description
    # st.title(f"Okloa - Email Archive Analytics (Logged in as: {st.session_state.username})")
    # st.markdown("""
    # Welcome to Okloa, a platform for exploring and analyzing archived email data.
    # This application helps you visualize email communication patterns, search through
    # the corpus, and extract insights using advanced natural language processing techniques.
    # """)
    st.title("Dashboard")

    # Application title and description
    # st.title("Okloa - Email Archive Analytics")
    # st.markdown("""
    #     Welcome to Okloa, a platform for exploring and analyzing archived email data.
    #     This application helps you visualize email communication patterns, search through
    #     the corpus, and extract insights using advanced natural language processing techniques.
    # """)

    # Sidebar for navigation and controls - simplified
    st.sidebar.title("Navigation")

    # Organize pages into categories for better navigation
    navigation_categories = {
        "Overview": ["Dashboard"],
        "AI Assistants": ["Chat + RAG"], # "Colbert RAG"
        "Topic": ["Topic"],
        "Graph": ["Graph"],
        "Graph_Br": ["Graph_Br"],
        "Visualization": ["Structure de la boîte mail"],
        "Search": ["Recherche Sémantique"]
        # "Exploration": ["Email Explorer"],
    }

    # Display navigation categories
    selected_category = st.sidebar.radio("Category", list(navigation_categories.keys()))

    # Display pages within the selected category
    page = st.sidebar.radio(
        "Select a page:",
        navigation_categories[selected_category]
    )

    # Essential data loading - keep mailbox selection in sidebar for now
    st.sidebar.title("Données essentielles")

    with open(os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'project_config_file.json'), 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    mailboxs_names = list(json_data[ACTIVE_PROJECT]["mailboxs"].keys())
    mailbox_options = ["All Mailboxes"] + mailboxs_names
    selected_mailbox = st.sidebar.selectbox("Select Mailbox:", mailbox_options)

    # Store selected mailbox in session state for other pages to access
    st.session_state.selected_mailbox = selected_mailbox

    # Function to get date range from data
    @st.cache_data
    def get_date_range_from_data(mailbox_selection):
        """Get the min and max dates from the loaded data to set dynamic date range"""
        try:
            # Load a small sample to get date range without the full dataset
            db_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, f"{ACTIVE_PROJECT}.duckdb")
            analyzer = EmailAnalyzer(db_path=db_path)

            # Get min and max dates from database
            conn = analyzer.connect()
            query = """
            SELECT
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date
            FROM receiver_emails
            """

            # Add mailbox filter if specified
            if mailbox_selection != "All Mailboxes":
                query += f" WHERE folder = '{mailbox_selection}'"

            result = conn.execute(query).fetchone()

            if result and result[0] and result[1]:
                min_date = pd.to_datetime(result[0]).date()
                max_date = pd.to_datetime(result[1]).date()
                return min_date, max_date
            else:
                # Fallback to default dates if no data
                return pd.to_datetime("2020-01-01").date(), pd.to_datetime("2025-12-31").date()

        except Exception as e:
            print(f"Error getting date range: {e}")
            # Fallback to default dates
            return pd.to_datetime("2020-01-01").date(), pd.to_datetime("2025-12-31").date()

    # Initialize EmailFilters
    db_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, f"{ACTIVE_PROJECT}.duckdb")
    email_filters = EmailFilters(db_path)

    # Legacy filters for pages not yet converted - moved out of sidebar
    # Only keep essential ones in a collapsible section
    if page in ["Chat", "Colbert RAG", "Structure de la boîte mail"]:
        with st.sidebar.expander("Filtres hérités", expanded=False):
            st.markdown("*Filtres pour pages non converties*")
            # Get dynamic date range
            min_date, max_date = get_date_range_from_data(selected_mailbox)

            # Timeframe selection
            date_range = st.date_input(
                "Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            # Additional filters
            additional_filters = create_sidebar_filters(email_filters, selected_mailbox)
    else:
        # For pages using the new filter system, just get defaults
        min_date, max_date = get_date_range_from_data(selected_mailbox)
        date_range = (min_date, max_date)
        additional_filters = {}


    # Sidebar for logging out
    st.sidebar.title("Connexion")

    # Add logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    # Function to apply date range filter to dataframe
    def apply_date_filter(df, date_range):
        """Apply date range filter to a dataframe"""
        if df.empty:
            return df

        # Ensure date column exists and is in datetime format
        if 'date' not in df.columns:
            return df

        # Convert date column to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Handle different date_range formats
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        elif isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range[0], date_range[1]
        else:
            return df  # No valid date range provided

        # Convert dates to pandas Timestamp for comparison
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # End of day

        # Apply filter
        original_count = len(df)
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        # Store filter info in session state for display
        st.session_state.filter_info = {
            'original_count': original_count,
            'filtered_count': len(filtered_df),
            'start_date': start_date.date(),
            'end_date': end_date.date()
        }

        return filtered_df

    def parse_search_query(search_term: str):
        """Parse search query to extract from:, to:, and general text search."""
        if not search_term:
            return None, None, None

        # Initialize variables
        from_filter = None
        to_filter = None
        text_search = []

        # Split by spaces and process each part
        parts = search_term.split()

        for part in parts:
            if part.lower().startswith('from:'):
                from_filter = part[5:].strip('"\'')
            elif part.lower().startswith('to:'):
                to_filter = part[3:].strip('"\'')
            else:
                text_search.append(part)

        # Join remaining text for general search
        general_text = ' '.join(text_search) if text_search else None

        return from_filter, to_filter, general_text

    def show_df_table(df:pd.DataFrame, key_prefix: str, filter_status: bool = True):
        # Use the provided dataframe (which may already be contact-filtered)
        emails_df = df

        # Email list with advanced search filter
        search_term = st.text_input(
            "Search in emails:",
            placeholder='Examples: "projet" or from:john@example.com or to:marie@company.fr or from:sender@domain.com to:recipient@domain.com meeting'
        )

        if search_term:
            # Parse the search query
            from_filter, to_filter, general_text = parse_search_query(search_term)

            # Start with all emails
            filtered_df = emails_df.copy()

            # Apply from filter if specified
            if from_filter:
                filtered_df = filtered_df[
                    filtered_df["from"].str.contains(from_filter, case=False, na=False)
                ]

            # Apply to filter if specified
            if to_filter:
                filtered_df = filtered_df[
                    filtered_df["recipient_email"].str.contains(to_filter, case=False, na=False)
                ]

            # Apply general text search if specified
            if general_text:
                filtered_df = filtered_df[
                    filtered_df["subject"].str.contains(general_text, case=False, na=False) |
                    filtered_df["body"].str.contains(general_text, case=False, na=False)
                ]

            # Show what filters are active
            active_filters = []
            if from_filter:
                active_filters.append(f"**De:** `{from_filter}`")
            if to_filter:
                active_filters.append(f"**À:** `{to_filter}`")
            if general_text:
                active_filters.append(f"**Texte:** `{general_text}`")

            if active_filters:
                st.caption(f"🔍 Filtres actifs: {' • '.join(active_filters)} | {len(filtered_df)} résultats")
        else:
            filtered_df = emails_df

        # Display filtered emails with interactive viewer
        # st.write(f"Showing {len(filtered_df)} emails")
        create_email_table_with_viewer(filtered_df, key_prefix=key_prefix)

        if filter_status:
            # Show comprehensive filter status
            show_comprehensive_filter_status(additional_filters, email_filters)

    # Load data based on selection from DuckDB with enhanced filtering
    @st.cache_data
    def load_data_with_filters(mailbox_selection, additional_filters, use_agg_recipients=False):
        """Load and cache the selected mailbox data from DuckDB with additional filters applied at database level

        Args:
            mailbox_selection: The selected mailbox name
            additional_filters: Dictionary containing additional filter criteria
            use_agg_recipients: If True, uses get_app_dataframe_agg_recipients method
                               instead of get_app_DataFrame
        """
        try:
            db_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, f"{ACTIVE_PROJECT}.duckdb")
            analyzer = EmailAnalyzer(db_path=db_path)

            # Use the enhanced method that supports filters
            df = analyzer.get_app_dataframe_with_filters(
                mailbox=mailbox_selection,
                filters=additional_filters
            )

            if len(df) == 0:
                st.sidebar.warning("No emails found with the selected filters.")
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    "message_id", "date", "from", "recipient_email", "cc", "subject",
                    "body", "attachments", "has_attachments", "direction", "mailbox"
                ])

            return df
        except Exception as e:
            st.sidebar.error(f"Error loading data from DuckDB: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                "message_id", "date", "from", "recipient_email", "cc", "subject",
                "body", "attachments", "has_attachments", "direction", "mailbox"
            ])

    def show_filter_status():
        """Display information about the current date filter"""
        if 'filter_info' in st.session_state:
            info = st.session_state.filter_info
            filtered_count = info['filtered_count']
            original_count = info['original_count']
            start_date = info['start_date']
            end_date = info['end_date']

            if filtered_count < original_count:
                st.info(f"📅 Date filter active: Showing {filtered_count:,} of {original_count:,} emails (from {start_date} to {end_date})")
            else:
                st.info(f"📅 Showing all {original_count:,} emails (from {start_date} to {end_date})")


    # Function to display comprehensive filter status
    def show_comprehensive_filter_status(additional_filters, email_filters):
        """Display information about all active filters"""
        filter_messages = []

        # Date filter info
        if 'filter_info' in st.session_state:
            info = st.session_state.filter_info
            filtered_count = info['filtered_count']
            original_count = info['original_count']
            start_date = info['start_date']
            end_date = info['end_date']

            if filtered_count < original_count:
                filter_messages.append(f"📅 Date: {filtered_count:,} of {original_count:,} emails (from {start_date} to {end_date})")
            else:
                filter_messages.append(f"📅 Date: All {original_count:,} emails (from {start_date} to {end_date})")

        # Additional filters
        additional_filter_summary = email_filters.get_filter_summary(additional_filters)
        if additional_filter_summary != "No additional filters active":
            filter_messages.append("\n" + additional_filter_summary)

        # Display the combined filter status
        if filter_messages:
            st.info(" • ".join(filter_messages))
        else:
            st.info("📅 All emails shown with no filters applied")

    # Load data from mbox files based on selection
    @st.cache_data
    def load_data_from_mbox(mailbox_selection):
        """Load and cache the selected mailbox data from mbox files"""
        # Get the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        base_dir = os.path.join(project_root, 'data', 'raw')

        st.sidebar.write(f"Looking for mailboxes in: {base_dir}")

        try:
            if mailbox_selection == "All Mailboxes":
                df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"], base_dir=base_dir)
            else:
                # Extract the number from the selection
                mailbox_num = mailbox_selection.split()[-1]
                df = load_mailboxes([f"mailbox_{mailbox_num}"], base_dir=base_dir)

            if len(df) == 0:
                st.sidebar.warning("No emails found in the selected mailbox(es).")
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    "message_id", "date", "from", "recipient_email", "cc", "subject",
                    "body", "attachments", "has_attachments", "direction", "mailbox"
                ])

            return df
        except Exception as e:
            st.sidebar.error(f"Error loading mailboxes: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                "message_id", "date", "from", "recipient_email", "cc", "subject",
                "body", "attachments", "has_attachments", "direction", "mailbox"
            ])

    # Load data based on selection from DuckDB
    @st.cache_data
    def load_data(mailbox_selection, use_agg_recipients=False):
        """Load and cache the selected mailbox data from DuckDB

        Args:
            mailbox_selection: The selected mailbox name
            use_agg_recipients: If True, uses get_app_dataframe_agg_recipients method
                               instead of get_app_DataFrame
        """
        try:

            db_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, f"{ACTIVE_PROJECT}.duckdb")

            # Get data from DuckDB using EmailAnalyzer
            analyzer = EmailAnalyzer(db_path=db_path)

            if use_agg_recipients:
                df = analyzer.get_app_dataframe_agg_recipients()
                print("Using aggregated recipients method:", df.columns)
            else:
                df = analyzer.get_app_DataFrame()
                print("Using standard method:", df.columns)

            # Filter based on mailbox selection
            if mailbox_selection != "All Mailboxes":
                # Check which column name is available for filtering
                if 'mailbox_name' in df.columns:
                    df = df[df['mailbox_name'] == mailbox_selection]
                elif 'folder' in df.columns:
                    df = df[df['folder'] == mailbox_selection]

            if len(df) == 0:
                st.sidebar.warning("No emails found in the selected mailbox(es).")
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    "message_id", "date", "from", "recipient_email", "cc", "subject",
                    "body", "attachments", "has_attachments", "direction", "mailbox"
                ])

            return df
        except Exception as e:
            st.sidebar.error(f"Error loading data from DuckDB: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                "message_id", "date", "from", "recipient_email", "cc", "subject",
                "body", "attachments", "has_attachments", "direction", "mailbox"
            ])


    # Main content
    if page == "Dashboard":
        # Load data with working dropdown filters
        enhanced_filters, filters_changed = create_working_dropdown_filters(
            page_name="Dashboard",
            emails_df=None,  # Will be loaded after filters
            mailbox_options=mailbox_options,
            email_filters=email_filters
        )

        # Get filter values for data loading
        selected_mailbox_filter = enhanced_filters.get('mailbox', selected_mailbox)

        # Convert enhanced filters to the format expected by load_data_with_filters
        filter_dict = {}
        if enhanced_filters.get('direction'):
            filter_dict['direction'] = enhanced_filters['direction']
        if enhanced_filters.get('sender'):
            filter_dict['sender'] = enhanced_filters['sender']
        if enhanced_filters.get('recipient'):
            filter_dict['recipient'] = enhanced_filters['recipient']
        if enhanced_filters.get('has_attachments'):
            filter_dict['has_attachments'] = True

        emails_df = load_data_with_filters(selected_mailbox_filter, filter_dict, use_agg_recipients=True)

        # Apply date range filter if specified in enhanced filters
        if enhanced_filters.get('date_range'):
            emails_df = apply_date_filter(emails_df, enhanced_filters['date_range'])
        else:
            emails_df = apply_date_filter(emails_df, date_range)

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Emails", len(emails_df))

        with col2:
            sent_count = len(emails_df[emails_df["direction"] == "sent"])
            st.metric("Sent Emails", sent_count)

        with col3:
            received_count = len(emails_df[emails_df["direction"] == "received"])
            st.metric("Received Emails", received_count)

        with col4:
            # Handle aggregated recipient emails for unique contacts calculation
            unique_senders = set(emails_df["from"].dropna())
            unique_recipients = set()

            # Split aggregated recipient emails and add to set
            for recipients in emails_df["recipient_email"].dropna():
                if isinstance(recipients, str) and recipients.strip():
                    for recipient in recipients.split(','):
                        recipient = recipient.strip()
                        if recipient:
                            unique_recipients.add(recipient)

            # Calculate unique contacts (avoiding double counting)
            all_contacts = unique_senders.union(unique_recipients)
            unique_contacts = len(all_contacts)
            st.metric("Unique Contacts", unique_contacts)

        # Check if a contact filter is active
        contact_filter_key = "dashboard_contact_filter"
        if contact_filter_key not in st.session_state:
            st.session_state[contact_filter_key] = None

        # Apply contact filter if one is active (from enhanced filters or legacy)
        filtered_emails_df = emails_df
        active_contact_filter = enhanced_filters.get('contact_filter') or st.session_state[contact_filter_key]

        if active_contact_filter:
            filtered_emails_df = apply_contact_filter(emails_df, active_contact_filter)

            # Display active contact filter info
            st.info(f"📧 Filtrage actif pour le contact: `{active_contact_filter}` | {len(filtered_emails_df)} emails trouvés")

            # Add button to clear contact filter
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("❌ Supprimer le filtre contact", key="clear_contact_filter"):
                    st.session_state[contact_filter_key] = None
                    # Also clear from enhanced filters
                    if f"filter_contact_Dashboard" in st.session_state:
                        del st.session_state[f"filter_contact_Dashboard"]
                    clear_email_selection("dashboard")  # Clear any selected email
                    st.rerun()

        show_df_table(filtered_emails_df, key_prefix="dashboard", filter_status=True)

        # Create two columns for the charts
        timeline_col1, contacts_col2 = st.columns(2)

        with timeline_col1:
            # Timeline chart
            # st.subheader("Email Activity Over Time")
            st.plotly_chart(create_timeline(emails_df), use_container_width=True)

            # Top contacts
            st.subheader("Top Contacts")


        if not emails_df.empty:
            with contacts_col2:
                # Collect all contacts with their details
                all_contacts = []

                # Process senders (from column)
                for idx, row in emails_df.iterrows():
                    if pd.notna(row['from']) and row['from'].strip():
                        contact_email = row['from'].strip()
                        is_mailing_list = pd.notna(row.get('mailing_list_email')) and row.get('mailing_list_email') != ''
                        direction = 'sent' if row.get('direction') == 'sent' else 'received'

                        all_contacts.append({
                            'email': contact_email,
                            'is_mailing_list': is_mailing_list,
                            'direction': direction,
                            'type': 'sender'
                        })

                # Process recipients (recipient_email column - aggregated)
                for idx, row in emails_df.iterrows():
                    if pd.notna(row['recipient_email']) and row['recipient_email'].strip():
                        # Split aggregated recipients
                        recipients = [r.strip() for r in row['recipient_email'].split(',') if r.strip()]
                        is_mailing_list = pd.notna(row.get('mailing_list_email')) and row.get('mailing_list_email') != ''
                        direction = 'sent' if row.get('direction') == 'sent' else 'received'

                        for recipient in recipients:
                            all_contacts.append({
                                'email': recipient,
                                'is_mailing_list': is_mailing_list,
                                'direction': direction,
                                'type': 'recipient'
                            })

                if all_contacts:
                    # Convert to DataFrame for easier processing
                    contacts_df = pd.DataFrame(all_contacts)

                    # Count occurrences and aggregate mailing list info
                    contact_stats = contacts_df.groupby('email').agg({
                        'is_mailing_list': 'max',  # True if any occurrence is from mailing list
                        'direction': 'count'       # Count total occurrences
                    }).rename(columns={'direction': 'email_count'})

                    # Sort by email count and get top 20
                    top_contacts = contact_stats.sort_values('email_count', ascending=False).head(20)

                    # Create display with symbols
                    contact_list = []
                    for email, stats in top_contacts.iterrows():
                        # Determine symbol
                        if stats['is_mailing_list']:
                            symbol = "📮"  # Mailing list symbol
                            contact_type = "Mailing List"
                        else:
                            symbol = "👤"  # Human user symbol
                            contact_type = "Human User"

                        contact_list.append({
                            'Contact': f"{symbol} {email}",
                            'Type': contact_type,
                            'Email Count': stats['email_count']
                        })

                    ###### Commented but was a better display option
                    # # Display as a table
                    # if contact_list:
                    #     contacts_display_df = pd.DataFrame(contact_list).drop(columns=['Type'])
                    #     st.dataframe(
                    #         contacts_display_df,
                    #         hide_index=True,
                    #         use_container_width=True,
                    #         column_config={
                    #             "Contact": st.column_config.TextColumn(
                    #                 "Contact",
                    #                 width="large"
                    #             ),
                    #             "Email Count": st.column_config.NumberColumn(
                    #                 "Email Count",
                    #                 width="small"
                    #             )
                    #         }
                    #     )

                    # Display as a clickable table
                    if contact_list:
                        contacts_display_df = pd.DataFrame(contact_list).drop(columns=['Type'])

                        # Create clickable contact display
                        st.write("**Cliquez sur un contact pour filtrer les emails**")

                        # Display contacts as buttons in a more compact format
                        for idx, contact_row in enumerate(contact_list):
                            # Extract email from the formatted contact string
                            contact_display = contact_row['Contact']
                            # Extract email address (remove emoji and spaces)
                            if '📮' in contact_display:  # Mailing list
                                email_address = contact_display.replace('📮 ', '').strip()
                            else:  # Human user
                                email_address = contact_display.replace('👤 ', '').strip()

                            # Create button for each contact
                            if st.button(
                                f"{contact_display} ({contact_row['Email Count']} emails)",
                                key=f"contact_filter_{idx}",
                                help=f"Cliquer pour voir tous les emails impliquant {email_address}"
                            ):
                                st.session_state[contact_filter_key] = email_address
                                clear_email_selection("dashboard")  # Clear any selected email
                                st.rerun()

                        # Show summary
                        mailing_lists = sum(1 for c in contact_list if c['Type'] == 'Mailing List')
                        humans = len(contact_list) - mailing_lists
                        st.caption(f"📮 {mailing_lists} mailing lists • 👤 {humans} human users")
                    else:
                        st.info("No contact data available")
                else:
                    st.info("No contacts found in the current dataset")
        else:
            st.info("No emails available to analyze contacts")

        # Attachment formats charts
        st.subheader("Attachment Formats Analysis")

        if 'attachments' in emails_df.columns and not emails_df['attachments'].empty:
            # Extract file extensions from attachments
            all_extensions = []

            for attachments in emails_df['attachments'].dropna():
                if isinstance(attachments, list):
                    # If it's already a list (from the analyzer)
                    filenames = attachments
                elif isinstance(attachments, str) and attachments.strip():
                    # If it's a string, split by comma or pipe
                    filenames = [f.strip() for f in attachments.replace('|', ',').split(',')]
                else:
                    continue

                for filename in filenames:
                    if isinstance(filename, str) and '.' in filename:
                        ext = filename.split('.')[-1].lower().strip()
                        if ext and len(ext) <= 10:  # Reasonable extension length
                            all_extensions.append(f".{ext}")

            if all_extensions:
                # Count extensions
                from collections import Counter
                ext_counts = Counter(all_extensions)
                total_files = len(all_extensions)

                # For pie chart: group small extensions into "Others"
                pie_data = {}
                others_extensions = []

                for ext, count in ext_counts.items():
                    percentage = (count / total_files) * 100
                    if percentage >= 0.5:  # Show extensions with 0.5% or more
                        pie_data[ext] = count
                    else:
                        others_extensions.append(ext)

                # Add "Others" category if there are small extensions
                if others_extensions:
                    others_count = sum(ext_counts[ext] for ext in others_extensions)
                    others_label = "Others"
                    pie_data[others_label] = others_count

                # For bar chart: filter to top 7 extensions with >1%
                bar_data = {}
                for ext, count in ext_counts.most_common():
                    percentage = (count / total_files) * 100
                    if percentage >= 1.0:  # Only show extensions with 1% or more
                        bar_data[ext] = count
                    if len(bar_data) >= 7:  # Limit to top 7
                        break

                # Create two columns for the charts
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    # Pie chart with grouped "Others"
                    import plotly.express as px
                    fig_pie = px.pie(
                        values=list(pie_data.values()),
                        names=list(pie_data.keys()),
                        title="Distribution of Attachment Formats"
                    )
                    fig_pie.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Nombre: %{value}<br>Pourcentage: %{percent}<extra></extra>'
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)

                # with chart_col2:
                #     # Bar chart (top 7 extensions with >1%)
                #     if bar_data:
                #         fig_bar = px.bar(
                #             x=list(bar_data.keys()),
                #             y=list(bar_data.values()),
                #             title="Top Attachment Formats (>1%, max 7)",
                #             labels={'x': 'File Extension', 'y': 'Nombre'}
                #         )
                #         fig_bar.update_traces(
                #             hovertemplate='<b>%{x}</b><br>Nombre: %{y}<br>Pourcentage: %{customdata:.1f}%<extra></extra>',
                #             customdata=[(count/total_files)*100 for count in bar_data.values()]
                #         )
                #         fig_bar.update_layout(height=400)
                #         st.plotly_chart(fig_bar, use_container_width=True)
                #     else:
                #         st.info("No extensions found with >1% representation for bar chart")

                # Show summary stats
                st.caption(f"Total attachment files: {len(all_extensions):,} | Unique formats: {len(ext_counts)}")
            else:
                st.info("No attachment format data available in the filtered results")
        else:
            st.info("No attachments found in the current dataset")


    elif page == "Graph":

        if st.button("🚀 Run Script with Archive"):
            # Step 1: Define folder path
            # Get the current script directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            eml_folder = os.path.join(project_root, 'data','Projects' , ACTIVE_PROJECT, 'Boîte mail de Céline', 'processed', 'celine.guyon', 'Archive')



        # Optio
            #eml_folder = "../data/processed/celine_readpst_with_s/celine.guyon/Archive"
            emails_data = []

            # Step 2: Parse .eml files
            for filename in os.listdir(eml_folder):
                if filename.endswith(".eml"):
                    file_path = os.path.join(eml_folder, filename)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        try:
                            msg = email.message_from_file(f, policy=default)
                            sender = msg["From"]
                            receivers = msg.get_all("To", [])
                            subject = msg.get("Subject", "unknown")
                            date = msg.get("Date", "unknown")

                            # Clean sender
                            sender = email.utils.parseaddr(sender)[1] if sender else "unknown"

                            # Parse and flatten all receiver addresses
                            receiver_list = email.utils.getaddresses(receivers)
                            # Extract body
                            try:
                                html_body = getBody(msg)
                                soup = BeautifulSoup(html_body, 'html.parser')
                                body = soup.get_text()
                                body = decode_unicode_escape(body)
                            except Exception as e:
                                body = "[Error reading body]"



                            for name, addr in receiver_list:
                                addr = addr.strip()
                                if addr:  # Only keep non-empty addresses
                                    emails_data.append({
                                        "sender": sender,
                                        "receiver": addr,
                                        "subject": subject,
                                        "date": date,
                                        "body": body
                                    })

                        except Exception as e:
                            print(f"❌ Failed to parse {filename}: {e}")

            # Step 3: Create DataFrame
            df = pd.DataFrame(emails_data)

            # Optional: replace missing with placeholder
            df.replace("", "unknown", inplace=True)
            df.fillna("unknown", inplace=True)

            # Step 4: Use DuckDB to store DataFrame
            # Step 4: Use DuckDB to store DataFrame
            con = duckdb.connect(database=':memory:', read_only=False)
            for col in ["sender", "receiver", "subject", "date", "body"]:
                df[col] = df[col].astype(str).apply(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
            # Register DataFrame as a DuckDB view
            con.register("emails_df", df)

            # Now create a table from that view (optional if you prefer to use the view directly)
            con.execute("CREATE TABLE emails AS SELECT * FROM emails_df")


            # Step 5: Query Data from DuckDB (Example query)
            query = "SELECT sender, receiver, COUNT(*) AS email_count FROM emails GROUP BY sender, receiver ORDER BY email_count DESC LIMIT 10"
            result = con.execute(query).fetchdf()

            # Step 6: Display data with Streamlit
            st.title('Email Data Graph')

            import subprocess

            # Save DataFrame to CSV (or Parquet if you prefer)
            df.to_csv(f"{eml_folder}/temp_data.csv", index=False)

            # Button to run script and pass data

            with st.spinner("Running script..."):
                try:
                    result = subprocess.run(["python", "components/js2.py", f"{eml_folder}/temp_data.csv"],
                                            capture_output=True, text=True, check=True)
                    st.success("✅ Script executed successfully!")

                except subprocess.CalledProcessError as e:
                    st.error("❌ Failed to run the script.")
                    st.text(e.stderr)
            from pathlib import Path
            import shutil
            import streamlit as st
            # Folder path where the files are located
            folder_path = os.path.dirname(__file__)

        if st.button("🚀 Run Script with Envoyé"):
            # Step 1: Define folder path
            # Get the current script directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            eml_folder = os.path.join(project_root, 'data','Projects' , ACTIVE_PROJECT, 'Boîte mail de Céline', 'processed', 'celine.guyon', 'Éléments envoyés')

        # Optio
            #eml_folder = "../data/processed/celine_readpst_with_s/celine.guyon/Archive"
            emails_data = []

            # Step 2: Parse .eml files
            for filename in os.listdir(eml_folder):
                if filename.endswith(".eml"):
                    file_path = os.path.join(eml_folder, filename)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        try:
                            msg = email.message_from_file(f, policy=default)
                            sender = msg["From"]
                            receivers = msg.get_all("To", [])

                            # Clean sender
                            sender = email.utils.parseaddr(sender)[1] if sender else "unknown"

                            # Parse and flatten all receiver addresses
                            receiver_list = email.utils.getaddresses(receivers)

                            for name, addr in receiver_list:
                                addr = addr.strip()
                                if addr:  # Only keep non-empty addresses
                                    emails_data.append({
                                        "sender": sender,
                                        "receiver": addr
                                    })

                        except Exception as e:
                            print(f"❌ Failed to parse {filename}: {e}")

            # Step 3: Create DataFrame
            df = pd.DataFrame(emails_data)

            # Optional: replace missing with placeholder
            df.replace("", "unknown", inplace=True)
            df.fillna("unknown", inplace=True)

            # Step 4: Use DuckDB to store DataFrame
            # Step 4: Use DuckDB to store DataFrame
            con = duckdb.connect(database=':memory:', read_only=False)

            # Register DataFrame as a DuckDB view
            con.register("emails_df", df)

            # Now create a table from that view (optional if you prefer to use the view directly)
            con.execute("CREATE TABLE emails AS SELECT * FROM emails_df")


            # Step 5: Query Data from DuckDB (Example query)
            query = "SELECT sender, receiver, COUNT(*) AS email_count FROM emails GROUP BY sender, receiver ORDER BY email_count DESC LIMIT 10"
            result = con.execute(query).fetchdf()

            # Step 6: Display data with Streamlit
            st.title('Email Data Graph')

            import subprocess

            # Save DataFrame to CSV (or Parquet if you prefer)
            df.to_csv(f"{eml_folder}/temp_data.csv", index=False)

            # Button to run script and pass data

            with st.spinner("Running script..."):
                try:
                    result = subprocess.run(["python", "components/js.py", f"{eml_folder}/temp_data.csv"],
                                            capture_output=True, text=True, check=True)
                    st.success("✅ Script executed successfully!")

                except subprocess.CalledProcessError as e:
                    st.error("❌ Failed to run the script.")
                    st.text(e.stderr)
            from pathlib import Path
            import shutil
            import streamlit as st
            # Folder path where the files are located
            folder_path = os.path.dirname(__file__)
        if st.button("🚀 Run Script with Test"):
            folder_path = os.path.dirname(__file__)
            json_path = os.path.join(folder_path, "components/email_network4.json")
            with open(json_path, "r") as f:
                data_json = json.load(f)

        # Read HTML and inject the JSON directly
            html_path = os.path.join(folder_path, "components/viz copy 28.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        # For example, replace a placeholder in HTML like {{DATA_JSON}}
            html_content = html_content.replace("__GRAPH_DATA__", json.dumps(data_json))

            # Display in Streamlit
            components.html(html_content, height=1200,width=1200)
        if st.button("🚀 Run Script with Indesirable"):
            # Step 1: Define folder path
            # Get the current script directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            eml_folder = os.path.join(project_root, 'data','Projects' , ACTIVE_PROJECT, 'Boîte mail de Céline', 'processed', 'celine.guyon' , 'Courrier indésirable')


        # Optio

            emails_data = []

            # Step 2: Parse .eml files
            for filename in os.listdir(eml_folder):
                if filename.endswith(".eml"):
                    file_path = os.path.join(eml_folder, filename)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        try:
                            msg = email.message_from_file(f, policy=default)
                            sender = msg["From"]
                            receivers = msg.get_all("To", [])

                            # Clean sender
                            sender = email.utils.parseaddr(sender)[1] if sender else "unknown"

                            # Parse and flatten all receiver addresses
                            receiver_list = email.utils.getaddresses(receivers)

                            for name, addr in receiver_list:
                                addr = addr.strip()
                                if addr:  # Only keep non-empty addresses
                                    emails_data.append({
                                        "sender": sender,
                                        "receiver": addr
                                    })

                        except Exception as e:
                            print(f"❌ Failed to parse {filename}: {e}")

            # Step 3: Create DataFrame
            df = pd.DataFrame(emails_data)

            # Optional: replace missing with placeholder
            df.replace("", "unknown", inplace=True)
            df.fillna("unknown", inplace=True)

            # Step 4: Use DuckDB to store DataFrame
            # Step 4: Use DuckDB to store DataFrame
            con = duckdb.connect(database=':memory:', read_only=False)

            # Register DataFrame as a DuckDB view
            con.register("emails_df", df)

            # Now create a table from that view (optional if you prefer to use the view directly)
            con.execute("CREATE TABLE emails AS SELECT * FROM emails_df")


            # Step 5: Query Data from DuckDB (Example query)
            query = "SELECT sender, receiver, COUNT(*) AS email_count FROM emails GROUP BY sender, receiver ORDER BY email_count DESC LIMIT 10"
            result = con.execute(query).fetchdf()

            # Step 6: Display data with Streamlit
            st.title('Email Data Graph')

            import subprocess

            # Save DataFrame to CSV (or Parquet if you prefer)
            df.to_csv(f"{eml_folder}/temp_data.csv", index=False)

            # Button to run script and pass data

            with st.spinner("Running script..."):
                try:
                    result = subprocess.run(["python", "components/js.py", f"{eml_folder}/temp_data.csv"],
                                            capture_output=True, text=True, check=True)
                    st.success("✅ Script executed successfully!")

                except subprocess.CalledProcessError as e:
                    st.error("❌ Failed to run the script.")
                    st.text(e.stderr)
            from pathlib import Path
            import shutil
            import streamlit as st
            # Folder path where the files are located
            folder_path = os.path.dirname(__file__)
        import streamlit as st
        import streamlit.components.v1 as components
        import os

        folder_path = os.path.dirname(__file__)

        import json

        # Read JSON data
        json_path = os.path.join(folder_path, "components/email_network.json")
        with open(json_path, "r") as f:
            data_json = json.load(f)

        # Read HTML and inject the JSON directly
        html_path = os.path.join(folder_path, "components/viz copy 28.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # For example, replace a placeholder in HTML like {{DATA_JSON}}
        html_content = html_content.replace("__GRAPH_DATA__", json.dumps(data_json))

            # Display in Streamlit
        components.html(html_content, height=1200,width=1200)
    elif page == "Topic":
        folder_path = os.path.dirname(__file__)

        # Read JSON data
        json_path = os.path.join(folder_path, "components/tree3.json")

        with open(json_path, "r", encoding="utf-8") as f:
            data_json = json.load(f)

        # Read HTML and inject the JSON
        html_path = os.path.join(folder_path, "components/topic_tree.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        # Replace the placeholder with actual JSON data (as JS object)
        json_js = json.dumps(data_json)
        html_content = html_template.replace("__GRAPH_DATA__", json_js)

        # Display in Streamlit

        st.title("Topic Tree Visualization")

        components.html(html_content, height=800, width=2200)
    elif page == "Graph_Br":
        st.title("📬 Email Data Analysis ")

        # Load folder path
        folder_path = os.path.dirname(__file__)

        # Load the pre-parsed CSV
        csv_path = os.path.join(folder_path, "components/temp_data_full.csv")

        if not os.path.exists(csv_path):
            st.error("❌ CSV file 'temp_data.csv' not found.")
            st.stop()

        df = pd.read_csv(csv_path)
        df.replace("", "unknown", inplace=True)
        df.fillna("unknown", inplace=True)

        # Clean columns
        for col in ["sender", "receiver"]:
            df[col] = df[col].astype(str)

        st.success(f"✅ Loaded {len(df)} emails from CSV.")

        # Grouped contacts
        df["contact_1"] = df[["sender", "receiver"]].min(axis=1)
        df["contact_2"] = df[["sender", "receiver"]].max(axis=1)
        result = (
            df.groupby(["contact_1", "contact_2"])
            .size()
            .reset_index(name="email_count")
            .sort_values(by="email_count", ascending=False)
        )

        # Display results
        st.subheader("🔝 Top email pairs by count:")
        st.dataframe(result)

        st.subheader("📋 Full DataFrame:")



        @st.cache_data
        def load_html(filename):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                return f.read()

        @st.cache_data
        def load_json(filename):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                return json.load(f)


        # Show injected JSON graph visualization
        if st.button("🧠 Visualiser Graph JSON"):
            html = load_html("components/viz copy 29.html")
            json_path = os.path.join(folder_path, "components/email_network_full.json")
            if os.path.exists(json_path):
                graph_data = load_json("components/email_network_full.json")
                html = html.replace("__GRAPH_DATA__", json.dumps(graph_data))
                components.html(html, width=1200, height=800)
            else:
                st.error("❌ JSON file 'email_network.json' not found.")

    elif page == "Email Explorer":
        # Load data with working dropdown filters
        enhanced_filters, filters_changed = create_working_dropdown_filters(
            page_name="Email Explorer",
            emails_df=None,  # Will be loaded after filters
            mailbox_options=mailbox_options,
            email_filters=email_filters
        )

        # Get filter values for data loading
        selected_mailbox_filter = enhanced_filters.get('mailbox', selected_mailbox)

        # Convert enhanced filters to the format expected by load_data_with_filters
        filter_dict = {}
        if enhanced_filters.get('direction'):
            filter_dict['direction'] = enhanced_filters['direction']
        if enhanced_filters.get('sender'):
            filter_dict['sender'] = enhanced_filters['sender']
        if enhanced_filters.get('recipient'):
            filter_dict['recipient'] = enhanced_filters['recipient']
        if enhanced_filters.get('has_attachments'):
            filter_dict['has_attachments'] = True

        emails_df = load_data_with_filters(selected_mailbox_filter, filter_dict)

        # Apply date range filter if specified in enhanced filters
        if enhanced_filters.get('date_range'):
            emails_df = apply_date_filter(emails_df, enhanced_filters['date_range'])
        else:
            emails_df = apply_date_filter(emails_df, date_range)

        st.subheader("Email Explorer")

        # Show comprehensive filter status (using legacy for now)
        show_comprehensive_filter_status(additional_filters, email_filters)

        # Email list with filter
        search_term = st.text_input("Search in emails:")

        if search_term:
            filtered_df = emails_df[
                emails_df["subject"].str.contains(search_term, case=False, na=False) |
                emails_df["body"].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = emails_df

        # Display filtered emails with interactive viewer
        st.write(f"Showing {len(filtered_df)} emails")
        create_email_table_with_viewer(filtered_df, key_prefix="explorer")

    elif page == "Network Analysis":
        emails_df = load_data_with_filters(selected_mailbox, additional_filters)

        # Apply date range filter
        emails_df = apply_date_filter(emails_df, date_range)

        st.subheader("Email Network Analysis")

        # Show comprehensive filter status
        show_comprehensive_filter_status(additional_filters, email_filters)

        # Network visualization options
        st.write("This view shows the communication network between email addresses.")

        # Display network graph
        st.plotly_chart(create_network_graph(emails_df), use_container_width=True)

    # elif page == "Timeline":
    #     emails_df = load_data(selected_mailbox)
    #     st.subheader("Email Timeline")

    #     # Timeline visualization
    #     st.plotly_chart(create_timeline(emails_df), use_container_width=True)

    # Debugging timeline temporary page
    elif page == "Timeline":
        emails_df = load_data_with_filters(selected_mailbox, additional_filters, use_agg_recipients=True)

        # Apply date range filter
        emails_df = apply_date_filter(emails_df, date_range)

        st.subheader("Email Timeline")

        # Show comprehensive filter status
        show_comprehensive_filter_status(additional_filters, email_filters)

        # Print debug information
        st.write(f"Total emails loaded: {len(emails_df)}")

        # Check and fix the date column if needed
        if 'date' in emails_df.columns:
            # If dates are stored as string representations of Timestamp objects
            if emails_df['date'].dtype == 'object' and emails_df['date'].astype(str).str.contains('Timestamp').any():
                # Extract the actual date from the Timestamp string
                emails_df['date'] = emails_df['date'].astype(str).str.extract(r"Timestamp\('([^']+)'\)")[0]

            # Convert to datetime
            emails_df['date'] = pd.to_datetime(emails_df['date'], errors='coerce')

            # Show the date range for debugging
            if not emails_df['date'].isna().all():
                st.write(f"Date range: {emails_df['date'].min()} to {emails_df['date'].max()}")

        # Check the direction column
        if 'direction' in emails_df.columns:
            # Show unique values in the direction column
            directions = emails_df['direction'].unique()
            st.write(f"Direction values found: {directions}")

            # If needed, normalize direction values (case insensitive match)
            emails_df['direction'] = emails_df['direction'].str.lower()
            emails_df.loc[emails_df['direction'].str.contains('sent|outgoing|out'), 'direction'] = 'sent'
            emails_df.loc[emails_df['direction'].str.contains('received|incoming|in'), 'direction'] = 'received'

        # Now create the timeline with the fixed dataframe
        st.plotly_chart(create_timeline(emails_df), use_container_width=True)

    elif page == "Recherche Sémantique":
        # Add working dropdown filters to search page
        enhanced_filters, filters_changed = create_working_dropdown_filters(
            page_name="Recherche Sémantique",
            emails_df=None,
            mailbox_options=mailbox_options,
            email_filters=email_filters
        )

        st.subheader("Recherche avancée")

        # Load emails data with filters
        selected_mailbox_filter = enhanced_filters.get('mailbox', selected_mailbox)

        # Convert enhanced filters
        filter_dict = {}
        if enhanced_filters.get('direction'):
            direction_map = {"Envoyés": "sent", "Reçus": "received"}
            filter_dict['direction'] = direction_map.get(enhanced_filters['direction'], enhanced_filters['direction'])
        if enhanced_filters.get('sender'):
            filter_dict['sender'] = enhanced_filters['sender']
        if enhanced_filters.get('recipient'):
            filter_dict['recipient'] = enhanced_filters['recipient']
        if enhanced_filters.get('has_attachments'):
            filter_dict['has_attachments'] = True

        emails_df = load_data(selected_mailbox_filter)

        # Apply date range filter if specified
        if enhanced_filters.get('date_range'):
            emails_df = apply_date_filter(emails_df, enhanced_filters['date_range'])
        else:
            emails_df = apply_date_filter(emails_df, date_range)

        # Initialize Elasticsearch (mock mode)
        st.write("Cette interface vous permet de rechercher dans vos archives d'emails avec des filtres avancés.")

        # Create a layout with two columns
        col1, col2 = st.columns([2, 1])

        with col1:
            # Search query input
            search_query = st.text_input("Rechercher dans les emails:", placeholder="Entrez des mots-clés...")

        with col2:
            # Direction filter
            direction_options = ["Tous", "Envoyés", "Reçus"]
            selected_direction = st.selectbox("Direction:", direction_options)

            # Convert selection to filter format
            direction_filter = None
            if selected_direction == "Envoyés":
                direction_filter = "sent"
            elif selected_direction == "Reçus":
                direction_filter = "received"

        # Additional filters in an expander
        with st.expander("Filtres avancés"):
            # Date range filter
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Date de début:", value=None)
            with col_date2:
                end_date = st.date_input("Date de fin:", value=None)

            # Sender/recipient filters
            col_from, col_to = st.columns(2)

            # Get unique senders and recipients
            unique_senders = emails_df['from'].dropna().unique().tolist()
            unique_recipients = []
            for recipients in emails_df["recipient_email"].dropna():
                for recipient in recipients.split(';'):
                    recipient = recipient.strip()
                    if recipient and recipient not in unique_recipients:
                        unique_recipients.append(recipient)

            with col_from:
                selected_sender = st.selectbox(
                    "Expéditeur:",
                    ["Tous"] + sorted(unique_senders)
                )
            with col_to:
                selected_recipient = st.selectbox(
                    "Destinataire:",
                    ["Tous"] + sorted(unique_recipients)
                )

            # Attachment filter
            has_attachments = st.checkbox("Avec pièces jointes")

        # Prepare search filters
        filters = {}
        if direction_filter:
            filters['direction'] = direction_filter
        if selected_sender != "Tous":
            filters['from'] = selected_sender
        if selected_recipient != "Tous":
            filters["recipient_email"] = selected_recipient
        if has_attachments:
            filters['has_attachments'] = True

        # Prepare date range
        date_range = {}
        if start_date:
            date_range['start'] = pd.Timestamp(start_date)
        if end_date:
            # Set to end of day
            end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            date_range['end'] = end_datetime

        # Execute search when query is submitted
        if search_query or filters or date_range:
            # Show a spinner during search
            with st.spinner("Recherche en cours..."):
                # Use search functionality
                results_df = search_emails(
                    emails_df,
                    query=search_query,
                    filters=filters,
                    date_range=date_range
                )

            # Display results
            st.subheader(f"Résultats: {len(results_df)} emails trouvés")

            # Display results using the interactive viewer
            if not results_df.empty:
                create_email_table_with_viewer(results_df, key_prefix="search")
            else:
                st.info("Aucun résultat trouvé. Essayez d'élargir vos critères de recherche.")

    elif page == "Recherche ElasticSearch":
        # Add working dropdown filters to ElasticSearch page
        enhanced_filters, filters_changed = create_working_dropdown_filters(
            page_name="Recherche ElasticSearch",
            emails_df=None,
            mailbox_options=mailbox_options,
            email_filters=email_filters
        )

        # Load emails data with filters
        selected_mailbox_filter = enhanced_filters.get('mailbox', selected_mailbox)

        # Convert enhanced filters
        filter_dict = {}
        if enhanced_filters.get('direction'):
            direction_map = {"Envoyés": "sent", "Reçus": "received"}
            filter_dict['direction'] = direction_map.get(enhanced_filters['direction'], enhanced_filters['direction'])
        if enhanced_filters.get('sender'):
            filter_dict['sender'] = enhanced_filters['sender']
        if enhanced_filters.get('recipient'):
            filter_dict['recipient'] = enhanced_filters['recipient']
        if enhanced_filters.get('has_attachments'):
            filter_dict['has_attachments'] = True

        emails_df = load_data(selected_mailbox_filter)

        # Apply date range filter if specified
        if enhanced_filters.get('date_range'):
            emails_df = apply_date_filter(emails_df, enhanced_filters['date_range'])
        else:
            emails_df = apply_date_filter(emails_df, date_range)

        st.session_state.emails_df = emails_df

        # Direct implementation of ElasticSearch search page
        st.subheader("Recherche ElasticSearch")
        st.write("Cette interface vous permet de rechercher dans vos archives d'emails en utilisant ElasticSearch.")

        # Create tabs for different search modes
        search_tabs = st.tabs([
            "Recherche Simple",
            "Recherche Avancée",
            "Options"
        ])

        with search_tabs[0]:  # Simple Search
            col1, col2 = st.columns([3, 1])

            with col1:
                # Search query input
                search_query = st.text_input(
                    "Rechercher dans les emails:",
                    key="simple_search_query",
                    placeholder="Entrez des mots-clés..."
                )

            with col2:
                # Search mode selection
                search_mode = st.selectbox(
                    "Mode de recherche:",
                    options=[
                        "all",
                        "content_and_title",
                        "title_only",
                        "content_only"
                    ],
                    format_func=lambda x: {
                        "all": "Tous les champs",
                        "content_and_title": "Contenu et Titre",
                        "title_only": "Titre uniquement",
                        "content_only": "Contenu uniquement"
                    }.get(x, x),
                    key="simple_search_mode"
                )

            # Direction filter
            direction_options = ["Tous", "Envoyés", "Reçus"]
            selected_direction = st.selectbox("Direction:", direction_options, key="simple_direction")

            # Convert selection to filter format
            direction_filter = None
            if selected_direction == "Envoyés":
                direction_filter = "sent"
            elif selected_direction == "Reçus":
                direction_filter = "received"

            # Prepare filters
            filters = {}
            if direction_filter:
                filters["direction"] = direction_filter

            # Simple search button
            simple_search_button = st.button("Rechercher", key="simple_search_button")

            if simple_search_button:
                if not search_query and not filters:
                    st.warning("Veuillez saisir au moins un terme de recherche ou sélectionner un filtre.")
                else:
                    # Show a spinner during search
                    with st.spinner("Recherche en cours..."):
                        # Get fuzziness from session state or default to AUTO
                        fuzziness = st.session_state.get("fuzziness", "AUTO")

                        # Use enhanced search functionality
                        results_df = enhanced_search_emails(
                            emails_df,
                            query=search_query,
                            search_mode=search_mode,
                            filters=filters,
                            fuzziness=fuzziness,
                            size=100  # Limit to 100 results
                        )

                        # Store results in session state
                        st.session_state["search_results"] = results_df

                        # Display results count
                        st.subheader(f"Résultats: {len(results_df)} emails trouvés")

                        # Display results using the interactive viewer
                        if not results_df.empty:
                            create_email_table_with_viewer(results_df, key_prefix="es_search_simple")
                        else:
                            st.info("Aucun résultat trouvé. Essayez d'élargir vos critères de recherche ou de modifier le niveau de fuzziness.")

        with search_tabs[1]:  # Advanced Search
            st.write("Recherche avancée avec plus d'options de filtrage")

            # Search query input
            search_query = st.text_input(
                "Rechercher dans les emails:",
                key="advanced_search_query",
                placeholder="Entrez des mots-clés..."
            )

            # Select which fields to search in
            st.write("Champs à inclure dans la recherche:")
            col1, col2 = st.columns(2)

            with col1:
                include_subject = st.checkbox("Sujet", value=True, key="include_subject")
                include_body = st.checkbox("Contenu", value=True, key="include_body")

            with col2:
                include_from = st.checkbox("Expéditeur", value=False, key="include_from")
                include_to = st.checkbox("Destinataire", value=False, key="include_to")

            # Build search fields list
            search_fields = []
            if include_subject:
                search_fields.append("subject")
            if include_body:
                search_fields.append("body")
            if include_from:
                search_fields.extend(["from", "from_name"])
            if include_to:
                search_fields.extend(["recipient_email", "to_name"])

            # At least one field must be selected
            if not search_fields:
                st.warning("Veuillez sélectionner au moins un champ de recherche.")
                search_fields = ["subject", "body"]

            # Additional filters in an expander
            with st.expander("Filtres avancés", expanded=True):
                # Date range filter
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Date de début:", value=None, key="advanced_start_date")
                with col_date2:
                    end_date = st.date_input("Date de fin:", value=None, key="advanced_end_date")

                # Sender/recipient filters
                col_from, col_to = st.columns(2)

                # Get unique senders and recipients
                unique_senders = emails_df['from'].dropna().unique().tolist()
                unique_recipients = []
                for recipients in emails_df["recipient_email"].dropna():
                    for recipient in recipients.split(';'):
                        recipient = recipient.strip()
                        if recipient and recipient not in unique_recipients:
                            unique_recipients.append(recipient)

                with col_from:
                    selected_sender = st.selectbox(
                        "Expéditeur:",
                        ["Tous"] + sorted(unique_senders),
                        key="advanced_sender"
                    )
                with col_to:
                    selected_recipient = st.selectbox(
                        "Destinataire:",
                        ["Tous"] + sorted(unique_recipients),
                        key="advanced_recipient"
                    )

                # Attachment filter
                has_attachments = st.checkbox("Avec pièces jointes", key="advanced_has_attachments")

                # Direction filter
                direction_options = ["Tous", "Envoyés", "Reçus"]
                selected_direction = st.selectbox("Direction:", direction_options, key="advanced_direction")

                # Convert selection to filter format
                direction_filter = None
                if selected_direction == "Envoyés":
                    direction_filter = "sent"
                elif selected_direction == "Reçus":
                    direction_filter = "received"

            # Prepare search filters
            filters = {}
            if direction_filter:
                filters['direction'] = direction_filter
            if selected_sender != "Tous":
                filters['from'] = selected_sender
            if selected_recipient != "Tous":
                filters["recipient_email"] = selected_recipient
            if has_attachments:
                filters['has_attachments'] = True

            # Prepare date range
            date_range = {}
            if start_date:
                date_range['start'] = pd.Timestamp(start_date)
            if end_date:
                # Set to end of day
                end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                date_range['end'] = end_datetime

            # Advanced search button
            advanced_search_button = st.button("Rechercher", key="advanced_search_button")

            if advanced_search_button:
                if not search_query and not filters and not date_range:
                    st.warning("Veuillez saisir au moins un terme de recherche ou sélectionner un filtre.")
                else:
                    # Show a spinner during search
                    with st.spinner("Recherche en cours..."):
                        # Get fuzziness from session state or default to AUTO
                        fuzziness = st.session_state.get("fuzziness", "AUTO")

                        # Use enhanced search functionality
                        results_df = enhanced_search_emails(
                            emails_df,
                            query=search_query,
                            search_mode="advanced",
                            fields=search_fields,
                            filters=filters,
                            date_range=date_range,
                            fuzziness=fuzziness,
                            size=100  # Limit to 100 results
                        )

                        # Store results in session state
                        st.session_state["search_results"] = results_df

                        # Display results count
                        st.subheader(f"Résultats: {len(results_df)} emails trouvés")

                        # Display results using the interactive viewer
                        if not results_df.empty:
                            create_email_table_with_viewer(results_df, key_prefix="es_search_advanced")
                        else:
                            st.info("Aucun résultat trouvé. Essayez d'élargir vos critères de recherche ou de modifier le niveau de fuzziness.")

        with search_tabs[2]:  # Options
            st.write("Options de recherche ElasticSearch")

            # Fuzziness setting
            st.write("### Niveau de Fuzziness")
            fuzziness_options = [
                {"label": "AUTO (Recommandé)", "value": "AUTO"},
                {"label": "0 (Correspondance exacte)", "value": "0"},
                {"label": "1 (Permet 1 caractère de différence)", "value": "1"},
                {"label": "2 (Permet 2 caractères de différence)", "value": "2"}
            ]

            selected_fuzziness = st.selectbox(
                "Niveau de fuzziness:",
                options=fuzziness_options,
                format_func=lambda x: x["label"],
                index=0  # Default to AUTO
            )

            # Save fuzziness setting to session state
            st.session_state["fuzziness"] = selected_fuzziness["value"]

            # Explanation of search modes
            st.write("### Explication des modes de recherche:")
            st.markdown("""
            - **Tous les champs**: Recherche dans tous les champs (sujet, contenu, expéditeur, destinataire)
            - **Contenu et Titre**: Recherche uniquement dans le sujet et le contenu de l'email
            - **Titre uniquement**: Recherche uniquement dans le sujet de l'email
            - **Contenu uniquement**: Recherche uniquement dans le contenu de l'email
            - **Recherche avancée**: Permet de sélectionner les champs spécifiques à inclure dans la recherche
            """)

            # Explanation of fuzziness
            st.write("### Qu'est-ce que la fuzziness?")
            st.markdown("""
            La fuzziness permet de trouver des résultats même lorsque les termes recherchés
            contiennent des fautes d'orthographe ou des variations.

            - **AUTO**: Détermine automatiquement le niveau de fuzziness en fonction de la longueur du terme
            - **0**: Correspondance exacte, sans tolérance pour les fautes
            - **1**: Permet une différence d'un caractère (insertion, suppression, substitution)
            - **2**: Permet deux différences de caractères
            """)

            # Reset search parameters
            if st.button("Réinitialiser les paramètres de recherche"):
                # Clear session state for search parameters
                keys_to_clear = [
                    "simple_search_query", "simple_search_mode", "simple_direction",
                    "advanced_search_query", "include_subject", "include_body",
                    "include_from", "include_to", "advanced_start_date", "advanced_end_date",
                    "advanced_sender", "advanced_recipient", "advanced_has_attachments",
                    "advanced_direction", "search_results"
                ]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]

                # Set default fuzziness
                st.session_state["fuzziness"] = "AUTO"

                st.success("Paramètres réinitialisés.")
                st.rerun()

        # Display previous search results if available
        if "search_results" in st.session_state and not st.session_state["search_results"].empty:
            # Only show if not already displayed by a search button click
            if not (st.session_state.get("simple_search_button", False) or
                    st.session_state.get("advanced_search_button", False)):
                results_df = st.session_state["search_results"]
                st.subheader(f"Résultats précédents: {len(results_df)} emails trouvés")
                create_email_table_with_viewer(results_df, key_prefix="es_search_previous")

    elif page == "Chat":
        st.subheader("Discuter avec vos archives d'emails")

        # RAG-based chat interface
        st.markdown("""
        Cette interface conversationnelle vous permet de poser des questions sur vos archives d'emails.
        Le système utilise une recherche basée sur ColBERT pour trouver les emails pertinents et fournir des informations.

        **Exemples de questions que vous pouvez poser:**
        - "Quand est prévue la prochaine réunion du comité ?"
        - "Qu'est-ce qui a été discuté dans l'email de Marie Durand ?"
        - "Qui travaille sur le projet de numérisation ?"
        - "Quels sont les délais mentionnés dans les emails récents ?"
        """)

        # First, ensure we have emails loaded
        emails_df = load_data(selected_mailbox)

        # Apply date range filter
        emails_df = apply_date_filter(emails_df, date_range)

        # Initialize the RAG system (if needed)
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            index_dir = initialize_rag_system(emails_df, project_root)

            # Display system status
            with st.expander("System Status", expanded=False):
                st.success(f"RAG system initialized successfully.")
                st.info(f"Using index at: {index_dir}")
                st.info(f"Email corpus size: {len(emails_df)} emails")

            # Store conversation history in session state
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # Display chat history
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    st.chat_message("assistant").write(message["content"])
                    # Display sources if available
                    if "sources" in message:
                        with st.expander("Voir les sources"):
                            for source in message["sources"]:
                                st.markdown(source)

            # Chat input
            user_query = st.chat_input("Posez une question sur vos emails:")

            if user_query:
                # Display user message
                st.chat_message("user").write(user_query)

                # Add to history
                st.session_state.chat_history.append({"role": "user", "content": user_query})

                # Display thinking message
                with st.chat_message("assistant"):
                    thinking_msg = st.empty()
                    thinking_msg.write("Réflexion...")

                    try:
                        # Get answer from RAG system
                        with st.spinner():
                            start_time = time.time()
                            answer, sources = get_rag_answer(user_query, index_dir, top_k=3)
                            elapsed_time = time.time() - start_time

                        # Replace thinking message with answer
                        thinking_msg.write(answer)

                        # Show sources in expander
                        if sources:
                            with st.expander("Voir les emails sources"):
                                for source in sources:
                                    st.markdown(source)

                        # Add to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })

                        # Show response time
                        st.caption(f"Temps de réponse: {elapsed_time:.2f} secondes")

                    except Exception as e:
                        thinking_msg.error(f"Error: {str(e)}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"J'ai rencontré une erreur: {str(e)}"
                        })

            # Add a button to reset the chat history
            if st.session_state.chat_history and st.button("Réinitialiser la conversation"):
                st.session_state.chat_history = []
                st.rerun()

        except Exception as e:
            st.error(f"Erreur d'initialisation du système RAG: {str(e)}")
            st.info("Veuillez vous assurer que vous avez des emails chargés et essayez à nouveau.")

            # Fallback to a simple interface if RAG is not available
            user_query = st.text_input("Posez une question sur vos emails (mode basique):")
            if user_query:
                st.info("Le système RAG avancé n'est pas disponible. Utilisation du mode basique à la place.")
                st.write("Dans une implémentation complète, cela utiliserait un système RAG sophistiqué pour fournir des réponses basées sur le corpus d'emails.")

    elif page == "Colbert RAG":
        st.title("Colbert RAG - Recherche sémantique avancée")

        # Import the Colbert RAG component
        try:
            from components.colbert_rag_component import render_colbert_rag_component

            # Render the component with the loaded email data
            emails_df = load_data(selected_mailbox)

            # Apply date range filter
            emails_df = apply_date_filter(emails_df, date_range)

            render_colbert_rag_component(emails_df)
        except ImportError as e:
            st.error(f"Erreur d'importation du composant Colbert RAG: {str(e)}")
            st.info("Veuillez vérifier que toutes les dépendances sont installées.")
        except Exception as e:
            st.error(f"Erreur lors du rendu du composant Colbert RAG: {str(e)}")

    elif page == "Structure de la boîte mail":
        # Import and render the Mail Structure page
        try:
            # Use the clean version by default
            from components.mail_structure_clean import render_mail_structure_page
            render_mail_structure_page()

        except ImportError as e:
            st.error(f"Erreur d'importation de la page Structure de la boîte mail: {str(e)}")
            st.info("Veuillez vérifier que le module mail_structure.py est disponible.")
        except Exception as e:
            st.error(f"Erreur lors du rendu de la page Structure de la boîte mail: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

        # # Check if we should use alternative versions (from debug options)
        # if st.session_state.get('use_step_debug_mail_structure', False):
        #     try:
        #         from components.mail_structure_step_debug import render_mail_structure_page as step_debug_render
        #         st.markdown("---")
        #         st.subheader("🔍 Step-by-Step Debug Version")
        #         step_debug_render()
        #         st.session_state.use_step_debug_mail_structure = False  # Reset after use
        #     except Exception as e:
        #         st.error(f"Step debug version failed: {str(e)}")
        #         st.session_state.use_step_debug_mail_structure = False

        # elif st.session_state.get('use_fixed_mail_structure', False):
        #     try:
        #         from components.mail_structure_fixed import render_mail_structure_page as fixed_render
        #         st.markdown("---")
        #         st.subheader("📁 Fixed Mail Structure")
        #         fixed_render()
        #         st.session_state.use_fixed_mail_structure = False  # Reset after use
        #     except Exception as e:
        #         st.error(f"Fixed version failed: {str(e)}")
        #         st.session_state.use_fixed_mail_structure = False

        # elif st.session_state.get('use_ultimate_mail_structure', False):
        #     try:
        #         from components.mail_structure_ultimate import render_mail_structure_page as ultimate_render
        #         st.markdown("---")
        #         st.subheader("🏆 Ultimate Mail Structure")
        #         ultimate_render()
        #         st.session_state.use_ultimate_mail_structure = False  # Reset after use
        #     except Exception as e:
        #         st.error(f"Ultimate version failed: {str(e)}")
        #         st.session_state.use_ultimate_mail_structure = False

        # elif st.session_state.get('use_diagnostic_mail_structure', False):
        #     try:
        #         from components.mail_structure_diagnostic import render_mail_structure_page as diagnostic_render
        #         st.markdown("---")
        #         st.subheader("🔧 Diagnostic Mail Structure")
        #         diagnostic_render()
        #         st.session_state.use_diagnostic_mail_structure = False  # Reset after use
        #     except Exception as e:
        #         st.error(f"Diagnostic version failed: {str(e)}")
        #         st.session_state.use_diagnostic_mail_structure = False

    elif page == "Chat + RAG":
        # No filters for chat - load data directly
        emails_df = load_data(selected_mailbox)

        # Apply date range filter
        emails_df = apply_date_filter(emails_df, date_range)

        # Import and render the Chat + RAG component
        try:
            from components.chat_rag_component import render_chat_rag_component
            render_chat_rag_component(emails_df)
        except ImportError as e:
            st.error(f"Erreur d'importation du composant Chat + RAG: {str(e)}")
            st.info("Veuillez vérifier que toutes les dépendances sont installées.")
        except Exception as e:
            st.error(f"Erreur lors du rendu du composant Chat + RAG: {str(e)}")

    # elif page == "Manage Projects":
    #     # Import and run the manage_projects page
    #     import app.pages.manage_projects

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("Okloa - Email Archive Analytics Platform")
