import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from collections import Counter

from clustering_reworking import merge_clusters

# --- Chemins ---
base_dir = Path(__file__).parent
output_folder = base_dir.parent / "data/processed/clustering/topic/optimize_dbscan"
embeddings_path = output_folder.parent / "topics_embeddings.npy"
chunks_path = output_folder.parent / "topics_chunks.npy"
dbscan_results_file = output_folder / "topics_dbscan_results.pkl"
results_file = base_dir / "grid_search_results.csv"

# --- Chargement embeddings / chunks / CSV ---
embeddings = np.load(embeddings_path)
chunks = np.load(chunks_path, allow_pickle=True).tolist()
with open(dbscan_results_file, "rb") as f:
    results = pickle.load(f)

df_results = pd.read_csv(results_file)
print(f"[INFO] {len(df_results)} combinaisons chargées depuis le CSV.")

# --- Sélection de la 5ème combinaison ---
idx = 4
comb = df_results.iloc[idx]
alpha, beta, gamma, min_score = comb["alpha"], comb["beta"], comb["gamma"], comb["min_score"]
print(f"[INFO] Paramètres 5ème combinaison : alpha={alpha}, beta={beta}, gamma={gamma}, min_score={min_score}")

# --- Chargement labels DBSCAN ---
key_target = "eps=0.20_min=10_metric=cosine"
labels_db = np.array(results[key_target]["labels"])

# --- Filtrer outliers dès le départ ---
mask_valid = labels_db != -1
embeddings_valid = embeddings[mask_valid]
labels_valid = labels_db[mask_valid]
chunks_valid = [chunks[i] for i, m in enumerate(mask_valid) if m]
print(f"[INFO] {len(labels_valid)} embeddings après suppression des -1.")

# --- PCA pour réduire embeddings avant merge_clusters ---
print("[INFO] Calcul PCA...")
pca = PCA(n_components=50, random_state=42)
embeddings_reduced = pca.fit_transform(embeddings_valid)
print("[INFO] PCA terminée.")

# --- Stopwords ---
stopwords = ["alors","au","aucuns","aussi","autre","avant","avec","avoir","bon","car","ce","cela","ces","ceux",
"chaque","ci","comme","comment","dans","des","du","dedans","dehors","depuis","devrait","doit","donc","dos",
"droite","début","elle","elles","en","encore","essai","est","et","eu","fait","faites","fois","font","hors",
"ici","il","ils","je","juste","la","le","les","leur","là","ma","maintenant","mais","mes","mine","moins",
"mon","mot","même","ni","nommés","notre","nous","nouveaux","ou","où","par","parce","parole","pas",
"personnes","peut","peu","pièce","plupart","pour","pourquoi","quand","que","quel","quelle","quelles",
"quels","qui","sa","sans","ses","seulement","si","sien","son","sont","sous","soyez","sujet","sur","ta",
"tandis","tellement","tels","tes","ton","tous","tout","trop","très","tu","valeur","voie","voient",
"vont","votre","vous","vu","ça","étaient","état","étions","été","être"]

print("[INFO] Application merge_clusters...")
labels_merged, cluster_keywords, cluster_scores, _ = merge_clusters(
    embeddings_reduced, chunks_valid, labels_valid, stopwords,
    target_clusters=10, alpha=alpha, beta=beta, gamma=gamma, min_score=min_score
)

label_counts = Counter(labels_merged)
most_common_label = label_counts.most_common(1)[0][0]
pct_common = (label_counts[most_common_label] / len(labels_merged)) * 100
print(f"[INFO] Cluster omniprésent : {most_common_label} ({pct_common:.1f}% des données)")

mask_common = labels_merged == most_common_label
emb_common = embeddings_reduced[mask_common]
chunks_common = [chunks_valid[i] for i, m in enumerate(mask_common) if m]

k = 10  
print(f"[INFO] Application KMeans(k={k}) sur le cluster omniprésent...")
kmeans = KMeans(n_clusters=k, random_state=42)
sub_labels = kmeans.fit_predict(emb_common)

labels_final = labels_merged.copy()
offset = labels_final.max() + 1
for i, idx_mask in enumerate(np.where(mask_common)[0]):
    labels_final[idx_mask] = offset + sub_labels[i]

unique_labels = np.unique(labels_final)
label_map = {old: new for new, old in enumerate(unique_labels)}
labels_final_mapped = np.array([label_map[l] for l in labels_final])


print("[INFO] Calcul TSNE 2D...")
emb_2d = TSNE(n_components=2, random_state=42).fit_transform(embeddings_reduced)
print("[INFO] TSNE terminé.")

# --- Sauvegarde ---
np.save("labels.npy", labels_final_mapped)
np.save("emb_2d.npy", emb_2d)
with open("chunks.pkl", "wb") as f:
    pickle.dump(chunks_valid, f)

print("[INFO] Labels finaux, embeddings 2D et chunks sauvegardés !")
