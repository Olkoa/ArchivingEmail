import json
import sys
import pandas as pd

# Get filename from args
if len(sys.argv) > 1:
    filename = sys.argv[1]
    df = pd.read_csv(filename)
    print("✅ Data received:")
    print(df.head())
else:
    print("❌ No data file provided.")


# Step 1: Get unique nodes (email addresses)
unique_emails = pd.unique(df[["sender", "receiver"]].values.ravel())

# Create node objects
nodes = [{"id": email, "name": email} for email in unique_emails]

# Step 2: Create edges
edges = []
for i, row in df.iterrows():
    edges.append({
        "id": f"e{i}",
        "source": row["sender"],
        "target": row["receiver"],
        "label": f"{row['sender']} → {row['receiver']}",
        "date":row["date"],
        "body":row["body"],
        "subject":row["subject"],
    })

# Combine into Sigma.js format
graph_data = {
    "nodes": nodes,
    "edges": edges
}

# Step 3: Export to JSON
with open("components/email_network.json", "w") as f:
    json.dump(graph_data, f, indent=4)

print("✅ Exported to email_network.json")