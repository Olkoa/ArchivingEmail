import pandas as pd
import numpy as np
from pathlib import Path
import os
import json
from scipy.cluster.hierarchy import fcluster

from .vizz4 import treatement2
from .tree1 import build_summary_tree_all_levels


def build_cluster_tree(topic_graphs_path: Path | str | None = None):
    MODULE_DIR = Path(__file__).resolve().parent

    cluster_levels_df = pd.read_csv(MODULE_DIR / "clusters_by_height_filtered.csv")
    df4 = pd.read_pickle(MODULE_DIR / "df4_with_embeddings.pkl")
    to_cluster_df = pd.read_csv(MODULE_DIR / "clustered_topics_tt.csv")
    # Load later
    linked = np.load(MODULE_DIR / "linked_matrix.npy", allow_pickle=True)

    output_dir = MODULE_DIR / "outputs_by_height"
    output_dir.mkdir(exist_ok=True)
    for col in cluster_levels_df.columns:
        if col.startswith("height_"):
            print(f"Traitement pour {col}")
            cluster_col = col
            height_str = col.replace("height_", "")
            
            # Nom des fichiers pour chaque niveau
            text_json_path = output_dir / f"clustered_texts_{height_str}.json"
            summary_json_path = output_dir / f"topic_summaries_{height_str}.json"
            tree_png_path = output_dir / f"cluster_tree_{height_str}"

            # Appel de traitement
            treatement2(
                to_cluster_df=cluster_levels_df,
                df5=df4,  # ton dataframe d'origine avec colonnes 'text' et 'topic'
                linked=linked,
                cluster_col=cluster_col,
                text_json_path=text_json_path,
                summary_json_path=summary_json_path,
                tree_png_path=tree_png_path
            )
    def get_valid_heights(cluster_levels_df, summary_dir, all_heights):
        valid_heights = []
        for h in all_heights:
            col = f"height_{h:.1f}"
            summary_file = summary_dir / f"topic_summaries_{h:.1f}.json"
            if col in cluster_levels_df.columns and summary_file.exists():
                valid_heights.append(round(h, 1))
        return valid_heights

    # Original range
    all_heights = np.round(np.arange(0.4, 3.6, 0.1), 1).tolist()

    # Filter valid ones
    heights = get_valid_heights(cluster_levels_df, output_dir, all_heights)

    # Now run the tree build
    build_summary_tree_all_levels(
        df5=df4,
        linked=linked,
        cluster_levels_df=cluster_levels_df,
        summary_dir=str(output_dir),
        heights=heights,
        output_path=str(output_dir / "full_tree_all_levels")
    )

    # Define the range of heights you want to explore
    heights = np.arange(0.1, max(linked[:, 2]), 0.1)  # or any suitable step and max

    # Dictionary to store grouped topics at each height
    grouped_topics_by_height = {}

    for h in heights:
        # Step 1: Cut dendrogram at height h
        cluster_labels = fcluster(linked, t=h, criterion='distance')
        
        # Step 2: Assign cluster labels
        to_cluster_df['cluster'] = cluster_labels
        
        # Step 3: Group topics by cluster
        grouped_topics = to_cluster_df.groupby('cluster')['topic'].apply(list)
        
        # Save to dictionary using the height as key
        grouped_topics_by_height[round(h, 2)] = grouped_topics.to_dict()
        

    # Optional: Save all grouped topics by height to JSON
    with (MODULE_DIR / "grouped_topics_all_heights.json").open("w", encoding="utf-8") as f:
        json.dump(grouped_topics_by_height, f, indent=2)
    print("Max linkage height:", linked[:, 2].max())
    for h in np.arange(0.1, 0.5, 0.1):
        labels = fcluster(linked, t=h, criterion='distance')
        print(f"Height {h:.1f} → unique clusters: {len(set(labels))}")


    # Define the range of heights you want to explore
    heights = np.round(np.arange(0.1, max(linked[:, 2]), 0.1), 4)

    # Dictionary to store grouped topics at each height
    grouped_topics_by_height = {}

    # Track previous labels for comparison
    prev_labels = None

    for h in heights:
        # Step 1: Cut dendrogram at height h
        cluster_labels = fcluster(linked, t=h, criterion='distance')
        
        # Only store if cluster configuration changed
        if prev_labels is None or not np.array_equal(cluster_labels, prev_labels):
            # Step 2: Assign cluster labels
            to_cluster_df['cluster'] = cluster_labels

            # Step 3: Group topics by cluster
            grouped_topics = to_cluster_df.groupby('cluster')['topic'].apply(list)

            # Save only when changed
            grouped_topics_by_height[round(h, 2)] = grouped_topics.to_dict()
            prev_labels = cluster_labels
    # Add final merge explicitly at the top dendrogram height
    final_t = round(linked[:, 2].max() + 0.1, 4)  # Ensure it's above the last merge height
    final_labels = fcluster(linked, t=final_t, criterion='distance')

    # Only save if different from the previous
    if not np.array_equal(final_labels, prev_labels):
        to_cluster_df['cluster'] = final_labels
        grouped_topics = to_cluster_df.groupby('cluster')['topic'].apply(list)
        grouped_topics_by_height[round(final_t, 2)] = grouped_topics.to_dict()        

    # Save result to JSON
    filtered_path = MODULE_DIR / "grouped_topics_filtered.json"
    with filtered_path.open("w", encoding="utf-8") as f:
        json.dump(grouped_topics_by_height, f, indent=2)

    # Load clusters_by_height from your JSON file
    with filtered_path.open("r", encoding="utf-8") as f:
        clusters_by_height = json.load(f)

    # Heights sorted as floats (keys are strings in JSON)
    sorted_heights = sorted(clusters_by_height.keys(), key=float)

    # Load summaries for each height from your summary JSON files
    summaries_by_height = {}
    for h in sorted_heights:
        summary_file = output_dir / f"topic_summaries_{h}.json"
        if summary_file.exists():
            with summary_file.open("r", encoding="utf-8") as sf:
                summaries_by_height[h] = json.load(sf)
        else:
            summaries_by_height[h] = {}

    # Function to get summary or fallback to Merge <height>
    def get_summary_or_merge(cluster_id, height):
        summary = summaries_by_height.get(height, {}).get(f"topic_{cluster_id}", "")
        if summary and summary.strip():
            return summary
        else:
            return f"Merge {height}"


    # Build a node with name, summary, children
    def build_tree_node(height, cluster_id, topics):
        return {
            "name": str(cluster_id),
            "summary": get_summary_or_merge(cluster_id, height),
            "children": []
        }

    # Build nodes map for all heights
    nodes_map = {}

    bottom_height = sorted_heights[0]
    # Create leaf nodes at bottom height
    nodes_map[bottom_height] = {}
    for cid, topics in clusters_by_height[bottom_height].items():
        nodes_map[bottom_height][cid] = build_tree_node(bottom_height, cid, topics)

    # Build internal nodes upwards
    for i in range(1, len(sorted_heights)):
        curr_height = sorted_heights[i]
        prev_height = sorted_heights[i - 1]
        nodes_map[curr_height] = {}

        for cid, topics in clusters_by_height[curr_height].items():
            node = build_tree_node(curr_height, cid, topics)

            # Find children clusters from previous height fully included in this cluster
            children = []
            for pcid, ptopics in clusters_by_height[prev_height].items():
                if set(ptopics).issubset(set(topics)):
                    children.append(nodes_map[prev_height][pcid])

            node["children"] = children
            nodes_map[curr_height][cid] = node

    # Create root node(s) at top height
    top_height = sorted_heights[-1]
    root_children = list(nodes_map[top_height].values())

    if len(root_children) == 1:
        root_node = root_children[0]
    else:
        root_node = {
            "name": "root",
            "summary": f"Merge {top_height}",
            "children": root_children
        }

    # Save as JSON for d3.js consumption
    destination = Path(topic_graphs_path) if topic_graphs_path else (MODULE_DIR / "cluster_summary_tree.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as f:
        json.dump(root_node, f, indent=2, ensure_ascii=False)
