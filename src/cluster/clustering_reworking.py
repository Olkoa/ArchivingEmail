import numpy as np
import pickle
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import plotly.express as px
import pandas as pd
from tqdm import tqdm
from collections import Counter
import numpy as np
import pickle
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import plotly.express as px
import pandas as pd
from tqdm import tqdm
from collections import Counter, defaultdict
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

import os
from dotenv import load_dotenv
load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

# --- Chemins ---
base_dir = Path(__file__).parent.parent
# output_folder = base_dir.parent / "data" / "Projects" / ACTIVE_PROJECT / "clustering" / "topic" / "optimize_dbscan"
output_folder = base_dir.parent / "data" / "Projects" / ACTIVE_PROJECT / "semantic_search"/ "topic" / "optimize_dbscan"
embeddings_path = output_folder.parent / "topics_embeddings.npy"
chunks_path = output_folder.parent / "topics_chunks.npy"
dbscan_results_file = output_folder / "topics_dbscan_results.pkl"

# --- Chargement ---
print("[INFO] Chargement des données...", embeddings_path)
embeddings = np.load(embeddings_path)
chunks = np.load(chunks_path, allow_pickle=True).tolist()
with open(dbscan_results_file, "rb") as f:
    results = pickle.load(f)

key_target = "eps=0.20_min=10_metric=cosine"
labels_db = np.array(results[key_target]["labels"])
unique_labels = np.unique(labels_db[labels_db != -1])
print(f"[INFO] Clusters DBSCAN valides : {len(unique_labels)}")

# --- PCA ---
print("[INFO] Calcul PCA...")
pca = PCA(n_components=50, random_state=42)
embeddings_reduced = pca.fit_transform(embeddings)
print("[INFO] PCA terminée.")

# --- Stopwords ---
stopwords = ["alors","au","aucuns","aussi","autre","avant","avec","avoir","bon",
    "car","ce","cela","ces","ceux","chaque","ci","comme","comment","dans",
    "des","du","dedans","dehors","depuis","devrait","doit","donc","dos",
    "droite","début","elle","elles","en","encore","essai","est","et","eu",
    "fait","faites","fois","font","hors","ici","il","ils","je","juste",
    "la","le","les","leur","là","ma","maintenant","mais","mes","mine",
    "moins","mon","mot","même","ni","nommés","notre","nous","nouveaux",
    "ou","où","par","parce","parole","pas","personnes","peut","peu",
    "pièce","plupart","pour","pourquoi","quand","que","quel","quelle",
    "quelles","quels","qui","sa","sans","ses","seulement","si","sien",
    "son","sont","sous","soyez","sujet","sur","ta","tandis","tellement",
    "tels","tes","ton","tous","tout","trop","très","tu","valeur","voie",
    "voient","vont","votre","vous","vu","ça","étaient","état","étions",
    "été","être", "laure", "raphaëlle", "clerc", "charly", "guyon",
    "bernard", "myriam","pascal", "elisabeth", "frederic", "voilà",
]

# --- Fonction mots-clés ---
def compute_cluster_keywords(chunks, labels, stopwords, top_k=15, min_docs=10, max_features=5000):
    cluster_keywords = {}
    cluster_counts = {}
    vectorizer = TfidfVectorizer(
        stop_words=stopwords,
        max_features=max_features,
        min_df=2,    # mot doit apparaître au moins dans 2 documents
        max_df=0.6   # ignore les mots présents dans plus de 60% des documents
    )
    for cid in np.unique(labels):
        if cid == -1:
            continue
        cluster_chunks = [chunks[i] for i, lab in enumerate(labels) if lab == cid]
        if len(cluster_chunks) < min_docs:
            continue
        try:
            tfidf_matrix = vectorizer.fit_transform(cluster_chunks)
            if tfidf_matrix.shape[1] == 0:
                continue
            scores = np.array(tfidf_matrix.mean(axis=0)).flatten()
            words = vectorizer.get_feature_names_out()
            top_words = [words[i] for i in scores.argsort()[::-1][:top_k]]
            cluster_keywords[cid] = set(top_words)
            cluster_counts[cid] = Counter(" ".join(cluster_chunks).split())
        except ValueError:
            continue
    return cluster_keywords, cluster_counts


