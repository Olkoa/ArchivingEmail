import pandas as pd
df4 = pd.read_pickle("df4_with_embeddings.pkl")
df_filtered = df4[df4.index == df4['medoid_index']]
medoid_rows=df_filtered
import numpy as np
from sklearn.preprocessing import normalize

# Step 1: Separate untouched rows

to_cluster_df = medoid_rows
#to_cluster_df = medoid_rows
medoid_embeddings = np.array(to_cluster_df['embedding'].tolist())
medoid_embeddings = normalize(medoid_embeddings)
from scipy.cluster.hierarchy import linkage, dendrogram

linked = linkage(medoid_embeddings, method='ward')  # or 'average', 'complete'
import matplotlib.pyplot as plt

labels = to_cluster_df['topic'].fillna('').astype(str).tolist()

plt.figure(figsize=(16, 6))
dendrogram(
    linked,
    labels=labels,
    leaf_rotation=90.,
    leaf_font_size=8.,
    color_threshold=0.7  # Optional threshold
)
plt.axhline(y=0.7, c='red', ls='--')
plt.title("Dendrogram of Medoid Topics")
plt.xlabel("Topics (Medoids)")
plt.ylabel("Distance")
plt.tight_layout()
plt.show()

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize
from scipy.cluster.hierarchy import linkage, fcluster

# Normalize embeddings
medoid_embeddings = np.array(medoid_rows['embedding'].tolist())
medoid_embeddings = normalize(medoid_embeddings)

# Hierarchical clustering
linked = linkage(medoid_embeddings, method='ward')

# Heights from 0.4 to 3.5
heights = np.round(np.arange(0.1, 3.6, 0.05), 1)

# DataFrame to store only meaningful clustering steps
cluster_levels_df = pd.DataFrame(index=medoid_rows.index)
prev_labels = None

for h in heights:
    labels = fcluster(linked, t=h, criterion='distance')
    
    # Only add if the labels changed
    if prev_labels is None or not np.array_equal(labels, prev_labels):
        cluster_levels_df[f'height_{h:.1f}'] = labels
        prev_labels = labels

# Add topic for reference
cluster_levels_df['topic'] = medoid_rows['topic'].fillna('').astype(str).values

# Save
cluster_levels_df.to_csv("clusters_by_height_filtered.csv", index=False)


print(cluster_levels_df)
from scipy.cluster.hierarchy import fcluster

# Step 1: Cut the dendrogram at height 1.4
cluster_labels = fcluster(linked, t=0.7, criterion='distance')

# Step 2: Add cluster labels to your DataFrame
to_cluster_df['cluster'] = 999000+cluster_labels

# Optional: View unique topics per cluster
grouped_topics = to_cluster_df.groupby('cluster')['topic'].apply(list)

# Save or print them
print(grouped_topics)

# You can also convert to a dictionary if needed
cluster_dict = grouped_topics.to_dict()

# Or save as a CSV or JSON
to_cluster_df.to_csv("clustered_topics_tt.csv", index=False)
# OR
grouped_topics.to_json("grouped_topics_tt.json")

from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import numpy as np

# Save
np.save("linked_matrix.npy", linked)


