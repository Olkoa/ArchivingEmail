import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import pairwise_distances
from graphviz import Digraph
from graphviz.backend import ExecutableNotFound
from scipy.cluster.hierarchy import to_tree

from .gpt4_1 import summarize_all_topics

def _sanitize_text(value: str) -> str:
    if value is None:
        return ""
    return str(value).encode("utf-8", errors="replace").decode("utf-8")


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
        
        texts = [
            _sanitize_text(extract_last_message_single_line(t))
            for t in sample['text'].tolist()
        ]
        sanitized_cluster_texts = []
        for text in texts:
            clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
            clean_text = clean_text.replace("\x00", "")
            clean_text = "".join(ch for ch in clean_text if ch >= " " or ch in ("\n", "\t"))
            sanitized_cluster_texts.append(clean_text)

        cluster_data[f"topic_{cluster}"] = sanitized_cluster_texts

    # Save text samples
    text_json_path = Path(text_json_path)
    summary_json_path = Path(summary_json_path)
    tree_png_path = Path(tree_png_path)

    text_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    tree_png_path.parent.mkdir(parents=True, exist_ok=True)

    with text_json_path.open('w', encoding='utf-8') as f:
        json.dump(cluster_data, f, indent=4, ensure_ascii=False)

    print(f"Saved clustered texts to {text_json_path}")
    
    # Call summarizer
    summarize_all_topics(text_json_path, output_path=summary_json_path)

    if not summary_json_path.exists():
        # Fallback summaries if LLM call failed
        fallback = {}
        for cluster, texts in cluster_data.items():
            if texts:
                excerpt = _sanitize_text(texts[0])[:280]
                fallback[cluster] = excerpt if excerpt else "Résumé indisponible"
            else:
                fallback[cluster] = "Résumé indisponible"

        with summary_json_path.open('w', encoding='utf-8') as f:
            json.dump(fallback, f, indent=4, ensure_ascii=False)
        print(f"⚠️ Sommaires LLM indisponibles, utilisation d'un résumé basique pour {summary_json_path}")

    # Read summaries
    with summary_json_path.open('r', encoding='utf-8') as f:
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
    try:
        dot.render(tree_png_path, format='png')
        print(f"Saved cluster tree to {tree_png_path}.png")
    except ExecutableNotFound:
        print("⚠️ Graphviz 'dot' executable not found; skipping tree rendering.")

    return finaldf
