import pandas as pd
import json
from llm_summary import summarize_all_topics
import numpy as np
import pandas as pd
from sklearn.metrics import pairwise_distances
from graphviz import Digraph
from scipy.cluster.hierarchy import to_tree
import re
def extract_last_message_single_line(full_text):
    # Pattern to match typical forwarded/replied parts
    pattern = r'(De :|Envoyé :|À :|Objet :|-------- Message transféré --------|Le \d{2}/\d{2}/\d{4} à \d{2}:\d{2})'
    
    # Split at the first occurrence of any pattern
    split_text = re.split(pattern, full_text, flags=re.IGNORECASE)
    
    # Keep only the first part (last message)
    last_message = split_text[0].strip()
    
    return last_message
def treatement2(to_cluster_df, df5, linked, cluster_col, text_json_path, summary_json_path, tree_png_path):
    print(to_cluster_df[cluster_col].nunique())
    df_filtered = to_cluster_df[['topic', cluster_col]]
    df_filtered_sorted = df_filtered.sort_values(by='topic')
    df5['topic'] = df5['topic'].astype(str)
    df_filtered_sorted['topic'] = df_filtered_sorted['topic'].astype(str)
    df_merged = pd.merge(df5, df_filtered_sorted[['topic', cluster_col]], on='topic', how='left')
    print(df_merged[cluster_col].nunique())
    dfm = df_merged

    # Group and sample
    cluster_data = {}
    grouped = dfm.groupby(cluster_col)
    for cluster, group in grouped:
        sample = group.sample(min(len(group), 100))
        
        texts = [extract_last_message_single_line(t) for t in sample['text'].tolist()]
        cluster_data[f"topic_{cluster}"] = texts

    # Save text samples
    with open(text_json_path, 'w', encoding='utf-8') as f:
        json.dump(cluster_data, f, indent=4, ensure_ascii=False)

    print(f"Saved clustered texts to {text_json_path}")
    
    # Call summarizer
    summarize_all_topics(text_json_path,output_path=summary_json_path)

    # Read summaries
    with open(summary_json_path, 'r', encoding='utf-8') as f:
        topic_summaries = json.load(f)

    finaldf = to_cluster_df.copy()
    finaldf['topic_summary'] = finaldf[cluster_col].apply(lambda x: topic_summaries.get(f"topic_{x}", "Résumé non disponible"))

    # Create cluster tree
    tree, nodes = to_tree(linked, rd=True)
    dot = Digraph(comment='Cluster Tree')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box')

    def add_nodes(node):
        if node.is_leaf():
            try:
                label = str(finaldf['topic_summary'].iloc[node.id])
                dot.node(str(node.id), label)
            except:
                dot.node(str(node.id), "Résumé indisponible")
        else:
            dot.node(str(node.id), f"Merge\n{node.dist:.2f}")
            add_nodes(node.left)
            add_nodes(node.right)
            dot.edge(str(node.id), str(node.left.id))
            dot.edge(str(node.id), str(node.right.id))

    add_nodes(tree)
    dot.render(tree_png_path, format='png')
    print(f"Saved cluster tree to {tree_png_path}.png")

    return finaldf
