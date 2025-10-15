import pandas as pd

csv_path = "src/data/processed/clustering/topic/chunked_emails.csv"
df = pd.read_csv(csv_path)

nb_total = len(df)
nb_vides = df['body'].isna().sum() + (df['body'].str.strip() == "").sum()

print(f"Total chunks : {nb_total}")
print(f"Chunks vides (NaN ou blancs) : {nb_vides}")
