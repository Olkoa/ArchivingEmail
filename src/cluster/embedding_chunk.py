import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

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

def embed_mails(input_file: Path, output_folder: Path, model_name: str = "all-MiniLM-L6-v2",
                chunk_size: int = 200, overlap: int = 20, save_name: str = "topics"):
    """
    Chunk les mails, calcule les embeddings et sauvegarde les résultats.
    """
    output_folder.mkdir(parents=True, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    mails = [e["body"] for e in data]

    all_chunks = []
    for mail in mails:
        chunks = chunk_text(mail, chunk_size, overlap)
        all_chunks.extend(chunks)

    print(f"{input_file}: Total chunks = {len(all_chunks)}")

    print(f"Loading model '{model_name}'...")
    model = SentenceTransformer(model_name)
    print("Starting embedding process ...")
    embeddings = model.encode(all_chunks, convert_to_numpy=True, show_progress_bar=True)

    chunks_file = output_folder / f"{save_name}_chunks.npy"
    embeddings_file = output_folder / f"{save_name}_embeddings.npy"

    np.save(chunks_file, np.array(all_chunks, dtype=object))
    np.save(embeddings_file, embeddings)

    print(f"Chunks saved to: {chunks_file}")
    print(f"Embeddings saved to: {embeddings_file}")

    return all_chunks, embeddings


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
 