import streamlit as st
import plotly.express as px
from collections import Counter
from src.topic.config import STOPWORDS
from src.topic.data_loader import load_data
from src.topic.semantic_search import semantic_search
from src.topic.semantic_utils import (
    perform_semantic_search,
    save_results_to_json,
    highlight_query_terms,
    compute_bow
)

# --- Charger les données ---
embeddings_vis, df_vis = load_data()

# --- Calcul du Bag of Words par cluster ---
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

# --- Initialisation de session_state pour stocker les résultats ---
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = df_vis.copy()
if "display_text" not in st.session_state:
    st.session_state.display_text = ""

# --- Interface ---
st.title("🧠 t-SNE Clusters + Recherche Sémantique")

# Champ de recherche
query = st.text_input("🔍 Rechercher des documents...", "")

# Bouton de recherche
if st.button("Rechercher"):
    if query.strip() == "":
        st.info("Pas de recherche effectuée.")
        st.session_state.filtered_df = df_vis.copy()
        st.session_state.display_text = ""
    else:
        filtered_df, raw_results = perform_semantic_search(
            query, embeddings_vis, df_vis, semantic_search
        )

        # Stocker le DataFrame filtré
        st.session_state.filtered_df = filtered_df

        # Préparer les résultats textuels
        chunks_to_display = []
        for r in raw_results:
            highlighted = highlight_query_terms(r["text"], query)
            chunks_to_display.append(f"{r['rank']}. ({r['score']:.3f}) {highlighted}")
        st.session_state.display_text = "\n\n".join(chunks_to_display)

        # Sauvegarde automatique
        save_results_to_json(query, raw_results)

# --- Sélection des clusters à afficher ---
st.subheader("🎨 Visualisation t-SNE")
selected_clusters = st.multiselect(
    "Sélectionne des clusters à afficher :",
    sorted(df_vis["cluster"].unique()),
    default=sorted(df_vis["cluster"].unique())
)

# Filtrer selon la recherche ET les clusters
filtered_plot = st.session_state.filtered_df[
    st.session_state.filtered_df["cluster"].isin(selected_clusters)
]

# Affichage du graphique
fig = px.scatter(
    filtered_plot,
    x="x",
    y="y",
    color="cluster",
    hover_data=["hover"],
    title=f"t-SNE projection ({len(filtered_plot)} points affichés)"
)
st.plotly_chart(fig, use_container_width=True)

# --- Affichage des résultats textuels ---
if st.session_state.display_text:
    st.subheader("📄 Top résultats de la recherche")
    st.markdown(st.session_state.display_text, unsafe_allow_html=True)

# --- Bag of Words ---
st.subheader("🧩 Bag-of-Words du cluster sélectionné")
if selected_clusters:
    all_chunks = filtered_plot["chunk"].tolist()
    bow = compute_bow(all_chunks)
    if bow:
        st.text("\n".join([f"{w}: {c}" for w, c in bow]))
    else:
        st.text("Aucun mot significatif trouvé.")
else:
    st.text("Sélectionne un cluster pour afficher son Bag-of-Words.")
