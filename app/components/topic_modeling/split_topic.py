import json
import math
import traceback
from collections import defaultdict
from pathlib import Path

import pandas as pd
from bertopic import BERTopic


def split_topics():
    """Split topic samples into two JSON files for processing."""
    MODULE_DIR = Path(__file__).resolve().parent

    # Load the DataFrame (if not already loaded)
    df = pd.read_csv(MODULE_DIR / "bertopic_output.csv")

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
        topic_model = BERTopic.load(str(MODULE_DIR / "bertopic_model_fr"))
        topic_labels = topic_model.get_topic_info().set_index("Topic")["Name"].to_dict()
        samples["topic_label"] = samples["topic"].map(topic_labels)

    except Exception as e:
        print("⚠️ Error while loading topic labels:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {e}")
        print("Traceback:")
        traceback.print_exc()

    # Save to JSON
    samples_path = MODULE_DIR / "topic_samples.json"
    samples.to_json(samples_path, orient="records", force_ascii=False, indent=2)

    # Load your data (replace 'your_data' with your actual data variable or file load)
    with samples_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    # Group texts by topic
    grouped = defaultdict(list)
    for item in data:
        topic_key = f"topic_{item['topic']}"
        grouped[topic_key].append(item['text'])

    # Convert defaultdict to regular dict and save
    grouped_path = MODULE_DIR / 'topic_samples_grp.json'
    with grouped_path.open('w', encoding='utf-8') as f:
        json.dump(dict(grouped), f, indent=2, ensure_ascii=False)

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
    def save_split_json(first_half, second_half, output_path_1, output_path_2):
        # Save first half
        with open(output_path_1, "w", encoding="utf-8") as f1:
            json.dump(first_half, f1, ensure_ascii=False, indent=2)
        print(f"✅ First half saved to {output_path_1}")

        # Save second half
        with open(output_path_2, "w", encoding="utf-8") as f2:
            json.dump(second_half, f2, ensure_ascii=False, indent=2)
        print(f"✅ Second half saved to {output_path_2}")

    docs = load_sampled_docs(grouped_path)

    # Split the topics into two parts
    first_half, second_half = split_json(docs)

    split_1_path = MODULE_DIR / "split_1.json"
    split_2_path = MODULE_DIR / "split_2.json"

    # Save the two parts into separate files
    save_split_json(first_half, second_half, split_1_path, split_2_path)
