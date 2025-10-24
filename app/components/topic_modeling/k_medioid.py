import pandas as pd
from pyclustering.cluster.kmedoids import kmedoids
from pyclustering.utils import calculate_distance_matrix
import random
import joblib
import numpy as np
from tqdm import tqdm  # Import tqdm for the progress bar
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent


def _load_topic_dataframe():
    df = pd.read_csv(MODULE_DIR / "bertopic_output.csv")
    embeddings = joblib.load(MODULE_DIR / "embeddings_fr.pkl")

    if len(df) != embeddings.shape[0]:
        raise ValueError("Mismatch between df rows and embeddings")

    df = df.copy()
    df["embedding"] = [vec.tolist() for vec in embeddings]
    df.to_pickle(MODULE_DIR / "df_with_embeddings.pkl")

    # Filter out outliers (topic == -1)
    return df[df['topic'] != -1].copy()


def compute_kmedoids_per_topic(df, n_clusters):
    topic_results = {}
    grouped = df.groupby('topic')

    for topic, group in tqdm(grouped, desc="Processing Topics", total=len(grouped)):
        topic_indices = group.index.tolist()
        topic_embeddings = np.array(group['embedding'].tolist())

        n_samples = topic_embeddings.shape[0]
        if n_samples == 0:
            continue

        medoid_count = max(1, min(n_clusters, n_samples))
        initial_medoids = random.sample(range(n_samples), medoid_count)
        distance_matrix = calculate_distance_matrix(topic_embeddings)

        kmedoids_instance = kmedoids(
            distance_matrix,
            initial_medoids,
            data_type='distance_matrix',
            ccore=False,
        )
        kmedoids_instance.process()

        clusters = kmedoids_instance.get_clusters()
        medoid_indices = kmedoids_instance.get_medoids()
        original_medoid_indices = [topic_indices[i] for i in medoid_indices]

        labels = np.zeros(n_samples, dtype=int)
        for cluster_id, cluster in enumerate(clusters):
            for idx in cluster:
                labels[idx] = cluster_id

        topic_results[topic] = {
            'labels': labels.tolist(),
            'medoid_indices': medoid_indices,
            'original_medoid_indices': original_medoid_indices
        }

    return topic_results


def run_kmedoid_clustering(n_clusters: int = 1, save: bool = True):
    df_filtered = _load_topic_dataframe()
    results = compute_kmedoids_per_topic(df_filtered, n_clusters)

    if save:
        joblib.dump(results, MODULE_DIR / "topic_kmedoids_results_or.pkl")
        print("✅ K-Medoids clustering results saved.")

    return results


if __name__ == "__main__":
    run_kmedoid_clustering()
