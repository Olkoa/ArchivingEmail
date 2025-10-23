import pandas as pd
import json
from bertopic import BERTopic

# Load the DataFrame (if not already loaded)
df = pd.read_csv("bertopic_output.csv")

# Filter out outliers (topic == -1)
df_filtered = df[df['topic'] != -1]

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

except Exception as e:
    print("⚠️ Error while loading topic labels:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
    print("Traceback:")
    traceback.print_exc()

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

import json
import math

# Load sampled documents
def load_sampled_docs(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# Split the topics into two parts
def split_json(docs):
    # Get the list of topics
    topics = list(docs.items())
    mid_index = math.ceil(len(topics) / 2)  # Find the middle index to split the list

    # Split into two parts
    first_half = dict(topics[:mid_index])
    second_half = dict(topics[mid_index:])

    return first_half, second_half

# Save the splitted JSON to files
def save_split_json(first_half, second_half, output_path_1="split_1.json", output_path_2="split_2.json"):
    # Save first half
    with open(output_path_1, "w", encoding="utf-8") as f1:
        json.dump(first_half, f1, ensure_ascii=False, indent=2)
    print(f"✅ First half saved to {output_path_1}")

    # Save second half
    with open(output_path_2, "w", encoding="utf-8") as f2:
        json.dump(second_half, f2, ensure_ascii=False, indent=2)
    print(f"✅ Second half saved to {output_path_2}")

docs = load_sampled_docs("topic_samples_grp.json")

    # Split the topics into two parts
first_half, second_half = split_json(docs)

    # Save the two parts into separate files
save_split_json(first_half, second_half)
