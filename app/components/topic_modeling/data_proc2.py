import pandas as pd
import joblib

df4 = pd.read_pickle("df2_with_embeddings.pkl")
df3 = pd.read_pickle("scores_df.pkl")
topic_kmedoids_results = joblib.load("topic_kmedoids_results_or.pkl")
df4['score'] = df4['topic'].map(df3['score'])
print(df4)
medoid_dict= topic_kmedoids_results
# Convert to a dictionary mapping topic → medoid_index
topic_to_medoid = {topic: v['original_medoid_indices'][0] for topic, v in medoid_dict.items()}
# Add medoid index as a new column
df4['medoid_index'] = df4['topic'].map(topic_to_medoid)
print('****************')
print(df4)
df4.to_pickle("df4_with_embeddings.pkl")
