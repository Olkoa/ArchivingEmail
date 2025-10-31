import numpy as np
import pickle
import pandas as pd

from src.topic.config import (
    chunks_path,
    chunk_metadata_path,
    embeddings_path,
    vis_chunks_path,
    vis_emb_2d_path,
    vis_labels_path,
)


def load_data(project: str | None = None):
    embeddings_file = embeddings_path(project)
    chunks_file = chunks_path(project)
    emb_2d_file = vis_emb_2d_path(project)
    labels_file = vis_labels_path(project)
    vis_chunks_file = vis_chunks_path(project)
    metadata_file = chunk_metadata_path(project)

    embeddings_all = np.load(embeddings_file)
    chunks_all = np.load(chunks_file, allow_pickle=True).tolist()

    emb_2d = np.load(emb_2d_file)
    labels = np.load(labels_file)
    with open(vis_chunks_file, "rb") as handle:
        chunks_vis = pickle.load(handle)

    metadata_df = None
    if metadata_file.exists():
        try:
            metadata_df = pd.read_pickle(metadata_file)
            metadata_df = metadata_df.reset_index(drop=True)
        except Exception as metadata_error:
            print(f"[semantic] Unable to load chunk metadata ({metadata_file}): {metadata_error}")
            metadata_df = None
    else:
        metadata_df = None

    # mapping chunk -> index
    chunk_to_idx = {c: i for i, c in enumerate(chunks_all)}
    vis_indices = [chunk_to_idx[c] for c in chunks_vis]
    embeddings_vis = embeddings_all[vis_indices]

    # dataframe
    df_vis = pd.DataFrame({
        "x": emb_2d[:, 0],
        "y": emb_2d[:, 1],
        "cluster": labels.astype(str),
        "chunk": chunks_vis
    })
    df_vis["cluster_id"] = labels

    if metadata_df is not None:
        if len(metadata_df) == len(df_vis):
            for column in metadata_df.columns:
                df_vis[column] = metadata_df[column]
        else:
            merge_cols = ["chunk_text", "chunk_id", "message_id"]
            available_merge_cols = [col for col in merge_cols if col in metadata_df.columns and col != "chunk_text"]
            if "chunk_text" in metadata_df.columns:
                available_merge_cols.insert(0, "chunk_text")
            if available_merge_cols:
                df_vis = df_vis.merge(
                    metadata_df,
                    left_on=available_merge_cols[0],
                    right_on=available_merge_cols[0],
                    how="left",
                    suffixes=("", "_meta")
                )
            else:
                print("[semantic] Chunk metadata shape mismatch and no matching columns for merge; skipping enrichment.")

    return embeddings_vis, df_vis
