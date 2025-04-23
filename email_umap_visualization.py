import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import umap
import umap.plot

# Load your DataFrame with embeddings and clusters
df_emails_with_clusters = pd.read_pickle('data/Projects/Projet Demo/emails_with_clusters.pkl')

# Filter to only rows with valid embeddings
valid_embeddings_mask = df_emails_with_clusters['embeddings_values'].notna()
filtered_df = df_emails_with_clusters[valid_embeddings_mask].copy()

print(f"Working with {len(filtered_df)} emails that have valid embeddings")

# Convert the list of embeddings to a numpy array for UMAP
embeddings_array = np.array(filtered_df['embeddings_values'].tolist())
print(f"Embeddings array shape: {embeddings_array.shape}")

# Get the cluster labels
cluster_labels = filtered_df['cluster'].astype(int).values

# ----- UMAP -----
# Initialize UMAP with parameters appropriate for your data size
n_samples = len(embeddings_array)
neighbors = min(30, max(5, n_samples // 50))  # Adjust based on your data size

print(f"Initializing UMAP with n_neighbors={neighbors}")

reducer = umap.UMAP(
    n_components=2,
    n_neighbors=neighbors,
    metric='cosine',     
    min_dist=0.1,        # Controls how tightly points are packed together
    random_state=42      # For reproducibility
)

# Fit UMAP to your embeddings and transform to 2D
embedding = reducer.fit_transform(embeddings_array)
print(f"UMAP embedding shape: {embedding.shape}")

# ----- Plotting with UMAP using KMeans clusters -----
plt.figure(figsize=(12, 10))

# Create a scatter plot
scatter = plt.scatter(
    embedding[:, 0], 
    embedding[:, 1], 
    c=cluster_labels, 
    cmap='viridis', 
    s=50,  # Marker size
    alpha=0.7
)

# Add a colorbar
plt.colorbar(scatter, label='Cluster')

# Add cluster annotations
for cluster_id in np.unique(cluster_labels):
    # Find the center of each cluster
    cluster_points = embedding[cluster_labels == cluster_id]
    if len(cluster_points) > 0:
        center_x = np.mean(cluster_points[:, 0])
        center_y = np.mean(cluster_points[:, 1])
        
        # Get the cluster name if available
        if 'cluster_names' in locals() and cluster_id in cluster_names:
            cluster_name = cluster_names[cluster_id]
        else:
            # Count emails in cluster
            count = np.sum(cluster_labels == cluster_id)
            cluster_name = f"Cluster {cluster_id} ({count} emails)"
        
        # Annotate with cluster name
        plt.annotate(
            cluster_name,
            (center_x, center_y),
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7)
        )

plt.title('Email Clusters Visualization (UMAP)')
plt.tight_layout()
plt.savefig('email_clusters_umap.png')
plt.show()

# ----- Alternative UMAP visualization using umap.plot -----
string_cluster_labels = [f"Cluster {label}" for label in cluster_labels]
print("Creating UMAP plot with cluster labels...")
fig = umap.plot.points(reducer, labels=np.array(string_cluster_labels))
plt.title('Email Clusters Visualization (UMAP - Cluster Labels)')
plt.savefig('email_clusters_umap_labeled.png')
plt.show()

# ----- Bonus: Interactive hover visualization -----
try:
    import plotly.express as px
    
    # Create a DataFrame for plotly
    umap_df = pd.DataFrame({
        'UMAP1': embedding[:, 0],
        'UMAP2': embedding[:, 1],
        'cluster': cluster_labels,
        'subject': filtered_df['subject'].values if 'subject' in filtered_df.columns else [f"Email {i}" for i in range(len(embedding))]
    })
    
    # Create an interactive scatter plot
    fig = px.scatter(
        umap_df, 
        x='UMAP1', 
        y='UMAP2', 
        color='cluster',
        hover_data=['subject'],
        title='Interactive Email Clusters (UMAP)',
        color_continuous_scale='viridis'
    )
    
    # Save as HTML file for interactive viewing
    fig.write_html('email_clusters_interactive.html')
    print("Created interactive visualization: email_clusters_interactive.html")
    
except ImportError:
    print("Plotly not available - skipping interactive visualization")
