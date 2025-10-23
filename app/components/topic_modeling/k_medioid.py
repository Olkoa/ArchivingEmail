import pandas as pd
from pyclustering.cluster.kmedoids import kmedoids
from pyclustering.utils import calculate_distance_matrix
import random
import joblib
import numpy as np
from tqdm import tqdm  # Import tqdm for the progress bar

import pandas as pd
import joblib

# Load your original DataFrame
df = pd.read_csv("bertopic_output.csv")  # Replace with your actual file path


# Load the embeddings
embeddings = joblib.load("embeddings_fr.pkl")

# Check dimensions match
assert len(df) == embeddings.shape[0], "Mismatch between df rows and embeddings"

# Add a new column with the vector as a list
df["embedding"] = [vec.tolist() for vec in embeddings]

# Optional: Save to file
df.to_pickle("df_with_embeddings.pkl")
df1 = df.copy()

# Example: Remove rows where column 'B' has value 'X'
df1 = df1[df1['topic'] != -1]

df1




# Function to compute K-Medoids for each topic
def compute_kmedoids_per_topic(df1, n_clusters):
    # Dictionary to store the results per topic
    topic_results = {}

    # Group the DataFrame by 'topic'
    grouped = df1.groupby('topic')

    # Use tqdm to show progress for each topic
    for topic, group in tqdm(grouped, desc="Processing Topics", total=len(grouped)):
        # Get the indices for the current topic
        topic_indices = group.index.tolist()

        # Extract embeddings for the current topic from the 'embedding' column
        topic_embeddings = np.array(group['embedding'].tolist())  # Convert list of embeddings to a numpy array

        # Run K-Medoids clustering for the current topic
        n_samples = topic_embeddings.shape[0]
        initial_medoids = random.sample(range(n_samples), n_clusters)
        print("calcule dist")
        # Create distance matrix
        distance_matrix = calculate_distance_matrix(topic_embeddings)
        print("clust")
        # K-Medoids clustering
        kmedoids_instance = kmedoids(distance_matrix, initial_medoids, data_type='distance_matrix')
        print("fin")
        kmedoids_instance.process()

        clusters = kmedoids_instance.get_clusters()
        medoid_indices = kmedoids_instance.get_medoids()
        original_medoid_indices = [topic_indices[i] for i in medoid_indices]

        # Build labels
        labels = np.zeros(n_samples, dtype=int)
        for cluster_id, cluster in enumerate(clusters):
            for idx in cluster:
                labels[idx] = cluster_id

        # Store the results for this topic
        topic_results[topic] = {
            'labels': labels.tolist(),
            'medoid_indices': medoid_indices,
            'original_medoid_indices': original_medoid_indices
        }

    return topic_results

# Example usage
n_clusters = 1  # Adjust as needed
topic_kmedoids_results = compute_kmedoids_per_topic(df1, n_clusters)

# Optionally: Save results to a file
joblib.dump(topic_kmedoids_results, "topic_kmedoids_results_or.pkl")
print("✅ K-Medoids clustering results saved.")

