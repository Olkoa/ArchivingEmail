from pathlib import Path
import mailparser
import json
from tqdm import tqdm
from features.clean_data import extract_clean_text  
from cluster.embedding_chunk import chunk_text, embed_mails
import pandas as pd
import numpy as np
from utils_pipeline import *

# --------------------------
# Nettoyage des mails
# --------------------------
def automate_cleaning(input_folder, output_file):
    output_path = Path(output_file)
    if output_path.exists():
        print(f"[SKIP] JSON déjà présent : {output_path}")
        return output_path

    input_path = Path(input_folder)
    if not input_path.exists():
        raise FileNotFoundError(f"Dossier non trouvé : {input_path}")

    all_mails = []
    errors = 0
    eml_files = sorted(input_path.rglob("*.eml"))

    for eml_file in tqdm(eml_files, desc="Parsing mails"):  # ← Ici on lit les mails bruts et on nettoie le texte
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
            print(f"Erreur pour {eml_file}: {e}")

    # ← Créer le dossier si inexistant
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_mails, f, ensure_ascii=False, indent=4)

    print(f"[INFO] Total mails nettoyés : {len(all_mails)}, erreurs : {errors}")
    print(f"[INFO] JSON sauvegardé : {output_path}")  # ← JSON = mails nettoyés (sera utilisé pour chunks + embeddings)
    return output_path

# --------------------------
# Création des chunks
# --------------------------
def chunk_mails(json_path, output_dir, chunk_size=200, overlap=20):
    output_dir = Path(output_dir)
    csv_path = output_dir / "chunked_emails.csv"
    if csv_path.exists():
        print(f"[SKIP] Chunks déjà présents : {csv_path}")
        return pd.read_csv(csv_path)

    with open(json_path, "r", encoding="utf-8") as f:
        mails = json.load(f)

    rows = []
    for mail in tqdm(mails, desc="Chunking mails"):  # ← Ici on découpe le corps des mails en chunks
        body = mail.get("body", "")
        chunks = chunk_text(body, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            rows.append({
                "subject": mail.get("subject", ""),
                "body": chunk,
                "chunk_id": i,
                "sender": ";".join([addr[1] for addr in mail.get("from", [])]) if isinstance(mail.get("from"), list) else str(mail.get("from")),
                "recipient": ";".join([addr[1] for addr in mail.get("to", [])]) if isinstance(mail.get("to"), list) else str(mail.get("to")),
                "date": mail.get("date"),
                "file": mail.get("file"),
                "folder": mail.get("folder"),
            })

    df_chunks = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    df_chunks.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[INFO] Chunks créés et sauvegardés : {csv_path}")  # ← CSV chunks = base pour embeddings
    return df_chunks

# --------------------------
# Calcul embeddings
# --------------------------
def compute_embeddings(json_path, output_dir, model_name="all-MiniLM-L6-v2"):
    output_dir = Path(output_dir)
    chunks_file = output_dir / "topics_chunks.npy"      # ← Contient tous les chunks pour la pipeline
    embeddings_file = output_dir / "topics_embeddings.npy"  # ← Contient les embeddings des chunks

    if chunks_file.exists() and embeddings_file.exists():
        print(f"[SKIP] Embeddings déjà présents : {embeddings_file}")
        all_chunks = np.load(chunks_file, allow_pickle=True).tolist()
        embeddings = np.load(embeddings_file)
        return all_chunks, embeddings

    # ← Créer le dossier si inexistant
    output_dir.mkdir(parents=True, exist_ok=True)
    all_chunks, embeddings = embed_mails(
        input_file=json_path,
        output_folder=output_dir,
        model_name=model_name,
        save_name="topics"  # ← Sauvegarde topics_chunks.npy + topics_embeddings.npy
    )
    # ← Plus tard, ces données peuvent servir à calculer emb_2d / labels pour la visualisation t-SNE
    return all_chunks, embeddings

# --------------------------
# Pipeline complète
# --------------------------
def automate_full_process(input_folder, json_file, chunk_output_dir, compute_embeds=True):
    print("\n--- Étape 1 : Nettoyage des mails ---")
    json_path = automate_cleaning(input_folder, json_file)

    print("\n--- Étape 2 : Création des chunks ---")
    df_chunks = chunk_mails(json_path, chunk_output_dir)

    all_chunks, embeddings = None, None
    if compute_embeds:
        print("\n--- Étape 3 : Calcul des embeddings ---")
        all_chunks, embeddings = compute_embeddings(json_path, chunk_output_dir)
        # ← Ici on a déjà les embeddings, ils peuvent être utilisés pour calculer emb_2d / labels
        # emb_2d.npy = t-SNE des embeddings
        # labels.npy = clusters assignés aux chunks
        # chunks.pkl = sauvegarde des chunks pour visualisation

    print("\n[INFO] Pipeline complète terminée !")
    return df_chunks, all_chunks, embeddings

# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    base_dir = Path(__file__).parent

    input_folder = base_dir.parent / "data" / "mail_export" / "celine_guyon"
    json_file = base_dir.parent / "data" / "processed" / "celine_guyon" / "all_cleaned_mails.json"
    chunk_output_dir = base_dir.parent / "data" / "processed" / "clustering" / "topic"

    print("\n=== Lancement de la pipeline complète ===")
    df_chunks, all_chunks, embeddings = automate_full_process(
        input_folder=input_folder,
        json_file=json_file,
        chunk_output_dir=chunk_output_dir,
        compute_embeds=True
    )

    print(f"\n[INFO] Total chunks créés : {len(df_chunks)}")
    if all_chunks is not None:
        print(f"[INFO] Total chunks pour embeddings : {len(all_chunks)}")
        print(f"[INFO] Embeddings shape : {embeddings.shape}")
