import numpy as np
import pickle
import pandas as pd
from config import EMBEDDINGS_PATH, CHUNKS_PATH, VIS_EMB_2D, VIS_LABELS, VIS_CHUNKS

def load_data():
    # embeddings et chunks
    embeddings_all = np.load(EMBEDDINGS_PATH)
    chunks_all = np.load(CHUNKS_PATH, allow_pickle=True).tolist()

    # visu
    emb_2d = np.load(VIS_EMB_2D)
    labels = np.load(VIS_LABELS)
    with open(VIS_CHUNKS, "rb") as f:
        chunks_vis = pickle.load(f)

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
