# import pandas as pd
# import plotly.express as px

# # --- Charger les résultats ---
# df = pd.read_csv("grid_search_results.csv")

# # --- Visualiser Silhouette Score ---
# fig_sil = px.scatter_3d(
#     df, x="alpha", y="beta", z="gamma",
#     size="silhouette", color="silhouette",
#     hover_data=["min_score", "davies_bouldin", "calinski_harabasz", "n_clusters"]
# )
# fig_sil.update_layout(title="Grid Search - Silhouette Score")
# fig_sil.show()

# # --- Visualiser Davies-Bouldin Score (plus petit = mieux) ---
# fig_db = px.scatter_3d(
#     df, x="alpha", y="beta", z="gamma",
#     size="davies_bouldin", color="davies_bouldin",
#     hover_data=["min_score", "silhouette", "calinski_harabasz", "n_clusters"]
# )
# fig_db.update_layout(title="Grid Search - Davies-Bouldin Score")
# fig_db.show()

# # --- Visualiser Calinski-Harabasz Score (plus grand = mieux) ---
# fig_ch = px.scatter_3d(
#     df, x="alpha", y="beta", z="gamma",
#     size="calinski_harabasz", color="calinski_harabasz",
#     hover_data=["min_score", "silhouette", "davies_bouldin", "n_clusters"]
# )
# fig_ch.update_layout(title="Grid Search - Calinski-Harabasz Score")
# fig_ch.show()

# # --- Optionnel : trouver la meilleure combinaison selon Silhouette ---
# best = df.sort_values("silhouette", ascending=False).iloc[0]
# print("[INFO] Meilleure combinaison selon Silhouette Score :")
# print(best)
