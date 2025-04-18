import streamlit as st
import streamlit.components.v1 as components
import json

# Load the JSON data
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Load the HTML template
def load_html(file_path):
    with open(file_path, 'r') as f:
        return f.read()

# File paths
json_data = load_json("email_network.json")
fullscreen_html_template = load_html("viz copy 13.html")

# Replace the placeholder with JSON data
html_with_data = fullscreen_html_template.replace("__GRAPH_DATA__", json.dumps(json_data))

# Save the final HTML to a file
with open("fullscreen_graph_rendered.html", "w") as f:
    f.write(html_with_data)

# UI
st.title("Graph Visualization")
st.markdown("Click below to open a full screen view of the graph in a new tab.")

# Button that links to the generated HTML
st.markdown(
    f"""
    <a href="fullscreen_graph_rendered.html" target="_blank">
        <button style="padding:10px 20px;font-size:16px;">Open Full Screen</button>
    </a>
    """,
    unsafe_allow_html=True
)

# Also embed the graph inline
components.html(html_with_data, height=800, width=1200)
