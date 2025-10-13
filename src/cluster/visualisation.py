import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import pickle

base_dir = Path(__file__).parent
embeddings_path = base_dir.parent / "data" / "processed" / "clustering" / "topic" / "topics_embeddings.npy"
chunks_path = base_dir.parent / "data" / "processed" / "clustering" / "topic" / "topics_chunks.npy"
dbscan_results_file = base_dir.parent / "data" / "processed" / "clustering" / "topic" / "optimize_dbscan" / "topics_dbscan_results.pkl"

target_eps = [0.2, 0.3, 0.4]
target_min_samples = [3, 5, 10]
target_metrics = ["cosine"]


print("Chargement des embeddings et des chunks...")
embeddings = np.load(embeddings_path)
chunks = np.load(chunks_path, allow_pickle=True).tolist()
print(f" {len(embeddings)} embeddings et {len(chunks)} chunks chargés")

if len(embeddings) != len(chunks):
    raise ValueError(" Nombre de chunks et embeddings différents !")


print(f" Chargement des résultats DBSCAN : {dbscan_results_file}")
with open(dbscan_results_file, "rb") as f:
    db_results = pickle.load(f)


for key, res in db_results.items():
    params = res["params"]
    eps = params["eps"]
    min_samples = params["min_samples"]
    metric = params["metric"]

    if eps not in target_eps or min_samples not in target_min_samples or metric not in target_metrics:
        continue

    labels = np.array(res["labels"])
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_outliers = np.sum(labels == -1)

    print(f"\n {key} → {n_clusters} clusters, {n_outliers} outliers")

    df = pd.DataFrame({
        "chunk": chunks,
        "cluster": labels
    })
    df_valid = df[df["cluster"] != -1]

    topics = {}

    french_stopwords = [
    "alors", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon",
    "car", "ce", "cela", "ces", "ceux", "chaque", "ci", "comme", "comment", "dans",
    "des", "du", "dedans", "dehors", "depuis", "devrait", "doit", "donc", "dos",
    "droite", "début", "elle", "elles", "en", "encore", "essai", "est", "et", "eu",
    "fait", "faites", "fois", "font", "hors", "ici", "il", "ils", "je", "juste",
    "la", "le", "les", "leur", "là", "ma", "maintenant", "mais", "mes", "mine",
    "moins", "mon", "mot", "même", "ni", "nommés", "notre", "nous", "nouveaux",
    "ou", "où", "par", "parce", "parole", "pas", "personnes", "peut", "peu",
    "pièce", "plupart", "pour", "pourquoi", "quand", "que", "quel", "quelle",
    "quelles", "quels", "qui", "sa", "sans", "ses", "seulement", "si", "sien",
    "son", "sont", "sous", "soyez", "sujet", "sur", "ta", "tandis", "tellement",
    "tels", "tes", "ton", "tous", "tout", "trop", "très", "tu", "valeur", "voie",
    "voient", "vont", "votre", "vous", "vu", "ça", "étaient", "état", "étions",
    "été", "être"
]
    vectorizer = TfidfVectorizer(stop_words=french_stopwords, max_features=50)

    for cluster_id in df_valid["cluster"].unique():
        cluster_texts = df_valid[df_valid["cluster"] == cluster_id]["chunk"].tolist()
        if not cluster_texts:
            continue
        tfidf_matrix = vectorizer.fit_transform(cluster_texts)
        scores = np.array(tfidf_matrix.mean(axis=0)).flatten()
        words = vectorizer.get_feature_names_out()
        top_words = [words[i] for i in scores.argsort()[::-1][:10]]
        topics[cluster_id] = top_words

    print(f" Topics pour {key}:")
    for cluster_id, top_words in topics.items():
        print(f"Cluster {cluster_id}: {', '.join(top_words)}")

    print("Calcul t-SNE pour visualisation...")
    tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
    emb_2d = tsne.fit_transform(embeddings)

    plt.figure(figsize=(12, 8))
    valid_labels = np.unique(labels[labels != -1])
    colors = plt.cm.get_cmap("tab20", len(valid_labels))

    for i, label in enumerate(valid_labels):
        mask = labels == label
        plt.scatter(emb_2d[mask, 0], emb_2d[mask, 1],
                    s=20,
                    color=colors(i),
                    label=f"Cluster {label}",
                    alpha=0.7)

    plt.title(f"t-SNE visualization of DBSCAN clusters ({key})", fontsize=16)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xlabel("t-SNE 1")
    plt.ylabel("t-SNE 2")
    plt.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    plt.show()
