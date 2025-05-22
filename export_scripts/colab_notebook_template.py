"""
Google Colab notebook code to load and use your exported data.

Upload this as a .ipynb or copy-paste the cells.
"""

# Cell 1: Install dependencies
"""
!pip install ragatouille
!pip install pandas pyarrow
"""

# Cell 2: Upload and load data
"""
from google.colab import files
import pandas as pd
import os

# Upload your parquet file
print("Please upload your rag_emails_for_colab.parquet file:")
uploaded = files.upload()

# Load the data
parquet_file = list(uploaded.keys())[0]
df = pd.read_parquet(parquet_file)

print(f"✅ Loaded {len(df):,} emails")
print(f"📊 Columns: {list(df.columns)}")
print(f"🔍 Sample:")
print(df.head())
"""

# Cell 3: Prepare for RAG (same function as your local code)
"""
def prepare_email_for_rag(df):
    emails_data = []
    
    for index, row in df.iterrows():
        # Format the email content (same as your local code)
        formatted_email = f"From: {row.get('from', '')}\\n"
        
        to_recipients = row.get('to_recipients', '')
        if to_recipients:
            formatted_email += f"To: {to_recipients}\\n"
        
        cc_recipients = row.get('cc_recipients', '')
        if cc_recipients:
            formatted_email += f"Cc: {cc_recipients}\\n"
        
        formatted_email += f"Subject: {row.get('subject', '')}\\n"
        formatted_email += f"Date: {row.get('date', '')}\\n"
        
        body = row.get('body', '')
        if body:
            # Truncate for safety
            max_chars = 1200
            if len(body) > max_chars:
                body = body[:max_chars] + "..."
            formatted_email += f"\\n{body}"
        
        metadata = {
            'email_id': row.get('email_id', ''),
            'from': row.get('from', ''),
            'subject': row.get('subject', ''),
            'date': str(row.get('date', '')),
            'original_index': index
        }
        
        emails_data.append((formatted_email, metadata))
    
    return emails_data

# Prepare data
emails_data = prepare_email_for_rag(df)
print(f"✅ Prepared {len(emails_data)} emails for indexing")
"""

# Cell 4: Create RAG index with GPU acceleration
"""
import time
from ragatouille import RAGPretrainedModel

# Use GPU if available
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔥 Using device: {device}")

# Initialize model
start_time = time.time()
rag_model = RAGPretrainedModel.from_pretrained("jinaai/jina-colbert-v2")

# Prepare texts and metadata
email_texts = [email[0] for email in emails_data]
email_ids = [f"email_{i}" for i in range(len(emails_data))]
email_metadata = [email[1] for email in emails_data]

print(f"🔄 Starting indexing of {len(email_texts)} emails...")

# Index with GPU acceleration
rag_model.index(
    collection=email_texts,
    document_ids=email_ids,
    document_metadatas=email_metadata,
    index_name="colab_emails_index",
    max_document_length=480,
    split_documents=True
)

end_time = time.time()
print(f"🎉 Indexing completed in {end_time - start_time:.2f} seconds")
"""

# Cell 5: Test search
"""
# Test search
query = "Quel mail parle d'Olkoa ?"

start_time = time.time()
results = rag_model.search(query=query, k=5, index_name="colab_emails_index")
end_time = time.time()

print(f"🔍 Search completed in {end_time - start_time:.4f} seconds")
print(f"📊 Found {len(results)} results")

for i, result in enumerate(results[:3]):
    print(f"\\n--- Result {i+1} ---")
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text'][:200]}...")
"""
