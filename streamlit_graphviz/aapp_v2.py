import os
import pandas as pd
import email
from email.policy import default
import streamlit.components.v1 as components
import duckdb
import streamlit as st

# Step 1: Define folder path
eml_folder = "Archive"
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
df.to_csv('emails_data1.csv', index=False)  # The index=False argument prevents writing row indices
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
query = """
SELECT 
    LEAST(sender, receiver) AS contact_1,
    GREATEST(sender, receiver) AS contact_2,
    COUNT(*) AS email_count
FROM emails
GROUP BY contact_1, contact_2
ORDER BY email_count DESC;
"""
result = con.execute(query).fetchdf()

# Step 6: Display data with Streamlit
st.title('Email Data Analysis')

# Display the results of the query in a table format
st.write("Top email pairs by count:")
st.dataframe(result)

# Optional: Display the full DataFrame in Streamlit
st.write("Full DataFrame of emails:")
st.dataframe(df)

# Total number of emails parsed
st.write(f"✔️ Total emails parsed: {len(df)}")
import subprocess

# Save DataFrame to CSV (or Parquet if you prefer)
df.to_csv("temp_data.csv", index=False)

# Button to run script and pass data
if st.button("🚀 Run Extra Script with Data"):
    with st.spinner("Running script..."):
        try:
            result = subprocess.run(["python", "js.py", "temp_data.csv"],
                                    capture_output=True, text=True, check=True)
            st.success("✅ Script executed successfully!")
            st.text(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error("❌ Failed to run the script.")
            st.text(e.stderr)
from pathlib import Path
import shutil
import streamlit as st
# Folder path where the files are located
folder_path = os.path.dirname(__file__)

# Button to run the visualization
if st.button("🚀 Run Script with Data"):
    # Path to your viz.html file
    html_path = os.path.join(folder_path, "viz.html")

    # Read the HTML content
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Embed the HTML content into the Streamlit app
    components.html(html_content, height=600)
    st.write(f"ccessible in the same")
    # Make sure data.json is accessible
    #st.write("Ensure55555 that data.json is accessible in the same folder.")

import streamlit as st
import streamlit.components.v1 as components
import os

# Example: load the HTML
html_path = os.path.join(folder_path, "viz.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()


    


import json

# Read JSON data
json_path = os.path.join(folder_path, "email_network.json")
with open(json_path, "r") as f:
    data_json = json.load(f)

# Read HTML and inject the JSON directly
html_path = os.path.join(folder_path, "viz2.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()
# Show it in Streamlit
if st.button("🚀 Run Scrith Data"):
# For example, replace a placeholder in HTML like {{DATA_JSON}}
    html_content = html_content.replace("__GRAPH_DATA__", json.dumps(data_json))

    # Display in Streamlit
    components.html(html_content, height=600,)
 