import matplotlib.pyplot as plt
import pandas as pd
df3 = pd.read_pickle("scores_df.pkl")

# Assuming your DataFrame is called df_scores and is already sorted by index
plt.figure(figsize=(14, 6))
plt.plot(df3.index, df3['score'], marker='o', linestyle='-')

plt.title('Topic Scores (Stock Chart Style)')
plt.xlabel('Topic Number')
plt.ylabel('Score')
plt.grid(True)

# Optional: show only some x-ticks to avoid clutter
plt.xticks(ticks=range(0, len(df3), 10))

plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt
import pandas as pd

# Sort the DataFrame by score (descending if you want highest on the left)
df_sorted = df3.sort_values(by='score', ascending=False).reset_index(drop=True)

# Plot
plt.figure(figsize=(14, 6))
plt.plot(df_sorted['score'], marker='o', linestyle='-')

plt.title('Topic Scores Sorted (Stock Chart Style)')
plt.xlabel('Ranked Topics (by Score)')
plt.ylabel('Score')
plt.grid(True)

plt.tight_layout()
plt.show()
