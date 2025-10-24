import json
from pathlib import Path

def merge_topic_summaries():
    # Base directory for topic modeling artifacts
    MODULE_DIR = Path(__file__).resolve().parent

    # Load the JSON data from file 1
    with (MODULE_DIR / 'topic_summaries.json').open('r', encoding='utf-8') as f1:
        data1 = json.load(f1)

    # Load the JSON data from file 2
    with (MODULE_DIR / 'topic_summaries2.json').open('r', encoding='utf-8') as f2:
        data2 = json.load(f2)

    # Merge the two dictionaries (data2 values override data1 in case of key conflicts)
    merged = {**data1, **data2}

    # Save the merged result
    with (MODULE_DIR / 'merged.json').open('w', encoding='utf-8') as outfile:
        json.dump(merged, outfile, ensure_ascii=False, indent=4)
