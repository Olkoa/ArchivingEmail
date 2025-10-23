import re
import json
from collections import defaultdict

# Path to your DOT file
dot_file = "cluster_tree f"

# Read the DOT file content
with open(dot_file, "r", encoding="utf-8") as f:
    dot_data = f.read()

# Parse nodes and labels
node_pattern = re.compile(r'(\d+)\s+\[label="(.+?)"\]', re.DOTALL)
edge_pattern = re.compile(r'(\d+)\s+->\s+(\d+)')

nodes = {}
children_map = defaultdict(list)
parents = {}

# Extract nodes
for match in node_pattern.finditer(dot_data):
    node_id = match.group(1)
    label = match.group(2).replace('\n', ' ').strip()
    nodes[node_id] = label

# Extract edges
for match in edge_pattern.finditer(dot_data):
    parent, child = match.group(1), match.group(2)
    children_map[parent].append(child)
    parents[child] = parent

# Find root (a node that is not a child of any node)
root_candidates = set(nodes.keys()) - set(parents.keys())
if not root_candidates:
    raise ValueError("No root node found.")
root_id = root_candidates.pop()

# Recursive function to build tree
def build_tree(node_id):
    return {
        "name": node_id,
        "summary": nodes[node_id],
        "children": [build_tree(child_id) for child_id in children_map.get(node_id, [])]
    }

tree = build_tree(root_id)

# Save as JSON
with open("treeDataf.json", "w", encoding="utf-8") as f:
    json.dump(tree, f, ensure_ascii=False, indent=2)

print("treeData.json generated successfully.")
