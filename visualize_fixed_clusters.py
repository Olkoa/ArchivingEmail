import pandas as pd
import os
import numpy as np
import plotly.express as px

# Load the existing data with clusters
try:
    df_emails_with_clusters = pd.read_pickle('data/Projects/Projet Demo/emails_with_clusters.pkl')
    print(f"Successfully loaded clustered emails: {df_emails_with_clusters.shape}")
except Exception as e:
    print(f"Error loading clustered data: {e}")
    exit(1)

# ===== CRUCIAL FIX: COLOR ASSIGNMENT CONSISTENCY =====
print("\n===== FIXING CLUSTER VISUALIZATION =====")

# Filter out emails without cluster assignments
valid_rows = df_emails_with_clusters.dropna(subset=['cluster_id', 'cluster_name'])
print(f"Working with {len(valid_rows)} emails that have valid clusters")

# We need to ensure that:
# 1. Each cluster ID maps to exactly one cluster name
# 2. Each cluster name maps to exactly one color

# Get a clean mapping from cluster ID to name
id_to_name_map = valid_rows.groupby('cluster_id')['cluster_name'].first().to_dict()
print("\nCluster ID to Name mapping:")
for cluster_id, name in id_to_name_map.items():
    count = len(valid_rows[valid_rows['cluster_id'] == cluster_id])
    print(f"  Cluster ID '{cluster_id}' -> '{name}' ({count} emails)")

# Get the unique cluster names
unique_names = sorted(id_to_name_map.values())

# Create an explicit color mapping (name -> color)
# Using a qualitative color scale with fixed assignment
colors = px.colors.qualitative.Vivid[:len(unique_names)]
color_mapping = {name: color for name, color in zip(unique_names, colors)}

print("\nExplicit color mapping:")
for name, color in color_mapping.items():
    print(f"  '{name}' -> {color}")

# Load data for TSNE visualization
# Check if we have precalculated TSNE coordinates
tsne_filepath = 'data/Projects/Projet Demo/tsne_coordinates.pkl'

if os.path.exists(tsne_filepath):
    print("\nLoading pre-calculated TSNE coordinates...")
    tsne_data = pd.read_pickle(tsne_filepath)
    # Extract the coordinates and associated email IDs
    tsne_coords = tsne_data['coords']
    email_ids = tsne_data['email_ids']
else:
    # We need to recalculate TSNE from the embeddings
    print("\nCalculating TSNE coordinates from embeddings...")
    from sklearn.manifold import TSNE
    
    # Extract embeddings from emails with valid clusters
    valid_embeddings = valid_rows['embeddings_values'].dropna().tolist()
    email_ids = valid_rows.dropna(subset=['embeddings_values']).index.tolist()
    
    # Calculate TSNE coordinates
    perplexity = min(30, max(5, len(valid_embeddings) // 10))
    print(f"Using TSNE with perplexity={perplexity}")
    
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
    tsne_coords = tsne.fit_transform(np.array(valid_embeddings))
    
    # Save for future use
    os.makedirs(os.path.dirname(tsne_filepath), exist_ok=True)
    pd.to_pickle({
        'coords': tsne_coords,
        'email_ids': email_ids
    }, tsne_filepath)

# Create a DataFrame for visualization with consistent naming and colors
tsne_df = pd.DataFrame({
    'TSNE1': tsne_coords[:, 0],
    'TSNE2': tsne_coords[:, 1],
    'email_id': email_ids
})

# Add cluster information from the original DataFrame
tsne_df['cluster_id'] = tsne_df['email_id'].map(
    valid_rows['cluster_id'].to_dict()
)

# Map cluster IDs to names using our consistent mapping
tsne_df['cluster_name'] = tsne_df['cluster_id'].map(id_to_name_map)

# Add subject for hover information
tsne_df['subject'] = tsne_df['email_id'].map(
    valid_rows['subject'].to_dict()
)

# Create the visualization with explicit color mapping
print("\nCreating visualization with fixed color mapping...")
fig = px.scatter(
    tsne_df,
    x='TSNE1',
    y='TSNE2',
    color='cluster_name',
    hover_data=['subject', 'cluster_id', 'email_id'],
    title='Interactive Email Clusters (TSNE) - Fixed Color Mapping',
    color_discrete_map=color_mapping
)

# Improve hover information
fig.update_traces(
    hovertemplate="<b>Email:</b> %{customdata[0]}<br><b>Cluster ID:</b> %{customdata[1]}<br><b>Email ID:</b> %{customdata[2]}<br><b>Cluster:</b> %{customdata[3]}<extra></extra>",
    customdata=np.column_stack((
        tsne_df['subject'].astype(str),
        tsne_df['cluster_id'].astype(str),
        tsne_df['email_id'].astype(str),
        tsne_df['cluster_name'].astype(str)
    ))
)

# Improve layout
fig.update_layout(
    legend_title_text='Clusters',
    xaxis_title='TSNE Dimension 1',
    yaxis_title='TSNE Dimension 2',
    legend=dict(
        title_font=dict(size=14),
        font=dict(size=12),
        itemsizing='constant',
        orientation='v',
        yanchor="top",
        y=1.0,
        xanchor="right",
        x=1.15,
        bordercolor="Black",
        borderwidth=1
    ),
    margin=dict(r=150)
)

# Save the visualization
fig.write_html('email_clusters_fixed_colors.html')
print("Created fixed visualization: email_clusters_fixed_colors.html")

# Save the data for verification
tsne_df.to_csv('tsne_visualization_fixed.csv', index=False)
print("Saved visualization data to tsne_visualization_fixed.csv")

# Create a validation file showing the mapping
validation_df = pd.DataFrame({
    'cluster_id': list(id_to_name_map.keys()),
    'cluster_name': list(id_to_name_map.values())
})
validation_df['color'] = validation_df['cluster_name'].map(color_mapping)
validation_df.to_csv('cluster_color_mapping.csv', index=False)
print("Saved cluster mapping to cluster_color_mapping.csv")

print("\n===== FIXED VISUALIZATION COMPLETE =====")
