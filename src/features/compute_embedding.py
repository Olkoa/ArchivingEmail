from pathlib import Path
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import time

def chunk_text(text, chunk_size=200, overlap=20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def save_embeddings_and_metadata(embeddings, metadata, folder_path, prefix="email_chunks"):
    os.makedirs(folder_path, exist_ok=True)
    np.save(folder_path / f"{prefix}_embeddings.npy", embeddings)
    with open(folder_path / f"{prefix}_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def save_times(times_dict, folder_path, filename="embedding_times.json"):
    os.makedirs(folder_path, exist_ok=True)
    times_path = folder_path / filename
    if times_path.exists():
        with open(times_path, "r", encoding="utf-8") as f:
            existing_times = json.load(f)
    else:
        existing_times = {}
    existing_times.update(times_dict)
    with open(times_path, "w", encoding="utf-8") as f:
        json.dump(existing_times, f, ensure_ascii=False, indent=2)
    print(f"Temps de calcul sauvegardés : {times_path}")

def search_best_email(models, mails, query, folder_path, chunk_size=200, overlap=20, save_prefix=None):
    results = {}
    times = {}

    for model_name in models:
        print(f"\n=== Test avec le modèle: {model_name} ===")
        model = SentenceTransformer(model_name)

        all_chunks = []
        metadata = []

        for mail_id, mail in enumerate(mails):
            chunks = chunk_text(mail, chunk_size, overlap)  # appel correct
            all_chunks.extend(chunks)
            for chunk_id, chunk in enumerate(chunks):  # ✅ renommé
                metadata.append({"mail_id": mail_id, "chunk_id": chunk_id, "text": chunk})

        start_time = time.time()
        embeddings = model.encode(all_chunks, convert_to_numpy=True, show_progress_bar=True)
        query_embedding = model.encode([query], convert_to_numpy=True)
        end_time = time.time()

        times[model_name] = end_time - start_time
        print(f"Temps de calcul des embeddings ({model_name}) : {times[model_name]:.2f} sec")

        similarities = cosine_similarity(query_embedding, embeddings)[0]
        best_idx = np.argmax(similarities)
        best_meta = metadata[best_idx]

        results[model_name] = {
            "mail_id": best_meta["mail_id"],
            "chunk_id": best_meta["chunk_id"],
            "texte_chunk": best_meta["text"],
            "score": similarities[best_idx]
        }

        if save_prefix:
            save_embeddings_and_metadata(embeddings, metadata, folder_path, prefix=f"{save_prefix}_{model_name}")

    save_times(times, folder_path)
    return results


# 🔹 Chemin racine
base_dir = Path(__file__).parent
processed_root = base_dir.parent / "data" / "processed" / "celine_guyon"
output_folder = processed_root  # Tu peux changer si tu veux un sous-dossier spécifique

# 🔹 Lire tous les fichiers JSON dans tous les sous-dossiers
mails = []
for json_file in processed_root.rglob("*.json"):
    if "all_cleaned_mails.json" in json_file.name:  # pour éviter de lire d’autres fichiers JSON si nécessaire
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        mails.extend([e["body"] for e in data])

print(f"Nombre total de mails trouvés : {len(mails)}")

# 🔹 Modèles et requête
models_to_test = [
    "multi-qa-MiniLM-L6-cos-v1",          
    "all-MiniLM-L6-v2",                   
    "all-mpnet-base-v2",                  
    "paraphrase-MiniLM-L12-v2",           
    "multi-qa-mpnet-base-dot-v1",         
    "sentence-t5-base",                   
    "distiluse-base-multilingual-cased-v2", 
    "paraphrase-multilingual-MiniLM-L12-v2" 
]

query = "Je veux voir ma facture"

# 🔹 Calcul embeddings
results = search_best_email(models_to_test, mails, query, output_folder, save_prefix="email_chunks")