def merge_clusters(embeddings, chunks, labels, stopwords, target_clusters=10, min_score=1.0, alpha=1.5, beta=5, gamma=0.05):
    print("[INFO] Démarrage fusion hiérarchique des clusters...")

    # Sécurités pour éviter IndexError
    if len(embeddings) != len(chunks):
        raise ValueError(f"Embeddings ({len(embeddings)}) et chunks ({len(chunks)}) doivent avoir la même longueur")
    if len(labels) != len(chunks):
        raise ValueError(f"Labels ({len(labels)}) et chunks ({len(chunks)}) doivent avoir la même longueur")

    current_labels = labels.copy()
    iteration = 0
    pbar = tqdm(total=10000, desc="Fusion clusters", unit="fusion")

    # Initialisation clusters valides
    valid_indices = np.arange(len(chunks))
    unique_cids = np.unique(current_labels[current_labels != -1])
    cluster_texts = {cid: [chunks[i] for i in valid_indices if current_labels[i] == cid] for cid in unique_cids}
    cluster_keywords, cluster_counts = compute_cluster_keywords(chunks, labels, stopwords)

    while True:
        unique_cids = np.unique(current_labels[current_labels != -1])
        if len(unique_cids) <= target_clusters:
            break

        # Centroids sécurisés
        centroids = []
        valid_cids = []
        for cid in unique_cids:
            idxs = np.where(current_labels == cid)[0]
            if len(idxs) == 0:
                continue
            centroids.append(embeddings[idxs].mean(axis=0))
            valid_cids.append(cid)

        if len(centroids) == 0:
            break
        centroids = np.vstack(centroids)
        sim_matrix = cosine_similarity(centroids)

        best_score = -1
        best_pair = None

        for i, cid1 in enumerate(valid_cids):
            for j, cid2 in enumerate(valid_cids):
                if cid1 >= cid2:
                    continue
                words1, words2 = cluster_keywords.get(cid1, set()), cluster_keywords.get(cid2, set())
                jaccard = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
                common_words = words1 & words2
                bonus = sum(min(cluster_counts[cid1].get(w, 0), cluster_counts[cid2].get(w, 0)) for w in common_words)
                score = alpha*sim_matrix[i, j] + beta*jaccard + gamma*bonus
                if score > best_score:
                    best_score = score
                    best_pair = (cid1, cid2)

        if best_pair is None or best_score < min_score:
            print(f"[INFO] Arrêt de la fusion : meilleur score {best_score:.3f} < seuil {min_score}")
            break

        cid1, cid2 = best_pair
        current_labels[current_labels == cid2] = cid1
        cluster_texts[cid1] += cluster_texts.get(cid2, [])
        for w, c in cluster_counts.get(cid2, {}).items():
            cluster_counts[cid1][w] += c
        cluster_texts.pop(cid2, None)
        cluster_counts.pop(cid2, None)

        # Recalcul mots-clés pour le cluster fusionné
        new_texts = cluster_texts[cid1]
        if len(new_texts) > 0:
            new_keywords, _ = compute_cluster_keywords(new_texts, np.array([0]*len(new_texts)), stopwords)
            cluster_keywords[cid1] = new_keywords[0] if len(new_keywords) > 0 else set()
        else:
            cluster_keywords[cid1] = set()

        iteration += 1
        pbar.set_description(f"Iteration {iteration}, clusters: {len(unique_cids)}, fusion {cid1}<-{cid2}, score={best_score:.3f}")
        pbar.update(1)

    pbar.close()
    print("[INFO] Fusion terminée.")

    # Calcul score final des clusters
    cluster_scores = {}
    for cid in np.unique(current_labels[current_labels != -1]):
        idx = np.where(current_labels == cid)[0]
        if len(idx) == 0:
            continue
        centroid = embeddings[idx].mean(axis=0)
        sim = cosine_similarity([centroid], embeddings[idx]).mean()
        cluster_scores[cid] = sim

    return current_labels, cluster_keywords, cluster_scores, cluster_counts

