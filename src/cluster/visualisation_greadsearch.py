import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Chemin vers le CSV du grid search ---
csv_path = "grid_search_results.csv"

# --- Chargement des résultats ---
df = pd.read_csv(csv_path)

# --- Affichage des 10 meilleures combinaisons par silhouette ---
print("\n=== Top 10 combinaisons par Silhouette Score ===")
print(df.sort_values("silhouette", ascending=False).head(10))

# --- Plot Silhouette Score vs param combos ---
plt.figure(figsize=(12, 6))
sns.scatterplot(data=df, x="alpha", y="silhouette", hue="beta", style="min_score", size="gamma", palette="viridis", sizes=(50,200))
plt.title("Silhouette Score selon alpha, beta, gamma et min_score")
plt.xlabel("Alpha")
plt.ylabel("Silhouette Score")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
plt.tight_layout()
plt.show()

# --- Optionnel: histogramme des scores ---
plt.figure(figsize=(8,5))
sns.histplot(df["silhouette"], bins=20, kde=True, color="skyblue")
plt.title("Distribution des Silhouette Scores")
plt.xlabel("Silhouette Score")
plt.ylabel("Count")
plt.show()
