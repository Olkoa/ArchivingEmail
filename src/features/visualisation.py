"""
Comparaison des modèles d'embeddings et visualisation
Affiche et sauvegarde les scores et le temps de calcul.
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import pickle
from pathlib import Path
from tqdm import tqdm
import pickle

base_dir = Path(__file__).parent.parent
output_folder = base_dir.parent / "data" / "Projects" / ACTIVE_PROJECT / "semantic_search" / "clustering"
output_folder.mkdir(parents=True, exist_ok=True)

output_file_1 = output_folder / "hdbscan" / "silhouette_score.pkl"
output_file_2 = output_folder / "hdbscan" /"davies.pkl"
output_file_3 = output_folder /  "hdbscan" /"calinski.pkl"
output_file_4 = output_folder /  "hdbscan" /"labels.pkl"
time_file = base_dir.parent / "data" / "processed" / "celine_guyon" / "Boîte de réception" / "embedding_times.json"

with open(time_file, "r", encoding="utf-8") as f:
    times = json.load(f)

with open(output_file_1, "rb") as f:
    silhouette_score = pickle.load(f)

with open(output_file_2, "rb") as f:
    davies_score = pickle.load(f)

with open(output_file_3, "rb") as f:
    calinski = pickle.load(f)

with open(output_file_4, "rb") as f:
    labels = pickle.load(f)

scores = {
    "silhouette score": silhouette_score,
    "davies_score": davies_score,
    "calinski": calinski
}

figures_folder = output_folder / "figures"
figures_folder.mkdir(parents=True, exist_ok=True)

def plot_histo_cluster(scores, show_plot=True):
    for method, score in scores.items():
        sorted_scores = dict(sorted(score.items(), key=lambda item: item[1], reverse=True))
        models = list(sorted_scores.keys())
        values = list(sorted_scores.values())

        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(values)))

        plt.figure(figsize=(12, 6))
        bars = plt.bar(models, values, color=colors, edgecolor="black")

        for bar, value in zip(bars, values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.002,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        plt.xticks(rotation=45, ha="right", fontsize=11)
        plt.ylabel("Score", fontsize=12)
        plt.title(f"Comparaison des modèles d'embeddings ({method})", fontsize=14, fontweight="bold")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()

        save_path = figures_folder / f"{method.replace(' ', '_')}_comparison.png"
        plt.savefig(save_path, dpi=300)
        print(f"Figure sauvegardée : {save_path}")

        if show_plot:
            plt.show()
        else:
            plt.close()

def plot_embedding_times(times, show_plot=True):
    models = list(times.keys())
    values = [times[m] for m in models]

    colors = plt.cm.plasma(np.linspace(0.3, 0.9, len(models)))

    plt.figure(figsize=(12, 6))
    bars = plt.bar(models, values, color=colors, edgecolor="black")

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f"{value:.2f}s",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.xticks(rotation=45, ha="right", fontsize=11)
    plt.ylabel("Temps de calcul (secondes)", fontsize=12)
    plt.title("Comparaison du temps de calcul des embeddings par modèle", fontsize=14, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    save_path = figures_folder / "embedding_times_comparison.png"
    plt.savefig(save_path, dpi=300)
    print(f"Figure sauvegardée : {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()

def plot_clusters_per_model(labels: dict, save_folder: Path, title: str = "Nombre de clusters par modèle", highlight_model: str = None, show_plot: bool = True):
    """
    Affiche et sauvegarde un bar plot du nombre de clusters par modèle.

    Args:
        labels (dict): dictionnaire {nom_model: liste_de_labels}.
        save_folder (Path): dossier où sauvegarder la figure.
        title (str): titre du graphique.
        highlight_model (str, optional): modèle à mettre en évidence (barre colorée différemment).
        show_plot (bool): si True, afficher le plot après création.
    """
    save_folder.mkdir(parents=True, exist_ok=True)

    # Calcul du nombre de clusters
    cluster_counts = {key: len(set(value)) for key, value in labels.items()}

    models = list(cluster_counts.keys())
    counts = list(cluster_counts.values())

    # Couleurs : mettre en évidence si highlight_model est défini
    colors = []
    cmap = plt.cm.viridis(np.linspace(0.3, 0.9, len(models)))
    for i, model in enumerate(models):
        if highlight_model and model == highlight_model:
            colors.append("orange")
        else:
            colors.append(cmap[i])

    plt.figure(figsize=(12, 6))
    bars = plt.bar(models, counts, color=colors, edgecolor="black")

    # Valeurs au-dessus des barres
    for bar, count in zip(bars, counts):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            f"{count}",
            ha="center",
            va="bottom",
            fontsize=10
        )

    plt.xticks(rotation=45, ha="right", fontsize=11)
    plt.ylabel("Nombre de clusters", fontsize=12)
    plt.title(title, fontsize=14, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    # Sauvegarde
    save_path = save_folder / "clusters_per_model.png"
    plt.savefig(save_path, dpi=300)
    if show_plot:
        plt.show()
    else:
        plt.close()
    print(f"Figure sauvegardée : {save_path}")


for key, value in labels.items():
    print(f"Pour le model {key}, on a {len(set(value))} clusters")

plot_histo_cluster(scores, show_plot=True)

plot_embedding_times(times, show_plot=True)

plot_clusters_per_model(labels, save_folder=figures_folder, highlight_model="all-MiniLM-L6-v2")

print("Toutes les figures ont été générées et sauvegardées dans :", figures_folder)


# all-MiniLM-L6-v2 mieux ? Je pense...