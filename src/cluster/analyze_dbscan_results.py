import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

def analyze_dbscan_results(results_path: Path, prefix: str = "topics"):
    # Vérification que le fichier existe
    if not results_path.exists():
        raise FileNotFoundError(f"❌ Fichier non trouvé : {results_path}")

    print(f"📂 Chargement des résultats depuis : {results_path}")
    with open(results_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    # Transformer en DataFrame
    df = pd.DataFrame(summary)

    # 🔹 Supprimer les lignes où au moins un score est NaN
    df = df.dropna(subset=["silhouette", "davies_bouldin", "calinski_harabasz"]).reset_index(drop=True)

    # Créer une version abrégée des clés
    df["short_key"] = [f"v{i+1}" for i in range(len(df))]

    # 🔹 Calculer pourcentage d'outliers
    df["pct_outliers"] = df["n_outliers"] / (df["n_outliers"] + df["n_clusters"])

    # 🔹 Normalisation pour score composite
    scaler = MinMaxScaler()
    df["silhouette_norm"] = scaler.fit_transform(df[["silhouette"]])
    df["davies_norm"] = 1 - scaler.fit_transform(df[["davies_bouldin"]])
    df["n_clusters_norm"] = 1 - scaler.fit_transform(df[["n_clusters"]])
    df["outliers_norm"] = 1 - scaler.fit_transform(df[["pct_outliers"]])

    # 🔹 Score composite
    # Formule : composite_score = 0.4*silhouette_norm + 0.3*davies_norm + 0.1*n_clusters_norm + 0.2*outliers_norm
    df["composite_score"] = (
        df["silhouette_norm"] * 0.4 +
        df["davies_norm"] * 0.3 +
        df["n_clusters_norm"] * 0.1 +
        df["outliers_norm"] * 0.2
    )

    # Colonnes de scores pour histogrammes
    score_metrics = ["silhouette", "davies_bouldin", "calinski_harabasz"]
    extra_metrics = ["n_clusters", "n_outliers"]

    # 🎨 Histogrammes pour scores
    for metric in score_metrics:
        plt.figure(figsize=(12, 6))
        plt.bar(df["short_key"], df[metric], color="skyblue", edgecolor="black")
        plt.title(f"{metric.replace('_',' ').capitalize()} par configuration ({prefix})", fontsize=16, weight="bold")
        plt.xlabel("Configurations (abrégées)", fontsize=12)
        plt.ylabel(metric.replace('_',' ').capitalize(), fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3, linestyle="--")
        plt.tight_layout()
        plt.show()

    # 📊 Histogrammes pour clusters et outliers
    for metric in extra_metrics:
        plt.figure(figsize=(12, 6))
        plt.bar(
            df["short_key"],
            df[metric],
            color="salmon" if metric == "n_outliers" else "lightgreen",
            edgecolor="black",
        )
        plt.title(f"{metric.replace('_', ' ').capitalize()} par configuration ({prefix})", fontsize=16, weight="bold")
        plt.xlabel("Configurations (abrégées)", fontsize=12)
        plt.ylabel(metric.replace("_", " ").capitalize(), fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3, linestyle="--")
        plt.tight_layout()
        plt.show()

    # 🔹 Histogramme pour composite score
    plt.figure(figsize=(12, 6))
    plt.bar(df["short_key"], df["composite_score"], color="gold", edgecolor="black")
    plt.title(f"Composite Score par configuration ({prefix})", fontsize=16, weight="bold")
    plt.xlabel("Configurations (abrégées)", fontsize=12)
    plt.ylabel("Composite Score", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    plt.show()

    # 🔹 Sauvegarde du DataFrame
    output_dir = results_path.parent
    csv_path = output_dir / f"{prefix}_dbscan_summary.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"\n💾 Tableau sauvegardé en CSV : {csv_path}")

    # 🔹 Top 5 modèles selon le score composite
    top5 = df.sort_values("composite_score", ascending=False).head(10)
    print("\n🏆 Top 10 modèles DBSCAN (score composite) :")
    print(top5[["short_key", "n_clusters", "n_outliers", "silhouette", "davies_bouldin", "composite_score"]])

    return df, top5


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    results_path = (
        base_dir.parent
        / "data"
        / "processed"
        / "clustering"
        / "topic"
        / "optimize_dbscan"
        / "topics_dbscan_summary.json"
    )

    df, top5 = analyze_dbscan_results(results_path, prefix="topics")

vi = "v7"
vi_row = df[df["short_key"] == vi]
if not vi_row.empty:
    full_model_name = vi_row["key"].values[0]
    print(f"📌 Le modèle correspondant à {vi} est : {full_model_name}")
else:
    print("❌ v8 non trouvé dans le DataFrame")
