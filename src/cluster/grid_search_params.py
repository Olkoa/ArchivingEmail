import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from clustering_reworking import merge_clusters

import os
from dotenv import load_dotenv
load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

# --- Chemins ---
base_dir = Path(__file__).parent.parent
output_folder = base_dir / f"data/Projects/{ACTIVE_PROJECT}/semantic_search/topic/optimize_dbscan"
embeddings_path = output_folder.parent / "topics_embeddings.npy"
chunks_path = output_folder.parent / "topics_chunks.npy"
dbscan_results_file = output_folder / "topics_dbscan_results.pkl"
results_file = base_dir / "grid_search_results.csv"

embeddings = np.load(embeddings_path)
chunks = np.load(chunks_path, allow_pickle=True).tolist()
with open(dbscan_results_file, "rb") as f:
    results = pickle.load(f)

df_results = pd.read_csv(results_file)
print(f"[INFO] {len(df_results)} combinaisons chargées depuis le CSV.")

idx = 4
comb = df_results.iloc[idx]
alpha = comb["alpha"]
beta = comb["beta"]
gamma = comb["gamma"]
min_score = comb["min_score"]
print(f"[INFO] Paramètres de la 5ème combinaison : alpha={alpha}, beta={beta}, gamma={gamma}, min_score={min_score}")

# --- Chargement labels DBSCAN ---
key_target = "eps=0.20_min=10_metric=cosine"
labels_db = np.array(results[key_target]["labels"])

# --- PCA pour réduire embeddings avant merge_clusters ---
print("[INFO] Calcul PCA...")
pca = PCA(n_components=50, random_state=42)
embeddings_reduced = pca.fit_transform(embeddings)
print("[INFO] PCA terminée.")

# --- Stopwords ---
stopwords = [
    "alors","au","aucuns","aussi","autre","avant","avec","avoir","bon","car","ce","cela","ces","ceux","chaque",
    "ci","comme","comment","dans","des","du","dedans","dehors","depuis","devrait","doit","donc","dos","droite",
    "début","elle","elles","en","encore","essai","est","et","eu","fait","faites","fois","font","hors","ici",
    "il","ils","je","juste","la","le","les","leur","là","ma","maintenant","mais","mes","mine","moins","mon",
    "mot","même","ni","nommés","notre","nous","nouveaux","ou","où","par","parce","parole","pas","personnes",
    "peut","peu","pièce","plupart","pour","pourquoi","quand","que","quel","quelle","quelles","quels","qui",
    "sa","sans","ses","seulement","si","sien","son","sont","sous","soyez","sujet","sur","ta","tandis",
    "tellement","tels","tes","ton","tous","tout","trop","très","tu","valeur","voie","voient","vont","votre",
    "vous","vu","ça","étaient","état","étions","été","être", "laure", "raphaëlle", "clerc", "charly", "guyon",
    "bernard", "myriam","pascal", "elisabeth", "frederic", "voilà"
]

print("[INFO] Application de merge_clusters avec la 5ème combinaison...")
labels_super, cluster_keywords, cluster_scores, _ = merge_clusters(
    embeddings_reduced, chunks, labels_db, stopwords,
    target_clusters=10, alpha=alpha, beta=beta, gamma=gamma, min_score=min_score
)

mask_not_out = labels_super != -1
labels_filtered = labels_super[mask_not_out]
emb_filtered = embeddings_reduced[mask_not_out]
chunks_filtered = [chunks[i] for i, m in enumerate(mask_not_out) if m]

n_clusters = len(np.unique(labels_filtered))
print(f"[INFO] Nombre de clusters valides : {n_clusters}")
if n_clusters > 1:
    sil = silhouette_score(emb_filtered, labels_filtered)
    db = davies_bouldin_score(emb_filtered, labels_filtered)
    ch = calinski_harabasz_score(emb_filtered, labels_filtered)
    print(f"[INFO] Scores : silhouette={sil:.3f}, DB={db:.3f}, CH={ch:.3f}")

print("[INFO] Calcul TSNE...")
emb_2d = TSNE(n_components=2, random_state=42).fit_transform(emb_filtered)
print("[INFO] TSNE terminé.")

np.save("labels_5eme_comb.npy", labels_filtered)
np.save("emb_2d_5eme_comb.npy", emb_2d)
with open("chunks_5eme_comb.pkl", "wb") as f:
    pickle.dump(chunks_filtered, f)

print("[INFO] Labels, embeddings 2D et chunks sauvegardés pour la 5ème combinaison !")
