import numpy as np
import pickle
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt

import os
from dotenv import load_dotenv
load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

base_dir = Path(__file__).parent.parent
output_folder = base_dir.parent / "data" / "Projects" / ACTIVE_PROJECT / "clustering" / "topic" / "optimize_dbscan"
embeddings_path = output_folder.parent / "topics_embeddings.npy"
chunks_path = output_folder.parent / "topics_chunks.npy"

embeddings = np.load(embeddings_path)
chunks = np.load(chunks_path, allow_pickle=True).tolist()

model_path = output_folder / "topics_eps=0.20_min=10_metric=cosine_model.pkl"
with open(model_path, "rb") as f:
    db = pickle.load(f)
labels_db = db.labels_

print(f"Clusters DBSCAN valides : {len(np.unique(labels_db[labels_db!=-1]))}, Outliers : {np.sum(labels_db==-1)}")

pca = PCA(n_components=50, random_state=42)
embeddings_reduced = pca.fit_transform(embeddings)

manual_groups = {
    0: [0,3,5],
    1: [1,2],
    2: [4,6,7],
}

new_labels = -1 * np.ones_like(labels_db)
for new_label, old_clusters in manual_groups.items():
    for old in old_clusters:
        new_labels[np.where(labels_db == old)] = new_label

vectorizer = TfidfVectorizer(stop_words="french", max_features=50)
df_clusters = {}
for cluster_id in np.unique(new_labels):
    if cluster_id == -1:
        continue
    cluster_chunks = [chunks[i] for i, lab in enumerate(new_labels) if lab == cluster_id]
    tfidf_matrix = vectorizer.fit_transform(cluster_chunks)
    scores = np.array(tfidf_matrix.mean(axis=0)).flatten()
    words = vectorizer.get_feature_names_out()
    top_words = [words[i] for i in scores.argsort()[::-1][:10]]
    df_clusters[cluster_id] = top_words

for cluster_id, top_words in df_clusters.items():
    print(f"Cluster {cluster_id}: {', '.join(top_words)}")
tsne = TSNE(n_components=2, random_state=42, init="random")
X_tsne = tsne.fit_transform(embeddings_reduced)

plt.figure(figsize=(12,8))
scatter = plt.scatter(X_tsne[:,0], X_tsne[:,1], c=new_labels, cmap="tab20", s=20)
plt.title("Clusters regroupés manuellement")
plt.colorbar(scatter, label="Nouveaux clusters")
plt.show()
