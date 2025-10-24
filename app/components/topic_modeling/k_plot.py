import pandas as pd
from pyclustering.cluster.kmedoids import kmedoids
from pyclustering.utils import calculate_distance_matrix
import random
import joblib
import numpy as np
from tqdm import tqdm  # Import tqdm for the progress bar
from pathlib import Path


def kmedoid_plotting():
    # Base directory for topic modeling artifacts
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

    df1
    topic_kmedoids_results = joblib.load(MODULE_DIR / 'topic_kmedoids_results_or.pkl')

    def plot_all_clusters_one_plot(df, topic_results):
        import matplotlib.pyplot as plt
        import numpy as np
        from sklearn.decomposition import PCA
        import matplotlib.cm as cm

        # Collect all embeddings and corresponding topic labels
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

            # Store index of medoid within this topic only
            medoid_points.append(embeddings[medoid_idx])
            medoid_labels.append(topic)

        # Reduce to 2D
        pca = PCA(n_components=2)
        reduced_embeddings = pca.fit_transform(all_embeddings)
        reduced_medoid_points = pca.transform(np.array(medoid_points))

        # Map topics to colors
        unique_topics = list(set(all_labels))
        topic_to_color = {topic: cm.tab20(i % 20) for i, topic in enumerate(unique_topics)}

        # Plot
        plt.figure(figsize=(12, 10))

        for topic in unique_topics:
            indices = [i for i, label in enumerate(all_labels) if label == topic]
            points = reduced_embeddings[indices]
            plt.scatter(points[:, 0], points[:, 1], color=topic_to_color[topic], label=f"Topic {topic}", alpha=0.6)

        # Plot medoids
        for i, point in enumerate(reduced_medoid_points):
            plt.scatter(point[0], point[1], color='red', marker='*', s=250, edgecolor='black', label='Medoid' if i == 0 else "")

        plt.title("All Topic Clusters with Medoids")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.legend(loc='best', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    # plot_all_clusters_one_plot(df1, topic_kmedoids_results)
