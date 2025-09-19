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
    sys.exit()

# Step 1: Get unique nodes (email addresses)
unique_emails = pd.unique(df[["sender", "receiver"]].values.ravel())
nodes = [{"id": email, "name": email} for email in unique_emails]

# Step 2: Aggregate edges (group interactions by sender-receiver pair)
edge_map = {}

for _, row in df.iterrows():
    key = (row["sender"], row["receiver"])
    if key not in edge_map:
        edge_map[key] = {
            "id": f"{row['sender']}->{row['receiver']}",
            "source": row["sender"],
            "target": row["receiver"],
            "label": f"{row['sender']} → {row['receiver']}",
            "interactions": []  # store all interactions here
        }
    edge_map[key]["interactions"].append({
        "date": row["date"],
        "subject": row["subject"],
        "body": row["body"]
    })

# Convert edge_map to list
edges = list(edge_map.values())

# Step 3: Combine into Sigma.js format
graph_data = {
    "nodes": nodes,
    "edges": edges
}

# Step 4: Export to JSON
with open("components/email_network.json", "w") as f:
    json.dump(graph_data, f, indent=4)

print(f"✅ Exported {len(nodes)} nodes and {len(edges)} edges to components/email_network.json")