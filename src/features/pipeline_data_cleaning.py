from pathlib import Path
import mailparser
import json
from tqdm import tqdm
from clean_data import extract_clean_text
import pandas as pd
import numpy as np
from utils_pipeline import *
import sys
import pickle

# Ajouter src/ au sys.path
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from cluster.embedding_chunk import chunk_text, embed_mails
from topic.config import CHUNKS_PATH, EMBEDDINGS_PATH, VIS_CHUNKS, VIS_LABELS, VIS_EMB_2D, STOPWORDS

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN, KMeans
from collections import Counter

# --------------------------
# Étape 1 : Nettoyage des mails
# --------------------------
def automate_cleaning(input_folder, output_file, force=True, limit_mails=None):
    output_path = Path(output_file).expanduser().resolve()
    input_path = Path(input_folder).expanduser().resolve()

    if output_path.exists() and output_path.stat().st_size > 0 and not force:
        try:
            data = json.load(open(output_path, "r", encoding="utf-8"))
            if isinstance(data, list) and len(data) > 0:
                print(f"[SKIP] JSON déjà présent et valide : {output_path}")
                return output_path
        except json.JSONDecodeError:
            print(f"[WARN] JSON corrompu, recalcul forcé : {output_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Dossier non trouvé : {input_path}")

    eml_files = sorted(input_path.rglob("*.eml"))
    if limit_mails:
        eml_files = eml_files[:limit_mails]
        print(f"[TEST MODE] Seuls les {len(eml_files)} premiers mails seront traités.")

    all_mails = []
    errors = 0
    print(f"[INFO] Parsing de {len(eml_files)} mails...")
    for eml_file in tqdm(eml_files, desc="Parsing mails"):
        try:
            mail = mailparser.parse_from_file(str(eml_file))
            body = mail.body or ""
            cleaned_text = extract_clean_text(body)
            if not cleaned_text:
                continue
            mail_data = {
                "file": eml_file.name,
                "folder": str(eml_file.parent.relative_to(input_path)),
                "from": mail.from_,
                "to": mail.to,
                "subject": mail.subject or "",
                "date": mail.date.isoformat() if mail.date else None,
                "body": cleaned_text,
            }
            all_mails.append(mail_data)
        except Exception as e:
            errors += 1
            print(f"[ERREUR] {eml_file}: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_mails, f, ensure_ascii=False, indent=4)

    print(f"[INFO] Total mails nettoyés : {len(all_mails)}, erreurs : {errors}")
    print(f"[INFO] JSON sauvegardé : {output_path}")
    return output_path
# --------------------------
# Étape 2 : Création des chunks
# --------------------------
def chunk_mails(json_path, output_dir, chunk_size=200, overlap=20, force=True):
    output_dir = Path(output_dir).resolve()
    csv_path = output_dir / "chunked_emails.csv"

    if csv_path.exists() and csv_path.stat().st_size > 0 and not force:
        df = pd.read_csv(csv_path)
        if not df.empty:
            print(f"[SKIP] Chunks déjà présents : {csv_path}")
            return df

    with open(json_path, "r", encoding="utf-8") as f:
        mails = json.load(f)

    rows = []
    for mail in tqdm(mails, desc="Chunking mails"):
        body = mail.get("body", "")
        if not body.strip():
            continue
        chunks = chunk_text(body, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            rows.append({
                "subject": mail.get("subject", ""),
                "chunk": chunk,
                "chunk_id": i,
                "sender": ";".join([addr[1] for addr in mail.get("from", [])]) if isinstance(mail.get("from"), list) else str(mail.get("from")),
                "recipient": ";".join([addr[1] for addr in mail.get("to", [])]) if isinstance(mail.get("to"), list) else str(mail.get("to")),
                "date": mail.get("date"),
                "file": mail.get("file"),
                "folder": mail.get("folder"),
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    df_chunks = pd.DataFrame(rows)
    df_chunks.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[INFO] Chunks créés et sauvegardés : {csv_path} ({len(df_chunks)} chunks)")
    return df_chunks

# --------------------------
# Étape 3 : Calcul des embeddings + clustering
# --------------------------
def compute_embeddings(chunk_csv_path, embeddings_dir, force=True):
    embeddings_dir = Path(embeddings_dir).resolve()
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    df_chunks = pd.read_csv(chunk_csv_path)
    if "body" not in df_chunks.columns and "chunk" in df_chunks.columns:
        df_chunks = df_chunks.rename(columns={"chunk": "body"})
    print(f"[INFO] Calcul des embeddings pour {len(df_chunks)} chunks...")

    temp_csv_path = embeddings_dir / "temp_chunks.csv"
    df_chunks.to_csv(temp_csv_path, index=False)

    all_chunks, embeddings = embed_mails(
        input_file=temp_csv_path,
        output_folder=embeddings_dir,
        save_name="topics"
    )

    # Sauvegarde embeddings bruts
    np.save(EMBEDDINGS_PATH, embeddings)
    np.save(CHUNKS_PATH, np.array(all_chunks, dtype=object))

    # --------------------------
    # Clustering DBSCAN pour filtrer les outliers (-1)
    # --------------------------
    print("[INFO] Clustering DBSCAN...")
    dbscan = DBSCAN(eps=0.2, min_samples=10, metric="cosine")
    labels = dbscan.fit_predict(embeddings)

    mask_valid = labels != -1
    embeddings_valid = embeddings[mask_valid]
    chunks_valid = [all_chunks[i] for i, m in enumerate(mask_valid) if m]
    labels_valid = labels[mask_valid]

    # --------------------------
    # KMeans sur cluster 0
    # --------------------------
    print("[INFO] Application KMeans (k=10) sur le cluster 0...")
    k = 10
    idx_cluster0 = np.where(labels_valid == 0)[0]

    labels_final = labels_valid.copy()
    if len(idx_cluster0) > 0:
        emb_cluster0 = embeddings_valid[idx_cluster0]

        # Fit KMeans sur les embeddings du cluster 0
        kmeans = KMeans(n_clusters=k, random_state=42)
        sub_labels = kmeans.fit_predict(emb_cluster0)

        # Remplacer complètement les labels du cluster 0 par les sous-labels KMeans
        for i, idx in enumerate(idx_cluster0):
            labels_final[idx] = sub_labels[i]

    # --------------------------
    # Remapper les labels pour avoir des indices consécutifs
    # --------------------------
    unique_labels = np.unique(labels_final)
    label_map = {old: new for new, old in enumerate(unique_labels)}
    labels_final_mapped = np.array([label_map[l] for l in labels_final])

    # --------------------------
    # Réduction dimensionnelle pour visualisation
    # --------------------------
    print("[INFO] Réduction dimensionnelle PCA + TSNE...")
    pca = PCA(n_components=min(50, embeddings_valid.shape[1]), random_state=42)
    embeddings_reduced = pca.fit_transform(embeddings_valid)
    emb_2d = TSNE(n_components=2, random_state=42).fit_transform(embeddings_reduced)

    # Sauvegarde
    np.save(VIS_EMB_2D, emb_2d)
    np.save(VIS_LABELS, labels_final_mapped)
    with open(VIS_CHUNKS, "wb") as f:
        pickle.dump(chunks_valid, f)

    print(f"[INFO] Embeddings 2D et labels finaux sauvegardés !")
    return all_chunks, embeddings

# --------------------------
# Pipeline complète
# --------------------------
def automate_full_process(input_folder, json_file, chunk_output_dir, compute_embeds=True, force=True, limit_mails=None):
    print("\n--- Étape 1 : Nettoyage des mails ---")
    json_path = automate_cleaning(input_folder, json_file, force=force, limit_mails=limit_mails)

    print("\n--- Étape 2 : Création des chunks ---")
    df_chunks = chunk_mails(json_path, chunk_output_dir, force=force)

    all_chunks, embeddings = None, None
    if compute_embeds:
        print("\n--- Étape 3 : Calcul des embeddings et clustering ---")
        csv_chunks_path = Path(chunk_output_dir) / "chunked_emails.csv"
        all_chunks, embeddings = compute_embeddings(csv_chunks_path, chunk_output_dir, force=force)

    print("\n✅ Pipeline complète terminée !")
    return df_chunks, all_chunks, embeddings

# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    input_folder = base_dir / "data" / "mail_export" / "celine_guyon"
    json_file = base_dir.parent / "data" / "processed" / "celine_guyon" / "all_cleaned_mails.json"
    chunk_output_dir = base_dir.parent / "data" / "processed" / "clustering" / "topic"

    subset_mails = None # <- Ne traiter que 500 mails pour test
    print("\n=== Lancement de la pipeline complète (subset test) ===")
    df_chunks, all_chunks, embeddings = automate_full_process(
        input_folder=input_folder,
        json_file=json_file,
        chunk_output_dir=chunk_output_dir,
        compute_embeds=True,
        force=True,
        limit_mails=subset_mails
    )

    print(f"\n[INFO] Total chunks créés : {len(df_chunks)}")
    if all_chunks is not None:
        print(f"[INFO] Total chunks pour embeddings : {len(all_chunks)}")
        print(f"[INFO] Embeddings shape : {embeddings.shape}")