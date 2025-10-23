import joblib
import matplotlib.pyplot as plt
import umap
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# Load saved embeddings and texts
df = pd.read_csv("bertopic_output.csv")
embeddings = joblib.load("embeddings_fr.pkl")
texts = joblib.load("texts_fr.pkl")  # if saved earlier

reducer = umap.UMAP(n_components=2, random_state=42)
embeddings_2d = reducer.fit_transform(embeddings)

tsne = TSNE(n_components=2, random_state=42)
reduced = tsne.fit_transform(embeddings)

plt.figure(figsize=(12, 8))
sns.scatterplot(
    x=reduced[:, 0],
    y=reduced[:, 1],
    hue=df["topic"].astype(str),  # Ensure it's treated as categorical
    palette="tab20",
    legend="full",
    s=30
)
plt.title("Emails Colored by Topic")
plt.show()



# Load model
from bertopic import BERTopic
topic_model = BERTopic.load("bertopic_model_fr")

# Get mapping from topic ID to representative label (top words)
topic_labels = {
    topic: ", ".join([word for word, _ in topic_model.get_topic(topic)[:3]])  # top 3 words
    for topic in df["topic"].unique() if topic != -1
}
topic_labels[-1] = "Outlier"

# Replace numeric topic IDs with string labels for plotting
df["topic_label"] = df["topic"].map(topic_labels)

# Plot with topic labels
plt.figure(figsize=(12, 8))
sns.scatterplot(
    x=reduced[:, 0],
    y=reduced[:, 1],
    hue=df["topic_label"],
    palette="tab20",
    legend="full",
    s=30
)
plt.title("Emails Colored by Topic Label")
plt.show()


df = pd.read_csv("bertopic_output.csv")
print(df["topic"].value_counts())

print(df["topic"])

# Load model
import joblib
from bertopic import BERTopic
from sklearn.manifold import TSNE

import matplotlib.pyplot as plt
import seaborn as sns

topic_model = BERTopic.load("bertopic_model_fr")
df = pd.read_csv("bertopic_output.csv")
embeddings = joblib.load("embeddings_fr.pkl")

# Get mapping from topic ID to representative label (top words)
topic_labels = {
    topic: ", ".join([word for word, _ in topic_model.get_topic(topic)])  # top 3 words
    for topic in df["topic"].unique() if topic != -1
}
topic_labels[-1] = "Outlier"
# Reduce embeddings to 2D
tsne = TSNE(n_components=2, random_state=42)
reduced = tsne.fit_transform(embeddings)
# Replace numeric topic IDs with string labels for plotting
df["topic_label"] = df["topic"].map(topic_labels)

# Plot with topic labels
plt.figure(figsize=(12, 8))
sns.scatterplot(
    x=reduced[:, 0],
    y=reduced[:, 1],
    hue=df["topic_label"],
    palette="tab20",
    legend="full",
    s=30
)
plt.title("Emails Colored by Topic Label")
# Explicitly remove legend
plt.legend([],[], frameon=False)
plt.savefig("topic_scatter.png", dpi=300, bbox_inches='tight')  # <- must be before plt.close()

plt.show()

topic_model.get_topic_info()
# Get topic info DataFrame
topic_info = topic_model.get_topic_info()

# Build a dictionary mapping Topic ID → Name
id_to_name = dict(zip(topic_info["Topic"], topic_info["Name"]))

# Map the topic ID column in df to the topic name
df["topic_name"] = df["topic"].map(id_to_name)
print(df)
df22=df.copy()
df22 = df22.drop(columns=['probability', 'topic_name'])
import pandas as pd
import json



# Filter out outliers (topic == -1)
df_filtered = df22[df22['topic'] != -1]

# Sample 10 documents per topic
samples = (
    df_filtered
    .groupby('topic')
    .apply(lambda x: x.sample(n=min(10, len(x)), random_state=42))
    .reset_index(drop=True)
)

# Optional: Add topic label if you still have the model
try:
    topic_model = BERTopic.load("bertopic_model_fr")
    topic_labels = topic_model.get_topic_info().set_index("Topic")["Name"].to_dict()
    samples["topic_label"] = samples["topic"].map(topic_labels)
