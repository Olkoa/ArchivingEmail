import streamlit as st
import os
import sys
import json
import shutil
import uuid
from datetime import datetime
import tempfile
import re

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
demo_dir = os.path.join(project_root, 'data', 'Projects', 'Projet Demo')
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
