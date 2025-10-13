import numpy as np
import dash
from dash import dcc, html, Input, Output, State
from collections import Counter
from config import STOPWORDS, SEMANTIC_RESULTS_DIR
from data_loader import load_data
from semantic_search import semantic_search
from semantic_utils import (
    perform_semantic_search,
    save_results_to_json,
    highlight_query_terms,
    make_figure,
    compute_bow
)

embeddings_vis, df_vis = load_data()

# --- Calcul du Bag of Words par cluster (pour l’affichage du hover) ---
cluster_bow = {}
for cid in df_vis["cluster"].unique():
    cluster_chunks = df_vis[df_vis["cluster"] == cid]["chunk"].tolist()
    bow = Counter()
    for chunk in cluster_chunks:
        for word in chunk.lower().split():
            if word not in STOPWORDS:
                bow[word] += 1
    top_words = [w for w, _ in bow.most_common(10)]
    cluster_bow[cid] = ", ".join(top_words)

df_vis["hover"] = df_vis["cluster"].apply(
    lambda c: f"Cluster {c}<br>Top words: {cluster_bow[c]}"
)


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("t-SNE Clusters + Recherche Sémantique"),

    # Champ de recherche
    dcc.Input(
        id="semantic-search",
        type="text",
        placeholder="Ex: documents sur la santé...",
        style={"width": "50%", "marginBottom": "20px"}
    ),
    html.Button("Rechercher", id="btn-search", n_clicks=0),

    # Graphique t-SNE
    dcc.Graph(
        id="scatter-plot",
        figure=make_figure(df_vis),
        style={"height": "70vh"}
    ),

    # Résultats de recherche
    html.Div([
        html.H4("Top résultats de la recherche"),
        dcc.Markdown(
            id="search-results",
            style={"whiteSpace": "pre-wrap", "fontSize": 14},
            dangerously_allow_html=True
        )
    ], style={"marginTop": 20}),

    # Bag of Words dynamique
    html.Pre(
        id="output-bow",
        style={"marginTop": 20, "fontSize": 16, "whiteSpace": "pre-wrap"}
    )
])


@app.callback(
    [Output("scatter-plot", "figure"),
     Output("search-results", "children")],
    Input("btn-search", "n_clicks"),
    State("semantic-search", "value")
)
def semantic_filter(n, query):
    if not query or query.strip() == "":
        return make_figure(df_vis), "Pas de recherche effectuée."

    # Exécution de la recherche sémantique
    filtered, raw_results = perform_semantic_search(
        query, embeddings_vis, df_vis, semantic_search
    )

    # Mise en forme pour affichage
    chunks_to_display = []
    for r in raw_results:
        highlighted = highlight_query_terms(r["text"], query)
        chunks_to_display.append(f"{r['rank']}. ({r['score']:.3f}) {highlighted}")

    display_text = "\n\n".join(chunks_to_display)

    # Sauvegarde automatique en JSON
    save_results_to_json(query, raw_results)

    return make_figure(filtered), display_text



@app.callback(
    Output("output-bow", "children"),
    Input("scatter-plot", "selectedData")
)
def display_bow(selectedData):
    if selectedData is None or "points" not in selectedData:
        return "Sélectionne des points pour voir le Bag-of-Words."

    indices = [p["pointIndex"] for p in selectedData["points"]]
    selected_chunks = df_vis.iloc[indices]["chunk"].tolist()
    bow = compute_bow(selected_chunks)

    if not bow:
        return "Aucun mot significatif trouvé."

    text = f"Bag-of-Words ({len(selected_chunks)} chunks sélectionnés):\n"
    text += "\n".join([f"{w}: {c}" for w, c in bow])
    return text


if __name__ == "__main__":
    app.run(debug=True)
