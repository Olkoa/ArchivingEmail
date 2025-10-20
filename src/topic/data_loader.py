import numpy as np
import pickle
import pandas as pd

from src.topic.config import (
    chunks_path,
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

    embeddings_all = np.load(embeddings_file)
    chunks_all = np.load(chunks_file, allow_pickle=True).tolist()

    emb_2d = np.load(emb_2d_file)
    labels = np.load(labels_file)
    with open(vis_chunks_file, "rb") as handle:
        chunks_vis = pickle.load(handle)

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

    return embeddings_vis, df_vis
