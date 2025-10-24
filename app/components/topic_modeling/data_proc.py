import pandas as pd
from pyclustering.cluster.kmedoids import kmedoids
from pyclustering.utils import calculate_distance_matrix
import random
import joblib
import json
import numpy as np
from tqdm import tqdm  # Import tqdm for the progress bar
from pathlib import Path

def data_proc():
    # Base directory for artifacts relative to this module
    MODULE_DIR = Path(__file__).resolve().parent

    # Load your original DataFrame
    df = pd.read_csv(MODULE_DIR / "bertopic_output.csv")

    # Load the embeddings
    embeddings = joblib.load(MODULE_DIR / "embeddings_fr.pkl")

    # Check dimensions match
    assert len(df) == embeddings.shape[0], "Mismatch between df rows and embeddings"

    # Add a new column with the vector as a list
    df["embedding"] = [vec.tolist() for vec in embeddings]

    # Optional: Save to file
    df.to_pickle(MODULE_DIR / "df_with_embeddings.pkl")
    df1 = df.copy()


    # Example: Remove rows where column 'B' has value 'X'
    df1 = df1[df1['topic'] != -1]


    df2=df1.copy()


    # Read the topic titles JSON file
    with (MODULE_DIR / 'merged.json').open('r', encoding='utf-8') as f:
        topic_titles = json.load(f)
    #print(topic_titles)
    # Convert the topic_titles dictionary into a lookup table for easy mapping
    topic_mapping = {
        (int(key.split('_')[1]) if isinstance(key, str) and '_' in key else int(key)): value
        for key, value in topic_titles.items()
    }


    # Map the topic column to the corresponding title
    df2['title'] = df2['topic'].map(topic_mapping)

    # Print the updated DataFrame
    print(df2)
    df2.to_pickle(MODULE_DIR / "df2_with_embeddings.pkl")
