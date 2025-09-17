import streamlit as st
import os
import sys
import json
import shutil
import uuid
from datetime import datetime
import tempfile
import re
from dotenv import load_dotenv

load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

from components.logins import make_hashed_password, verify_password, add_user, initialize_users_db

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Get project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Page configuration
st.set_page_config(
    page_title="Visualisation des sujets de conversations",
    page_icon="📊",  # Changed the page icon to a chart/graph icon
    layout="wide",
)


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
    # Custom CSS
    try:
        css_path = os.path.join(os.path.dirname(__file__), '../static/project_manager.css')
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load custom CSS: {e}")
        # Continue without custom CSS

    # Title and description
    st.title("Sujets de Conversations")
    st.markdown("""
        Affichage des sujets de conversations sur la boîte mail de céline uniquement (pour le moment).
    """)

    # Path to the HTML file
    demo_dir = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT)
    topics_html_path = os.path.join(demo_dir, 'email_clusters_interactive.html')

    # Function to display the HTML graph
    def display_html_graph():
        # Check if the HTML file exists
        if os.path.exists(topics_html_path):
            # Read the HTML content
            with open(topics_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Display the HTML content
            st.components.v1.html(html_content, height=600, scrolling=True)
        else:
            st.error(f"Le fichier HTML n'a pas été trouvé: {topics_html_path}")

    # Display the graph
    display_html_graph()
