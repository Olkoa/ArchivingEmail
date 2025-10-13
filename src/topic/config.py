from pathlib import Path

# --- Racine du projet ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # Ajustez selon la profondeur de votre fichier

# --- Fichiers générés pour la visualisation ---
VIS_EMB_2D = PROJECT_ROOT / "src/data/semantic/cluster/emb_2d.npy"
VIS_LABELS = PROJECT_ROOT / "src/data/semantic/cluster/labels.npy"
VIS_CHUNKS = PROJECT_ROOT / "src/data/semantic/cluster/chunks.pkl"

# --- Répertoire de sauvegarde des résultats de recherche sémantique ---
SEMANTIC_RESULTS_DIR = PROJECT_ROOT / "src/data/semantic/return_app"

# --- Fichiers originaux embeddings/chunks ---
DATA_DIR = PROJECT_ROOT / "src/data/processed/clustering/topic"
EMBEDDINGS_PATH = DATA_DIR / "topics_embeddings.npy"
CHUNKS_PATH = DATA_DIR / "topics_chunks.npy"

# Stopwords
STOPWORDS = ["alors","au","aucuns","aussi","autre","avant","avec","avoir","bon","car","ce","cela","ces","ceux",
"chaque","ci","comme","comment","dans","des","du","dedans","dehors","depuis","devrait","doit","donc","dos",
"droite","début","elle","elles","en","encore","essai","est","et","eu","fait","faites","fois","font","hors",
"ici","il","ils","je","juste","la","le","les","leur","là","ma","maintenant","mais","mes","mine","moins",
"mon","mot","même","ni","nommés","notre","nous","nouveaux","ou","où","par","parce","parole","pas",
"personnes","peut","peu","pièce","plupart","pour","pourquoi","quand","que","quel","quelle","quelles",
"quels","qui","sa","sans","ses","seulement","si","sien","son","sont","sous","soyez","sujet","sur","ta",
"tandis","tellement","tels","tes","ton","tous","tout","trop","très","tu","valeur","voie","voient",
"vont","votre","vous","vu","ça","étaient","état","étions","été","être"]
