import pandas as pd
import joblib
from pathlib import Path


def update_df_with_medoid_indices():
    MODULE_DIR = Path(__file__).resolve().parent

    df4 = pd.read_pickle(MODULE_DIR / "df2_with_embeddings.pkl")
    df3 = pd.read_pickle(MODULE_DIR / "scores_df.pkl")
    topic_kmedoids_results = joblib.load(MODULE_DIR / "topic_kmedoids_results_or.pkl")
    df4['score'] = df4['topic'].map(df3['score'])
    print(df4)
    medoid_dict= topic_kmedoids_results
    # Convert to a dictionary mapping topic → medoid_index
    topic_to_medoid = {topic: v['original_medoid_indices'][0] for topic, v in medoid_dict.items()}
    # Add medoid index as a new column
    df4['medoid_index'] = df4['topic'].map(topic_to_medoid)
    print('****************')
    print(df4)
    df4.to_pickle(MODULE_DIR / "df4_with_embeddings.pkl")