# # --- Calcul super-clusters ---
# print("[INFO] Calcul des super-clusters...")
# labels_super, cluster_keywords_super, cluster_scores, cluster_counts = merge_clusters(
#     embeddings_reduced, chunks, labels_db, stopwords, target_clusters=10
# )
# print(f"[INFO] Nombre de super-clusters: {len(np.unique(labels_super[labels_super!=-1]))}")

# valid_super_clusters = set(cluster_keywords_super.keys())

# # --- Sous-clusters pour le super-cluster 1 ---
# mask_1 = labels_super == 1
# emb_cluster1 = embeddings_reduced[mask_1]
# chunks_cluster1 = [chunks[i] for i, m in enumerate(mask_1) if m]

# if len(emb_cluster1) == 0:
#     print("[WARN] Super-cluster 1 vide, skipping sous-clusters.")
#     sub_labels = np.array([])
#     cluster_keywords_sub = {}
#     valid_sub_clusters = set()
# else:
#     k = 10
#     print(f"[INFO] Cluster 1 contient {len(emb_cluster1)} documents. Application de KMeans(k={k})...")
#     kmeans_sub = KMeans(n_clusters=k, random_state=42)
#     sub_labels = kmeans_sub.fit_predict(emb_cluster1)
#     print("[INFO] Sous-clusters calculés.")

#     cluster_keywords_sub = {}
#     vectorizer_sub = TfidfVectorizer(stop_words=stopwords, max_features=5000)
#     top_k_sub = 15
#     for sub_cid in np.unique(sub_labels):
#         sub_chunks = [chunks_cluster1[i] for i, lab in enumerate(sub_labels) if lab == sub_cid]
#         if len(sub_chunks) < 3:
#             continue
#         tfidf_matrix = vectorizer_sub.fit_transform(sub_chunks)
#         if tfidf_matrix.shape[1] == 0:
#             continue
#         scores = np.array(tfidf_matrix.mean(axis=0)).flatten()
#         words = vectorizer_sub.get_feature_names_out()
#         top_words = [words[i] for i in scores.argsort()[::-1][:top_k_sub]]
#         cluster_keywords_sub[sub_cid] = set(top_words)
#     valid_sub_clusters = set(cluster_keywords_sub.keys())

# # --- Remapper labels super + sous clusters ---
# labels_combined = labels_super.copy()
# for i, idx in enumerate(np.where(mask_1)[0]):
#     if len(sub_labels) == 0:
#         continue
#     labels_combined[idx] = labels_super[idx]*10 + sub_labels[i]

# unique_combined = np.unique(labels_combined[labels_combined!=-1])
# label_mapping = {old: new for new, old in enumerate(unique_combined)}
# labels_mapped = np.array([label_mapping[l] for l in labels_combined if l != -1])

# # --- Filtrer outliers ---
# mask_not_out = labels_combined != -1
# embeddings_filtered = embeddings_reduced[mask_not_out]

# # --- Calcul des métriques de clustering sur embeddings PCA ---
# X = embeddings_filtered  # embeddings PCA filtrés (hors outliers)
# y = labels_mapped        # labels combinés mappés

# if len(np.unique(y)) > 1:
#     sil_score = silhouette_score(X, y)
#     db_score = davies_bouldin_score(X, y)
#     ch_score = calinski_harabasz_score(X, y)
    
