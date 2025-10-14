import pandas as pd
import json
from pathlib import Path
from tqdm import tqdm

def chunk_text(text, chunk_size=200, overlap=20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


base_dir = Path(__file__).resolve().parents[2]

json_path = base_dir /"src" / "data" / "processed" / "celine_guyon" / "all_cleaned_mails.json"

with open(json_path, "r", encoding="utf-8") as f:
    mails = json.load(f)

rows = []
for mail in tqdm(mails, desc="mail"):
    body = mail.get("body", "")
    chunks = chunk_text(body, chunk_size=200, overlap=20)

    for i, chunk in enumerate(chunks):
        rows.append({
            "subject": mail.get("subject", ""),
            "body": chunk,                      # ici un chunk = une ligne
            "chunk_id": i,                      # numéro du chunk dans le mail
            "sender": ";".join([addr[1] for addr in mail.get("from", [])]) if isinstance(mail.get("from"), list) else str(mail.get("from")),
            "recipient": ";".join([addr[1] for addr in mail.get("to", [])]) if isinstance(mail.get("to"), list) else str(mail.get("to")),
            "date": mail.get("date"),
            "file": mail.get("file"),
            "folder": mail.get("folder"),
        })

emails_df = pd.DataFrame(rows)

print(emails_df.head())
print(emails_df.columns)
print(f"Nombre total de chunks : {len(emails_df)}")
print(emails_df.columns)


# dossier de sortie : processed/rag 
output_dir = base_dir / "data" / "processed" / "rag" 
output_dir.mkdir(parents=True, exist_ok=True) # sauvegarde en CSV et Parquet 
csv_path = output_dir / "chunked_emails.csv"
emails_df.to_csv(csv_path, index=False, encoding="utf-8")