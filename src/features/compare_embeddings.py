import numpy as np
import json
import pickle
from pathlib import Path
from sklearn.cluster import KMeans
from tqdm import tqdm
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import hdbscan
import warnings

warnings.filterwarnings("ignore")

base_dir = Path(__file__).parent
output_folder = base_dir.parent / "data" / "processed" / "celine_guyon" / "Boîte de réception" 

models_name = [
    "multi-qa-MiniLM-L6-cos-v1",          
    "all-MiniLM-L6-v2",                   
    "all-mpnet-base-v2",                  
    "paraphrase-MiniLM-L12-v2",           
    "multi-qa-mpnet-base-dot-v1",         
    "sentence-t5-base",                   
    "distiluse-base-multilingual-cased-v2", 
    "paraphrase-multilingual-MiniLM-L12-v2" 
]

def minmax(x):
    arr = np.array(x, dtype=float)
    if arr.max() == arr.min():
        return np.zeros_like(arr)
    return (arr - arr.min()) / (arr.max() - arr.min())

def find_best_k_and_labels(embeddings, k_values=range(2, 200), verbose=False):
    evaluation_results = {}
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        silhouette = silhouette_score(embeddings, labels)
        davies = davies_bouldin_score(embeddings, labels)
        calinski = calinski_harabasz_score(embeddings, labels)
        evaluation_results[k] = {"silhouette": silhouette, "davies_bouldin": davies, "calinski_harabasz": calinski}
        if verbose:
            print(f"k={k} | Silhouette={silhouette:.4f} | Davies-Bouldin={davies:.4f} | Calinski-Harabasz={calinski:.2f}")

    sils = np.array([evaluation_results[k]["silhouette"] for k in k_values])
    davs = np.array([evaluation_results[k]["davies_bouldin"] for k in k_values])
    cals = np.array([evaluation_results[k]["calinski_harabasz"] for k in k_values])
    sils_n = minmax(sils)
    davs_n_inv = 1 - minmax(davs)
    cals_n = minmax(cals)
    combined = (sils_n + davs_n_inv + cals_n) / 3
    best_k = list(k_values)[int(np.argmax(combined))]

    kmeans = KMeans(n_clusters=best_k, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    final_scores = {
        "silhouette": silhouette_score(embeddings, labels),
        "davies_bouldin": davies_bouldin_score(embeddings, labels),
        "calinski_harabasz": calinski_harabasz_score(embeddings, labels)
    }
    return best_k, labels, final_scores

def cluster_with_hdbscan(embeddings, min_cluster_size=5, min_samples=None):
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples, metric='euclidean')
    labels = clusterer.fit_predict(embeddings)
    mask = labels != -1
    valid_labels = labels[mask]
    valid_embeddings = embeddings[mask]
    if len(np.unique(valid_labels)) > 1:
        silhouette = silhouette_score(valid_embeddings, valid_labels)
        davies = davies_bouldin_score(valid_embeddings, valid_labels)
        calinski = calinski_harabasz_score(valid_embeddings, valid_labels)
    else:
        silhouette = davies = calinski = np.nan
    return labels, {"silhouette": silhouette, "davies_bouldin": davies, "calinski_harabasz": calinski}

#  Dossier pour sauvegarder
clustering_folder = base_dir.parent / "data" / "processed" / "clustering"
clustering_folder.mkdir(parents=True, exist_ok=True)

# Dictionnaires pour chaque score et labels
kmeans_labels = {}
kmeans_silhouette = {}
kmeans_davies = {}
kmeans_calinski = {}

hdbscan_labels = {}
hdbscan_silhouette = {}
hdbscan_davies = {}
hdbscan_calinski = {}


for model_name in tqdm(models_name, desc="Clustering models"):
    prefix = f"email_chunks_{model_name}"
    embeddings_path = output_folder / f"{prefix}_embeddings.npy"
    embeddings = np.load(embeddings_path)

    # KMeans
    best_k, labels_k, scores_k = find_best_k_and_labels(embeddings)
    kmeans_labels[model_name] = labels_k
    kmeans_silhouette[model_name] = scores_k["silhouette"]
    kmeans_davies[model_name] = scores_k["davies_bouldin"]
    kmeans_calinski[model_name] = scores_k["calinski_harabasz"]

    # HDBSCAN
    labels_h, scores_h = cluster_with_hdbscan(embeddings)
    hdbscan_labels[model_name] = labels_h
    hdbscan_silhouette[model_name] = scores_h["silhouette"]
    hdbscan_davies[model_name] = scores_h["davies_bouldin"]
    hdbscan_calinski[model_name] = scores_h["calinski_harabasz"]

# Sauvegarde 
pickle.dump(kmeans_labels, open(clustering_folder / "kmeans"/ "kmeans_labels.pkl", "wb"))
pickle.dump(kmeans_silhouette, open(clustering_folder / "kmeans"/ "silhouette_score.pkl", "wb"))
pickle.dump(kmeans_davies, open(clustering_folder /"kmeans"/ "davies.pkl", "wb"))
pickle.dump(kmeans_calinski, open(clustering_folder /"kmeans"/ "calinski.pkl", "wb"))

pickle.dump(hdbscan_labels, open(clustering_folder / "hdbscan"/ "labels.pkl", "wb"))
pickle.dump(hdbscan_silhouette, open(clustering_folder /"hdbscan"/ "silhouette_score.pkl", "wb"))
pickle.dump(hdbscan_davies, open(clustering_folder /"hdbscan"/ "davies.pkl", "wb"))
pickle.dump(hdbscan_calinski, open(clustering_folder /"hdbscan"/ "calinski.pkl", "wb"))
