import streamlit as st
import streamlit.components.v1 as components
import json

# Function to load the HTML file
def load_html(file_path):
    with open(file_path, 'r') as f:
        return f.read()

# Function to load the JSON data
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Load the HTML content
html_file_path = 'viz copy 18.html'  # Adjust path if needed
html_content = load_html(html_file_path)

# Load the JSON data
json_file_path = 'email_network.json'  # Adjust path if needed
json_data = load_json(json_file_path)

html_content_with_json = html_content.replace("__GRAPH_DATA__", json.dumps(json_data))

# Embed the HTML content inside the Streamlit app
st.title("Graph Visualization with D3.js")
components.html(html_content_with_json,width=1200,height=800)
