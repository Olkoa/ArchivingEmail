import streamlit as st
import duckdb
import pandas as pd
import json

# Load the JSON file (ensure the filename is correct)
with open("graph.json") as f:
    graph_data = json.load(f)

# Prepare DataFrames from the JSON data
nodes_df = pd.DataFrame(graph_data["nodes"])
edges_df = pd.DataFrame(graph_data["edges"])

# Set up DuckDB connection
con = duckdb.connect()

# Register DataFrames as DuckDB tables
con.register("nodes_df", nodes_df)
con.register("edges_df", edges_df)

# Create or replace tables in DuckDB
con.execute("CREATE OR REPLACE TABLE nodes AS SELECT * FROM nodes_df")
con.execute("CREATE OR REPLACE TABLE edges AS SELECT * FROM edges_df")

# Streamlit layout
st.title("🕸️ Graph Explorer (DuckDB + JSON)")

# Display full nodes and edges tables
st.subheader("📦 Full Nodes Table")
st.dataframe(con.execute("SELECT * FROM nodes").df(), use_container_width=True)

st.subheader("🔗 Full Edges Table")
st.dataframe(con.execute("SELECT * FROM edges").df(), use_container_width=True)

# Set up session state for the search query if it's not already set
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Define a function to update the search query
def update_search_query():
    st.session_state.search_query = st.session_state.input_query

# Dynamic search bar with on_change to trigger query update
st.subheader("🔍 Dynamic Node Search")
search_query = st.text_input(
    "Start typing to filter nodes:",
    value=st.session_state.search_query,
    key="input_query",
    on_change=update_search_query
)

# Query DuckDB based on the search input
if st.session_state.search_query:
    query = f"""
        SELECT * FROM nodes
        WHERE LOWER(name) LIKE LOWER('%{st.session_state.search_query}%')
           OR LOWER(id) LIKE LOWER('%{st.session_state.search_query}%')
    """
    filtered_nodes = con.execute(query).df()
    st.write(f"🔎 {len(filtered_nodes)} node(s) matched:")
    st.dataframe(filtered_nodes, use_container_width=True)
else:
    st.info("Start typing above to search nodes dynamically.")