except:
    print("Could not load topic labels. Skipping that part.")

# Save to JSON
samples.to_json("topic_samples.json", orient="records", force_ascii=False, indent=2)

import json
from collections import defaultdict

# Load your data (replace 'your_data' with your actual data variable or file load)
with open('topic_samples.json', 'r') as f:
    data = json.load(f)

# Group texts by topic
grouped = defaultdict(list)
for item in data:
    topic_key = f"topic_{item['topic']}"
    grouped[topic_key].append(item['text'])

# Convert defaultdict to regular dict and save
with open('topic_samples_grp.json', 'w') as f:
    json.dump(dict(grouped), f, indent=2, ensure_ascii=False)

print(df22)
# Load model
import joblib
from bertopic import BERTopic
from sklearn.manifold import TSNE

import matplotlib.pyplot as plt
import seaborn as sns

topic_model = BERTopic.load("bertopic_model_fr")
df = pd.read_csv("bertopic_output.csv")
embeddings = joblib.load("embeddings_fr.pkl")

# Get mapping from topic ID to representative label (top words)
topic_labels = {
    topic: ", ".join([word for word, _ in topic_model.get_topic(topic)])  # top 3 words
    for topic in df["topic"].unique() if topic != -1
}
topic_labels[-1] = "Outlier"
# Reduce embeddings to 2D
tsne = TSNE(n_components=2, random_state=42)
reduced = tsne.fit_transform(embeddings)
# Replace numeric topic IDs with string labels for plotting
df["topic_label"] = df["topic"].map(topic_labels)

# Plot with topic labels
plt.figure(figsize=(12, 8))
sns.scatterplot(
    x=reduced[:, 0],
    y=reduced[:, 1],
    hue=df["topic_label"],
    palette="tab20",
    legend="full",
    s=30
)
plt.title("Emails Colored by Topic Label")
# Explicitly remove legend
plt.legend([],[], frameon=False)
plt.savefig("topic_scatter.png", dpi=300, bbox_inches='tight')  # <- must be before plt.close()

plt.show()

import joblib
import pandas as pd
from bertopic import BERTopic
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns

# Load model and data
topic_model = BERTopic.load("bertopic_model_fr")
df = pd.read_csv("bertopic_output.csv")
embeddings = joblib.load("embeddings_fr.pkl")

# Drop outliers
mask = df["topic"] != -1
df_filtered = df[mask].reset_index(drop=True)
embeddings_filtered = embeddings[mask]

# Get topic labels (top 3 words per topic)
topic_labels = {
    topic: ", ".join([word for word, _ in topic_model.get_topic(topic)])
    for topic in df_filtered["topic"].unique()
}
topic_labels[-1] = "Outlier"
df_filtered["topic_label"] = df_filtered["topic"].map(topic_labels)

# Reduce embeddings to 2D
tsne = TSNE(n_components=2, random_state=42)
reduced = tsne.fit_transform(embeddings_filtered)

# Plot with topic labels, no legend
plt.figure(figsize=(12, 8))
sns.scatterplot(
    x=reduced[:, 0],
    y=reduced[:, 1],
    hue=df_filtered["topic_label"],
    palette="tab20",
    legend=False,
    s=30
)
plt.title("Emails Colored by Topic Label (Outliers Removed)")
plt.savefig("topic_scatter_no_outliers.png", dpi=300, bbox_inches='tight')
plt.show()
topic_df = pd.DataFrame([
    {"topic_id": topic, "label": label}
    for topic, label in topic_labels.items()
])
topic_df.to_csv("topic_labels.csv", index=False)

topic_model.get_topic_info()
# Get topic info DataFrame
topic_info = topic_model.get_topic_info()

# Build a dictionary mapping Topic ID → Name
id_to_name = dict(zip(topic_info["Topic"], topic_info["Name"]))

# Map the topic ID column in df to the topic name
df["topic_name"] = df["topic"].map(id_to_name)
df["topic_label"] = df["topic"].map(topic_labels)
print('******************')
print(df)
df.to_csv("bertopic_output.csv", index=False)