import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

base_dir = Path(__file__).parent
results_file = base_dir / "grid_search_results.csv"

df = pd.read_csv(results_file)
print(f"[INFO] {len(df)} combinaisons chargées.")

def custom_score(row, w_sil=1.0, w_db=-0.5, w_ch=0.2):
    return (
        w_sil * row["silhouette"] +
        w_db * row["davies_bouldin"] +
        w_ch * row["calinski_harabasz"]
    )

df["custom_score"] = df.apply(custom_score, axis=1)

def plot_all_scores(df):
    metrics = ["silhouette", "davies_bouldin", "calinski_harabasz", "custom_score", "n_clusters"]
    titles = ["Silhouette Score", "Davies-Bouldin Score", "Calinski-Harabasz Score", "Score Custom", "Nombre de clusters"]

    fig, axes = plt.subplots(len(metrics), 1, figsize=(14, 20), sharex=True)

    for ax, metric, title in zip(axes, metrics, titles):
        ax.plot(df.index, df[metric], marker='o', linestyle='-', alpha=0.7)
        ax.set_ylabel(metric)
        ax.set_title(title)
        ax.grid(True)

    axes[-1].set_xlabel("Combinaison testée")
    plt.tight_layout()
    plt.show()


plot_all_scores(df)

# idx = 55
# comb_56 = df.iloc[idx]

# print("\n=== Paramètres de la combinaison 56 ===")
# print(comb_56[["alpha", "beta", "gamma", "min_score"]])
# print(f"Silhouette: {comb_56['silhouette']:.3f}")
# print(f"Davies-Bouldin: {comb_56['davies_bouldin']:.3f}")
# print(f"Calinski-Harabasz: {comb_56['calinski_harabasz']:.3f}")
# print(f"Nombre de clusters: {comb_56['n_clusters']}")
# print(f"Score custom: {comb_56['custom_score']:.3f}")
