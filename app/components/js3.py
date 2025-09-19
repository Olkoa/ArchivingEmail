import json
import sys
import pandas as pd

# --- Load CSV ---
if len(sys.argv) <= 1:
    print("❌ No data file provided.")
    sys.exit()

filename = sys.argv[1]
df = pd.read_csv(filename)
print("✅ Data received:")
print(df.head())

# --- Normalize all emails ---
def normalize_email(x):
    return str(x).strip().lower() if pd.notna(x) else ""

df["sender"] = df["sender"].apply(normalize_email)
df["receiver"] = df["receiver"].apply(normalize_email)

# Step 1: Unique nodes
unique_emails = pd.unique(df[["sender", "receiver"]].values.ravel())
nodes = [{"id": email, "name": email} for email in unique_emails if email]

# Step 2: Aggregate edges
edge_map = {}

for _, row in df.iterrows():
    sender, receiver = row["sender"], row["receiver"]
    if not sender or not receiver:
        continue  # skip invalid rows
    key = (sender, receiver)
    if key not in edge_map:
        edge_map[key] = {
            "id": f"{sender}->{receiver}",
            "source": sender,
            "target": receiver,
            "label": f"{sender} → {receiver}",
            "interactions": []
        }
    edge_map[key]["interactions"].append({
        "date": row.get("date", ""),
        "subject": row.get("subject", ""),
        "body": row.get("body", "")
    })

edges = list(edge_map.values())

# --- Debug: print interaction counts ---
for e in edges[:5]:
    print(f"{e['id']} → {len(e['interactions'])} interactions")

# Step 3: Export
graph_data = {"nodes": nodes, "edges": edges}
with open("components/email_network.json", "w") as f:
    json.dump(graph_data, f, indent=4)

print(f"✅ Exported {len(nodes)} nodes and {len(edges)} edges to components/email_network.json")