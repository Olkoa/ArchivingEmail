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
# Nodes
# -----------------------
unique_emails = pd.unique(df[["sender", "receiver"]].values.ravel())
nodes = [{"id": email, "name": email} for email in unique_emails]

# -----------------------
# Build unique edges
# -----------------------
unique_pairs = {}
for _, row in df.iterrows():
    src = str(row["sender"])
    tgt = str(row["receiver"])
    if not src or not tgt:
        continue
    # Undirected key (sorted tuple)
    pair = tuple(sorted((src, tgt)))
    if pair not in unique_pairs:
        unique_pairs[pair] = {
            "id": f"{src}->{tgt}",
            "source": src,
            "target": tgt,
            "label": f"{src} → {tgt}",
            "count": 1
        }
    else:
        # Increment count for extra info (optional)
        unique_pairs[pair]["count"] += 1

edges = list(unique_pairs.values())

# -----------------------
# Combine + Export
# -----------------------
graph_data = {"nodes": nodes, "edges": edges}

with open("components/email_network.json", "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=4)

print(f"✅ Exported {len(nodes)} nodes and {len(edges)} unique edges to email_network.json")