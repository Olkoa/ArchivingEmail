from scipy.spatial.distance import cdist
import pandas as pd
from pyclustering.cluster.kmedoids import kmedoids
from pyclustering.utils import calculate_distance_matrix
import random
import joblib
import json
import numpy as np
from tqdm import tqdm  # Import tqdm for the progress bar
from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import matplotlib.cm as cm

def k_distance_plot():
    MODULE_DIR = Path(__file__).resolve().parent

    df2 = pd.read_pickle(MODULE_DIR / "df2_with_embeddings.pkl")
    def compute_cluster_distances(df, topic_results):
        inter_cluster_dists = {}
        intra_cluster_dists = {}

        medoid_vectors = []
        topic_order = []

        for topic, info in topic_results.items():
            topic_df = df[df['topic'] == topic]

            if topic_df.empty:
                continue

            embeddings = np.array(topic_df['embedding'].tolist())
            medoid_idx = info['medoid_indices'][0]
            medoid_vector = embeddings[medoid_idx]

            # Store medoid vector for inter-cluster distance
            medoid_vectors.append(medoid_vector)
            topic_order.append(topic)

            # Intra-cluster distance: mean distance to medoid
            distances = cdist(embeddings, [medoid_vector])
            mean_intra = distances.mean()
            intra_cluster_dists[topic] = mean_intra

        # Inter-cluster distances between all medoids
        medoid_vectors = np.array(medoid_vectors)
        inter_d_matrix = cdist(medoid_vectors, medoid_vectors)

        # Store as DataFrame for easier inspection
        inter_cluster_df = pd.DataFrame(inter_d_matrix, index=topic_order, columns=topic_order)

        return intra_cluster_dists, inter_cluster_df
    topic_kmedoids_results = joblib.load(MODULE_DIR / "topic_kmedoids_results_or.pkl")
    intra_dists, inter_dists_df = compute_cluster_distances(df2, topic_kmedoids_results)

    print("Intra-cluster distances:")
    for topic, dist in intra_dists.items():
        print(f"Topic {topic}: {dist:.4f}")

    print("\nInter-cluster distance matrix:")
    print(inter_dists_df)
    def compute_cluster_scores(intra_dists, inter_dists_df, cluster_sizes, alpha=1.0, beta=1.0, gamma=1.0):
        scores = {}
        max_inter = inter_dists_df.values.max()
        max_size = max(cluster_sizes.values())
        
        for topic in intra_dists:
            intra = intra_dists[topic]
            # Mean inter-cluster distance from this cluster to all others (excluding self)
            inter = inter_dists_df.loc[topic].drop(topic).mean()
            size = cluster_sizes.get(topic, 1)

            # Composite score
            score = (
                alpha * (1 / (intra + 1e-8)) +
                beta * (inter / max_inter) +
                gamma * (size / max_size)
            )
            scores[topic] = score
        
        return scores
    # Get cluster sizes
    cluster_sizes = df2['topic'].value_counts().to_dict()

    # Compute scores
    cluster_scores = compute_cluster_scores(intra_dists, inter_dists_df, cluster_sizes)

    # Convert to DataFrame for easier viewing
    scores_df = pd.DataFrame.from_dict(cluster_scores, orient='index', columns=['score'])
    #scores_df = scores_df.sort_values('score', ascending=False)
    print(scores_df)
    scores_df.to_pickle(MODULE_DIR / "scores_df.pkl")
    def plot_all_clusters_one_plot(df, topic_results, cluster_scores=None):


        all_embeddings = []
        all_labels = []
        medoid_points = []
        medoid_labels = []

        for topic, info in topic_results.items():
            topic_df = df[df['topic'] == topic]
            embeddings = np.array(topic_df['embedding'].tolist())

            if embeddings.shape[0] == 0:
                continue

            medoid_idx = info['medoid_indices'][0]

            all_embeddings.extend(embeddings)
            all_labels.extend([topic] * len(embeddings))

            medoid_points.append(embeddings[medoid_idx])
            medoid_labels.append(topic)

        pca = PCA(n_components=2)
        reduced_embeddings = pca.fit_transform(all_embeddings)
        reduced_medoid_points = pca.transform(np.array(medoid_points))

        unique_topics = list(set(all_labels))
        topic_to_color = {topic: cm.tab20(i % 20) for i, topic in enumerate(unique_topics)}

        plt.figure(figsize=(12, 10))

        for topic in unique_topics:
            indices = [i for i, label in enumerate(all_labels) if label == topic]
            points = reduced_embeddings[indices]
            plt.scatter(points[:, 0], points[:, 1], color=topic_to_color[topic], label=f"Topic {topic}", alpha=0.6)

        # Normalize scores for marker size
        sizes = []
        if cluster_scores:
            raw_scores = [cluster_scores.get(topic, 1) for topic in medoid_labels]
            min_score, max_score = min(raw_scores), max(raw_scores)
            sizes = [100 + 500 * ((s - min_score) / (max_score - min_score + 1e-8)) for s in raw_scores]
        else:
            sizes = [250] * len(medoid_labels)

        for i, point in enumerate(reduced_medoid_points):
            plt.scatter(point[0], point[1], 
                        color='black', 
                        marker='d',  # 'P' for filled plus, change as desired
                        s=sizes[i], 
                        edgecolor='white',
                        linewidths=1.5,
                        label='Medoid' if i == 0 else "")

        plt.title("All Topic Clusters with Medoids (Sized by Score)")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.legend(loc='best', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    plot_all_clusters_one_plot(df2, topic_kmedoids_results, cluster_scores={int(k): v for k, v in scores_df['score'].to_dict().items()})
