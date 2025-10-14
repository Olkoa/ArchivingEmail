import json
from datetime import datetime
from pathlib import Path
from collections import Counter
from config import STOPWORDS, SEMANTIC_RESULTS_DIR
import plotly.express as px



def perform_semantic_search(query, embeddings_vis, df_vis, semantic_search_func, top_k=200):
    """
    Effectue une recherche sémantique et renvoie les meilleurs résultats
    (indices, scores, texte brut et embeddings associés).
    """
    top_idx, scores = semantic_search_func(query, embeddings_vis, top_k=top_k)
    filtered = df_vis.iloc[top_idx]

    raw_results = []
    for i, (idx, score) in enumerate(zip(top_idx[:10], scores[:10]), 1):
        chunk = df_vis.iloc[idx]["chunk"]
        embedding = embeddings_vis[idx].tolist()  # Convertit le vecteur NumPy en liste JSON-serializable

        raw_results.append({
            "rank": i,
            "score": float(score),
            "text": chunk,
            "embedding": embedding
        })

    return filtered, raw_results


def save_results_to_json(query, results, output_dir=SEMANTIC_RESULTS_DIR, prefix="search_results"):
    """
    Sauvegarde les résultats de recherche dans un fichier JSON
    dans le dossier défini dans config.py (SEMANTIC_RESULTS_DIR).
    """
    output_dir = Path(output_dir) if output_dir else SEMANTIC_RESULTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    filepath = output_dir / filename

    data = {
        "query": query,
        "timestamp": timestamp,
        "results": results
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Résultats sauvegardés dans : {filepath}")
    return filepath

def highlight_query_terms(text, query):
    """
    Met en valeur les mots du query dans un texte (HTML avec <span>).
    """
    highlighted = text
    for word in query.lower().split():
        highlighted = highlighted.replace(
            word, f"<span style='color:red;font-weight:bold'>{word}</span>"
        )
    return highlighted




def make_figure(df):
    """
    Crée une figure Plotly t-SNE à partir du DataFrame.
    """
    if "x" not in df.columns or "y" not in df.columns:
        raise ValueError("Les colonnes 'x' et 'y' doivent exister dans le DataFrame pour afficher le t-SNE.")

    fig = px.scatter(
        df,
        x="x",
        y="y",
        color="cluster",
        hover_data=["hover"],
        title="Visualisation t-SNE des chunks",
        opacity=0.8
    )

    fig.update_traces(marker=dict(size=6))
    fig.update_layout(
        dragmode='lasso',
        margin=dict(l=10, r=10, t=40, b=10),
        height=700,
        showlegend=True
    )

    return fig



def compute_bow(chunks, stopwords=STOPWORDS, top_n=10):
    """
    Calcule les mots les plus fréquents (bag-of-words) dans une liste de textes.
    """
    bow = Counter()
    for chunk in chunks:
        for word in chunk.lower().split():
            if word not in stopwords:
                bow[word] += 1
    return bow.most_common(top_n)
