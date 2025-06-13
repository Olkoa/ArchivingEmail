import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import json
import subprocess

# ------------------------
# Streamlit UI
# ------------------------

st.title("📬 Email Data Analysis ")

# Load folder path
folder_path = os.path.dirname(__file__)

# Load the pre-parsed CSV
csv_path = os.path.join(folder_path, "temp_data_full.csv")

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
    html = load_html("viz copy 29.html")
    json_path = os.path.join(folder_path, "email_network_full.json")
    if os.path.exists(json_path):
        graph_data = load_json("email_network_full.json")
        html = html.replace("__GRAPH_DATA__", json.dumps(graph_data))
        components.html(html, width=1200, height=800)
    else:
        st.error("❌ JSON file 'email_network.json' not found.")
