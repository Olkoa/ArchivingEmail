import json
import sys
import pandas as pd

# -----------------------
# Load data
# -----------------------
if len(sys.argv) <= 1:
    print("❌ No data file provided.")
    sys.exit(1)

filename = sys.argv[1]
df = pd.read_csv(filename)
print("✅ Data received:")
print(df.head())

# -----------------------
# Step 1: Unique Nodes
# -----------------------
unique_emails = pd.unique(df[["sender", "receiver"]].values.ravel())
nodes = [{"id": email, "name": email} for email in unique_emails]

# --- Aggregate interactions for Envoyé ---
edge_map = {}
for _, row in df.iterrows():
    src = str(row["sender"]).strip()
    tgt = str(row["receiver"]).strip()
    if not src or not tgt:
        continue
    pair = tuple(sorted((src, tgt)))
    interaction = {
        "sender": src,
        "receiver": tgt,
        # Include any metadata available for Envoyé (if only sender/receiver, just keep that)
    }
    if pair not in edge_map:
        edge_map[pair] = {
            "id": f"{pair[0]}->{pair[1]}",
            "source": pair[0],
            "target": pair[1],
            "label": f"{pair[0]} ↔ {pair[1]}",
            "count": 1,
            "interactions": [interaction]
        }
    else:
        edge_map[pair]["count"] += 1
        edge_map[pair]["interactions"].append(interaction)

# Nodes are still unique emails
unique_emails = pd.unique(df[["sender", "receiver"]].values.ravel())
nodes = [{"id": email, "name": email} for email in unique_emails]

graph_data = {"nodes": nodes, "edges": list(edge_map.values())}

# Save aggregated graph to JSON directly
with open("components/email_network.json", "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=4)