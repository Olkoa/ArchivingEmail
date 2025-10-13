import numpy as np
import pickle
import pandas as pd
from collections import Counter
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px

# --- Paths ---
base_dir = Path(__file__).parent
output_folder = base_dir.parent / "data/processed/clustering/topic/optimize_dbscan"
embeddings_path = output_folder.parent / "topics_embeddings.npy"
chunks_path = output_folder.parent / "topics_chunks.npy"

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

# --- Load embeddings & chunks ---
embeddings_all = np.load(embeddings_path)              # (31635, dim)
chunks_all = np.load(chunks_path, allow_pickle=True)   # (31635,)

# Chargement de la visu existante
emb_2d = np.load("emb_2d.npy")        # (7148, 2)
labels = np.load("labels.npy")        # (7148,)
with open("chunks.pkl", "rb") as f:
    chunks_vis = pickle.load(f)       # (7148,)

# Mapping chunk -> index dans embeddings_all
chunk_to_idx = {c: i for i, c in enumerate(chunks_all)}
vis_indices = [chunk_to_idx[c] for c in chunks_vis]

# Embeddings filtrés alignés avec df_vis
embeddings_vis = embeddings_all[vis_indices]

# --- Dataframe pour la visu ---
df_vis = pd.DataFrame({
    "x": emb_2d[:, 0],
    "y": emb_2d[:, 1],
    "cluster": labels.astype(str),
    "chunk": chunks_vis
})

# --- Bag of Words par cluster ---
cluster_bow = {}
for cid in df_vis["cluster"].unique():
    cluster_chunks = df_vis[df_vis["cluster"] == cid]["chunk"].tolist()
    bow = Counter()
    for chunk in cluster_chunks:
        for word in chunk.lower().split():
            if word not in stopwords:
                bow[word] += 1
    top_words = [w for w, _ in bow.most_common(10)]
    cluster_bow[cid] = ", ".join(top_words)

df_vis["hover"] = df_vis["cluster"].apply(
    lambda c: f"Cluster {c}<br>Top words: {cluster_bow[c]}"
)

# --- Scatter initial ---
def make_figure(filtered_df):
    fig = px.scatter(
        filtered_df, x="x", y="y", color="cluster",
        hover_name="hover",
        title="t-SNE clusters (pré-calculés)",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig.update_traces(marker=dict(size=8))
    return fig

# --- Modèle pour embeddings des requêtes ---
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# --- Recherche sémantique ---
def semantic_search(query, top_k=200):
    q_emb = model.encode([query])
    sims = cosine_similarity(q_emb, embeddings_vis)[0]
    top_idx = np.argsort(sims)[::-1][:top_k]
    return top_idx, sims[top_idx]

# --- Extraction du segment le plus pertinent dans un chunk ---
def best_matching_segment(chunk, query, segment_size=30):
    """
    Retourne la partie du chunk la plus proche du prompt.
    segment_size = nombre de mots par segment.
    """
    words = chunk.split()
    if len(words) <= segment_size:
        return chunk  # chunk court

    # créer les segments
    segments = [" ".join(words[i:i+segment_size]) for i in range(0, len(words), segment_size)]

    # embeddings des segments
    seg_emb = model.encode(segments)
    q_emb = model.encode([query])

    # similarité
    sims = cosine_similarity(q_emb, seg_emb)[0]

    # segment le plus proche
    best_idx = np.argmax(sims)
    return segments[best_idx]

# --- Dash app ---
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H2("t-SNE Clusters + Recherche Sémantique"),
    
    dcc.Input(
        id="semantic-search",
        type="text",
        placeholder="Ex: documents sur la santé...",
        style={"width": "50%", "marginBottom": "20px"}
    ),
    html.Button("Rechercher", id="btn-search", n_clicks=0),

    dcc.Graph(id="scatter-plot", figure=make_figure(df_vis), style={"height": "70vh"}),

    html.Div([
        html.H4("Top résultats de la recherche"),
        html.Pre(id="search-results", style={"whiteSpace": "pre-wrap", "fontSize": 14})
    ], style={"marginTop": 20}),

    html.Pre(id="output-bow", style={"marginTop": 20, "fontSize": 16, "whiteSpace": "pre-wrap"})
])

# --- Callback recherche ---
@app.callback(
    [Output("scatter-plot", "figure"),
     Output("search-results", "children")],
    Input("btn-search", "n_clicks"),
    State("semantic-search", "value")
)
def semantic_filter(n, query):
    if not query or query.strip() == "":
        return make_figure(df_vis), "⚠️ Pas de recherche effectuée."

    top_idx, scores = semantic_search(query, top_k=200)  # top 200 points pour scatter
    filtered = df_vis.iloc[top_idx]

    # Construire un affichage textuel des top résultats
    results_text = "🔎 Résultats les plus proches :\n\n"
    for i, (idx, score) in enumerate(zip(top_idx[:10], scores[:10]), 1):
        chunk = best_matching_segment(df_vis.iloc[idx]["chunk"], query)
        results_text += f"{i}. ({score:.3f}) {chunk}...\n"

    return make_figure(filtered), results_text

# --- Callback Bag-of-Words ---
@app.callback(
    Output("output-bow", "children"),
    Input("scatter-plot", "selectedData")
)
def display_bow(selectedData):
    if selectedData is None or "points" not in selectedData:
        return " Sélectionne des points pour voir le Bag-of-Words."
    indices = [p["pointIndex"] for p in selectedData["points"]]
    selected_chunks = df_vis.iloc[indices]["chunk"].tolist()
    bow = Counter()
    for chunk in selected_chunks:
        for word in chunk.lower().split():
            if word not in stopwords:
                bow[word] += 1
    if not bow:
        return " Aucun mot significatif trouvé."
    top_words = bow.most_common(10)
    return f" Bag-of-Words ({len(selected_chunks)} chunks sélectionnés):\n" + \
           "\n".join([f"{w}: {c}" for w, c in top_words])

if __name__ == "__main__":
    app.run(debug=True)
