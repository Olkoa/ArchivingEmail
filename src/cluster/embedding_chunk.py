import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

def chunk_text(text, chunk_size=200, overlap=20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
def embed_mails(input_file: Path, output_folder: Path,
                model_name: str = "all-MiniLM-L6-v2",
                save_name: str = "topics"):
    """
    Calcule les embeddings à partir d'un fichier CSV de chunks ou d'un JSON de mails.
    """
    output_folder.mkdir(parents=True, exist_ok=True)

    # --- Lecture du fichier selon le type ---
    input_file = Path(input_file)
    if input_file.suffix == ".csv":
        print(f"[INFO] Lecture CSV : {input_file}")
        df = pd.read_csv(input_file)
        texts = df["body"].dropna().astype(str).tolist()
    elif input_file.suffix == ".json":
        print(f"[INFO] Lecture JSON : {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        texts = [e["body"] for e in data if e.get("body")]
    else:
        raise ValueError(f"Format non supporté : {input_file.suffix}")

    print(f"[INFO] Total textes/chunks à encoder : {len(texts)}")

    # --- Chargement du modèle ---
    print(f"[INFO] Chargement du modèle '{model_name}'...")
    model = SentenceTransformer(model_name)

    print("[INFO] Calcul des embeddings...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    # --- Sauvegarde ---
    chunks_file = output_folder / f"{save_name}_chunks.npy"
    embeddings_file = output_folder / f"{save_name}_embeddings.npy"
    np.save(chunks_file, np.array(texts, dtype=object))
    np.save(embeddings_file, embeddings)

    print(f"[OK] Chunks sauvegardés dans : {chunks_file}")
    print(f"[OK] Embeddings sauvegardés dans : {embeddings_file}")

    return texts, embeddings


base_dir = Path(__file__).parent
processed_dir = base_dir.parent / "data" / "processed" / "celine_guyon"
output_base = base_dir.parent / "data" / "processed" / "clustering" / "topic"


json_files = list(processed_dir.rglob("all_cleaned_mails.json"))

print(f"Found {len(json_files)} JSON files to process.")


for json_file in json_files:
    relative_folder = json_file.parent.relative_to(processed_dir)
    output_folder = output_base / relative_folder
    save_name = "topics"

    embed_mails(json_file, output_folder, model_name="all-MiniLM-L6-v2", save_name=save_name)
 