#     print("\n=== Métriques de clustering sur embeddings PCA ===")
#     print(f"Silhouette Score: {sil_score:.3f}  ")
#     print(f"Davies-Bouldin Score: {db_score:.3f}  ")
#     print(f"Calinski-Harabasz Score: {ch_score:.3f}")
# else:
#     print("[WARN] Pas assez de clusters pour calculer Silhouette Score.")




# # --- TSNE ---
# print("[INFO] Calcul TSNE pour visualisation...")
# emb_2d = TSNE(n_components=2, random_state=42).fit_transform(embeddings_filtered)
# print("[INFO] TSNE terminé.")

# # --- DataFrame pour plot ---
# df = pd.DataFrame({
#     "x": emb_2d[:,0],
#     "y": emb_2d[:,1],
#     "cluster": labels_mapped
# })

# # --- Hover texte super-clusters ---
# hover_texts = []
# valid_indices = []
# for idx, l in enumerate(labels_combined[mask_not_out]):
#     super_cid = l // 10
#     if super_cid == 1:
#         sub_cid = l % 10
#         if sub_cid not in valid_sub_clusters:
#             continue
#         words = cluster_keywords_sub[sub_cid]
#     else:
#         if super_cid not in valid_super_clusters:
#             continue
#         words = cluster_keywords_super[super_cid]
#     score = cluster_scores.get(super_cid, 0)
#     hover_texts.append(f"Cluster {label_mapping[l]}<br>Score: {score:.2f}<br>Words: {', '.join(words)}")
#     valid_indices.append(idx)

# df = df.iloc[valid_indices].copy()
# df["hover"] = hover_texts

# # --- Plot 10 clusters par graphique ---
# batch_size = 10
# n_batches = int(np.ceil(df["cluster"].nunique() / batch_size))

# for b in range(n_batches):
#     batch_labels = list(range(b*batch_size, min((b+1)*batch_size, df["cluster"].nunique())))
#     df_batch = df[df["cluster"].isin(batch_labels)]
    
#     fig = px.scatter(
#         df_batch, x="x", y="y", color="cluster", hover_name="hover",
#         color_discrete_sequence=px.colors.qualitative.Plotly
#     )
#     fig.update_layout(
#         title=f"TSNE embeddings clusters {b*batch_size} à {min((b+1)*batch_size-1, df['cluster'].nunique()-1)}",
#         width=1000, height=800
#     )
#     fig.show()

# # --- Plot séparé pour les sous-clusters du super-cluster 1 ---
# mask_sub = mask_1[mask_not_out]
# df_sub = df[mask_sub]

# hover_texts_sub = []
# valid_indices_sub = []
# for i, idx in enumerate(np.where(mask_1)[0]):
#     if len(sub_labels) == 0:
#         continue
#     sub_cid = sub_labels[i]
#     if sub_cid not in valid_sub_clusters:
#         continue
#     words = cluster_keywords_sub[sub_cid]
#     hover_texts_sub.append(f"Sous-cluster {sub_cid}<br>Words: {', '.join(words)}")
#     valid_indices_sub.append(i)

# df_sub = df_sub.iloc[valid_indices_sub].copy()
# df_sub["hover"] = hover_texts_sub

# fig_sub = px.scatter(
#     df_sub, x="x", y="y", color="cluster", hover_name="hover",
#     color_discrete_sequence=px.colors.qualitative.Set1
# )
# fig_sub.update_layout(
#     title="TSNE embeddings sous-clusters du super-cluster 1",
#     width=1000, height=800
# )
# fig_sub.show()

# # --- Affichage détaillé des BoW ---
# for final_label in cluster_keywords_super.keys():  
#     words = cluster_keywords_super[final_label]
#     score = cluster_scores.get(final_label, 0)
#     word_counts = cluster_counts.get(final_label, {})
#     sorted_words = sorted([(w, word_counts.get(w, 0)) for w in words], key=lambda x: x[1], reverse=True)
#     print(f"Super-cluster {final_label} - Score: {score:.2f}")
#     for w, c in sorted_words:
#         print(f"{w}: {c}")
#     print("-"*60)
