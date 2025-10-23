import pandas as pd
import joblib
import json

# Load the JSON data from file 1
with open('topic_summaries.json', 'r') as f1:
    data1 = json.load(f1)

# Load the JSON data from file 2
with open('topic_summaries2.json', 'r') as f2:
    data2 = json.load(f2)

# Merge the two dictionaries (data2 values override data1 in case of key conflicts)
merged = {**data1, **data2}

# Save the merged result
with open('merged.json', 'w') as outfile:
    json.dump(merged, outfile, indent=4)
