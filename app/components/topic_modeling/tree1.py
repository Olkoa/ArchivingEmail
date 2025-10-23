from scipy.cluster.hierarchy import to_tree
from graphviz import Digraph
import json
import os
def closest_height(target, available):
    return min(available, key=lambda h: abs(h - target))
def build_summary_tree_all_levels(df5, linked, cluster_levels_df, summary_dir, heights, output_path):
    # Load all summaries once
    summary_by_height = {}
    for h in heights:
        json_path = os.path.join(summary_dir, f"topic_summaries_{h:.1f}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                summary_by_height[round(h, 1)] = json.load(f)

    # Convert linkage to tree
    tree, nodes = to_tree(linked, rd=True)

    # Add height to each node
    node_heights = {}
    for i, row in enumerate(linked):
        left, right, dist, _ = row
        node_id = i + len(df5)
        node_heights[node_id] = round(dist, 1)

    # Create Graphviz tree
    dot = Digraph(comment='Summary Tree with Levels')
    dot.attr(rankdir='LR')  # left to right
    dot.attr('node', shape='box')

    # Recursive function to build tree
    def add_nodes(node):
        if node.is_leaf():
            topic = str(df5.iloc[node.id]['topic'])         
            # Example usage for leaf nodes
            approx_height = 0.4
            closest = closest_height(approx_height, summary_by_height.keys())
            label = summary_by_height[closest].get(f"topic_{topic}", f"Topic {topic}")
            #label = summary_by_height[0.4].get(f"topic_{topic}", f"Topic {topic}")
            dot.node(str(node.id), label)
        else:
            node_id = node.id
            height = node_heights.get(node_id, 3.5)  # fallback
            summary_dict = summary_by_height.get(height, {})
            label = summary_dict.get(f"topic_{node_id}", f"Merge {height:.1f}")
            dot.node(str(node_id), label)
            add_nodes(node.left)
            add_nodes(node.right)
            dot.edge(str(node_id), str(node.left.id))
            dot.edge(str(node_id), str(node.right.id))

    add_nodes(tree)
    dot.render(output_path, format='png', cleanup=True)
    print(f"Tree rendered to {output_path}.png")
