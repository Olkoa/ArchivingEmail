import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize



base_dir = Path(__file__).parent
embeddings_path = base_dir.parent / "data" / "processed" / "clustering" / "topic" / "topics_embeddings.npy"

min_samples_values = [5, 10, 20, 50]   
n_components = 50                      


print("Chargement des embeddings ...")
embeddings = np.load(embeddings_path)
print(f"Shape embeddings: {embeddings.shape}")


embeddings_norm = normalize(embeddings)


print(f"Réduction PCA à {n_components} composantes ...")
pca = PCA(n_components=n_components, random_state=42)
embeddings_reduced = pca.fit_transform(embeddings_norm)
print(f"Shape après PCA: {embeddings_reduced.shape}")


plt.figure(figsize=(10, 6))

for min_samples in min_samples_values:
    neigh = NearestNeighbors(n_neighbors=min_samples, metric="euclidean")  
    nbrs = neigh.fit(embeddings_reduced)
    distances, indices = nbrs.kneighbors(embeddings_reduced)
    k_dist = np.sort(distances[:, -1])

    mean_val = np.mean(k_dist)
    median_val = np.median(k_dist)
    p90 = np.percentile(k_dist, 90)
    p95 = np.percentile(k_dist, 95)
    p99 = np.percentile(k_dist, 99)

    print(f"\n===== min_samples = {min_samples} =====")
    print(f"Moyenne   : {mean_val:.4f}")
    print(f"Médiane   : {median_val:.4f}")
    print(f"90e perc. : {p90:.4f}")
    print(f"95e perc. : {p95:.4f}")
    print(f"99e perc. : {p99:.4f}")

    plt.plot(k_dist, label=f"min_samples={min_samples}")

plt.xlabel("Points triés")
plt.ylabel("Distance au k-ième voisin")
plt.title("K-distance plot pour différents min_samples")
plt.legend()
plt.grid(True)
plt.show()
