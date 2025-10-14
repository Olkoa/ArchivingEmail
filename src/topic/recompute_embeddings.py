import numpy as np
from pathlib import Path
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- Chemins ---
DATA_DIR = Path(r"C:\Users\User.DESKTOP-R6U6E5L\Desktop\LabIA\olkoa\src\data\processed\clustering\topic")
CHUNKS_PATH = DATA_DIR / "topics_chunks.npy"
NEW_EMB_PATH = DATA_DIR / "topics_embeddings_minilm.npy"

# --- Chargement des chunks ---
chunks = np.load(CHUNKS_PATH, allow_pickle=True)
chunks = chunks.tolist()  # s'assurer que c'est une liste
print(f"[INFO] {len(chunks)} chunks chargés.")

# --- Chargement du modèle ---
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("[INFO] Modèle chargé.")

# --- Encodage des chunks ---
embeddings = []
for chunk in tqdm(chunks, desc="Encodage chunks"):
    emb = model.encode(chunk)
    embeddings.append(emb)

embeddings = np.vstack(embeddings)
print(f"[INFO] Embeddings générés avec shape : {embeddings.shape}")

# --- Sauvegarde ---
np.save(NEW_EMB_PATH, embeddings)
print(f"[INFO] Nouveaux embeddings sauvegardés dans {NEW_EMB_PATH}")
