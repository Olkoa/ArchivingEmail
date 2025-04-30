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



# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# Import project constants and elasticsearch enhanced search functionality
from constants import EMAIL_DISPLAY_TYPE, SIDEBAR_STATE
from src.features.elasticsearch_enhanced import enhanced_search_emails
from src.features.decodeml import decode_unicode_escape , getBody


# Set page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Okloa - Email Archive Analytics",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state=SIDEBAR_STATE,
)

# Import application components - using relative import
sys.path.append(os.path.dirname(__file__))
from components.email_viewer import create_email_table_with_viewer

from src.data.loading import load_mailboxes
from src.data.email_analyzer import EmailAnalyzer
from src.features.embeddings import generate_embeddings
from src.visualization.email_network import create_network_graph
from src.visualization.timeline import create_timeline
from src.rag.initialization import initialize_rag_system
from src.rag.retrieval import get_rag_answer
from src.features.search import search_emails

# Page configuration is already set at the top of the file

# Application title and description
st.title("Okloa - Email Archive Analytics")
st.markdown("""
    Welcome to Okloa, a platform for exploring and analyzing archived email data.
    This application helps you visualize email communication patterns, search through
    the corpus, and extract insights using advanced natural language processing techniques.
""")

# Sidebar for navigation and controls
st.sidebar.title("Navigation")

# Organize pages into categories for better navigation
navigation_categories = {

    "Overview": ["Dashboard"],
    "Exploration": ["Email Explorer", "Network Analysis", "Timeline"],
    "Search": ["Recherche", "Recherche ElasticSearch"],
    "Graph": ["Graph"],
    "AI Assistants": ["Chat", "Colbert RAG"]
}

# Display navigation categories
selected_category = st.sidebar.radio("Category", list(navigation_categories.keys()))

# Display pages within the selected category
page = st.sidebar.radio(
    "Select a page:",
    navigation_categories[selected_category]
)

# Data loading section (in the sidebar)
st.sidebar.title("Data")

# This will have to be an accessible var from the project selection and forward
project_name = "Projet Demo"

# get the mailboxes names from the project config file to allow separating mailboxs in the same project.
# with open(f"data/Projects/{project_name}/project_config_file.json", 'r', encoding='utf-8') as file:
with open(os.path.join(project_root, 'data', 'Projects', project_name, 'project_config_file.json'), 'r', encoding='utf-8') as file:
    json_data = json.load(file)

mailboxs_names = list(json_data["Projet Demo"]["mailboxs"].keys())

mailbox_options = ["All Mailboxes"] + mailboxs_names
selected_mailbox = st.sidebar.selectbox("Select Mailbox:", mailbox_options)

# Store selected mailbox in session state for other pages to access
st.session_state.selected_mailbox = selected_mailbox

# Timeframe selection
st.sidebar.title("Filters")
date_range = st.sidebar.date_input(
    "Date Range:",
    value=(pd.to_datetime("2023-01-01"), pd.to_datetime("2023-12-31")),
)

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
                "message_id", "date", "from", "to", "cc", "subject",
                "body", "attachments", "has_attachments", "direction", "mailbox"
            ])

        return df
    except Exception as e:
        st.sidebar.error(f"Error loading mailboxes: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            "message_id", "date", "from", "to", "cc", "subject",
            "body", "attachments", "has_attachments", "direction", "mailbox"
        ])

# Load data based on selection from DuckDB
@st.cache_data
def load_data(mailbox_selection):
    """Load and cache the selected mailbox data from DuckDB"""
    try:

        db_path = os.path.join(project_root, 'data', 'Projects', 'Projet Demo', 'célineETjoel.duckdb')

        # Get data from DuckDB using EmailAnalyzer
        analyzer = EmailAnalyzer(db_path=db_path)
        df = analyzer.get_app_DataFrame()
        print(df.columns)

        # Filter based on mailbox selection
        if mailbox_selection != "All Mailboxes":
            df = df[df['mailbox_name'] == mailbox_selection]

        if len(df) == 0:
            st.sidebar.warning("No emails found in the selected mailbox(es).")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                "message_id", "date", "from", "to", "cc", "subject",
                "body", "attachments", "has_attachments", "direction", "mailbox"
            ])

        return df
    except Exception as e:
        st.sidebar.error(f"Error loading data from DuckDB: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            "message_id", "date", "from", "to", "cc", "subject",
            "body", "attachments", "has_attachments", "direction", "mailbox"
        ])

# Main content
if page == "Dashboard":
    emails_df = load_data(selected_mailbox)

    # Display key metr ics
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
        unique_contacts = emails_df["from"].nunique() + emails_df["to"].nunique()
        st.metric("Unique Contacts", unique_contacts)

    # Timeline chart
    st.subheader("Email Activity Over Time")
    st.plotly_chart(create_timeline(emails_df), use_container_width=True)

    # Top contacts
    st.subheader("Top Contacts")
    # This would be implemented in a real application
elif page == "Graph":
    import os
    import pandas as pd
    import email
    from email.policy import default
    import streamlit.components.v1 as components
    import duckdb
    from pathlib import Path
    import streamlit as st
    if st.button("🚀 Run Script with Archieve"):
        # Step 1: Define folder path
        # Get the current script directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        eml_folder = os.path.join(project_root, 'data','Projects' ,'Projet Demo', 'Boîte mail de Céline', 'processed', 'celine.guyon', 'Archive')



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
        eml_folder = os.path.join(project_root, 'data','Projects' ,'Projet Demo', 'Boîte mail de Céline', 'processed', 'celine.guyon', 'Éléments envoyés')

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
        eml_folder = os.path.join(project_root, 'data','Projects' ,'Projet Demo', 'Boîte mail de Céline', 'processed', 'celine.guyon' , 'Courrier indésirable')


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

elif page == "Email Explorer":
    emails_df = load_data(selected_mailbox)
    st.subheader("Email Explorer")

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
    emails_df = load_data(selected_mailbox)
    st.subheader("Email Network Analysis")

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
    emails_df = load_data(selected_mailbox)
    st.subheader("Email Timeline")

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

elif page == "Recherche":
    st.subheader("Recherche avancée")

    # Load emails data
    emails_df = load_data(selected_mailbox)

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
        for recipients in emails_df['to'].dropna():
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
        filters['to'] = selected_recipient
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
    # Load emails data to make it available in session state
    emails_df = load_data(selected_mailbox)
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
            search_fields.extend(["to", "to_name"])

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
            for recipients in emails_df['to'].dropna():
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
            filters['to'] = selected_recipient
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
    from components.colbert_rag_component import render_colbert_rag_component

    # Render the component with the loaded email data
    emails_df = load_data(selected_mailbox)
    render_colbert_rag_component(emails_df)

# elif page == "Manage Projects":
#     # Import and run the manage_projects page
#     import app.pages.manage_projects

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Okloa - Email Archive Analytics Platform")
