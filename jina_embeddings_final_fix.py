import requests
import json
import os
import time
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from src.data.email_analyzer import EmailAnalyzer

# Load project settings
ACTIVE_PROJECT = "Projet Demo"  # Replace with your actual project ID

# Load data
db_path = os.path.join('data', "Projects", ACTIVE_PROJECT, 'célineETjoel.duckdb')
print(f"Loading data from: {db_path}")
email_analyzer = EmailAnalyzer(db_path)
df = email_analyzer.get_mail_bodies_for_embedding_DataFrame(max_body_chars = 8000)
print(f"DataFrame shape: {df.shape}")

# IMPORTANT: Reset the index to ensure we have a sequential integer index
df = df.reset_index(drop=True)
print("DataFrame index type:", type(df.index))
print("First 5 indices:", df.index[:5].tolist())

# Load environment variables for Jina AI
load_dotenv()
JINA_MODEL_URL = os.getenv("JINA_MODEL_URL")
JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_MODEL_NAME = os.getenv("JINA_MODEL_NAME")

# Set up API request headers
headers = {
    'Content-Type': 'application/json',
    'Authorization': JINA_API_KEY,
}

# Initialize embeddings column with object type to store arrays
df['embeddings'] = None
df['embeddings'] = df['embeddings'].astype('object')  # Important for storing arrays

# Process in batches to avoid the 2048 input limit
BATCH_SIZE = 500  # Smaller batch size
MAX_RETRIES = 5   # Number of retries for rate limit errors
BASE_DELAY = 40   # Initial delay in seconds
MAX_DELAY = 120   # Maximum delay in seconds

# Resume feature - check if output file exists
output_path = os.path.join('data', "Projects", ACTIVE_PROJECT, 'emails_with_embeddings.pkl')
last_processed_idx = -1  # Start from the beginning by default

# Try to load existing progress if the file exists
try:
    if os.path.exists(output_path):
        print(f"Found existing embeddings file. Checking for progress...")
        existing_df = pd.read_pickle(output_path)
        if 'embeddings' in existing_df.columns:
            # Make sure existing_df has a proper index too
            existing_df = existing_df.reset_index(drop=True)
            # Find the last row with a valid embedding
            valid_mask = existing_df['embeddings'].notna()
            if valid_mask.any():
                valid_indices = existing_df.index[valid_mask].tolist()
                last_processed_idx = max(valid_indices)
                print(f"Resuming from index {last_processed_idx + 1} (already processed {last_processed_idx + 1} items)")

                # Copy existing embeddings to our dataframe
                for idx in valid_indices:
                    if idx < len(df):
                        df.iloc[idx, df.columns.get_loc('embeddings')] = existing_df.iloc[idx, existing_df.columns.get_loc('embeddings')]
except Exception as e:
    print(f"Error checking for existing progress: {str(e)}")
    print("Starting from the beginning...")

# Calculate starting batch based on last processed index
start_batch = (last_processed_idx + 1) // BATCH_SIZE
num_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division

# Lists to collect successful embeddings for current session
current_session_count = 0

# Save progress periodically
SAVE_FREQUENCY = 5  # Save after every 5 successful batches

# Track successful batches for periodic saving
successful_batches = 0

# Create a temporary list to store embeddings for each batch
for batch_idx in range(start_batch, num_batches):
    start_idx = batch_idx * BATCH_SIZE
    end_idx = min((batch_idx + 1) * BATCH_SIZE, len(df))

    print(f"Processing batch {batch_idx + 1}/{num_batches} (items {start_idx} to {end_idx-1})")

    # Get slice of dataframe for this batch
    batch_df = df.iloc[start_idx:end_idx].copy()

    # Check which rows need processing
    rows_to_process_mask = batch_df['embeddings'].isna()
    rows_to_process_count = rows_to_process_mask.sum()

    if rows_to_process_count == 0:
        print(f"Skipping batch {batch_idx + 1}/{num_batches} - already processed")
        continue

    print(f"Processing {rows_to_process_count} rows in this batch")

    # Get texts for rows that need processing
    texts_to_process = batch_df.loc[rows_to_process_mask, 'body'].tolist()

    # Get original indices for tracking
    original_indices = batch_df.index[rows_to_process_mask].tolist()

    # Prepare batch data
    batch_data = {
        "model": JINA_MODEL_NAME,
        "task": "separation",
        "late_chunking": True,
        "truncate": True,
        "dimensions": 512,
        "input": texts_to_process,
    }

    # Implement retry logic with exponential backoff
    retry_count = 0
    success = False

    while not success and retry_count < MAX_RETRIES:
        try:
            # Make API request for this batch
            response = requests.post(JINA_MODEL_URL, headers=headers, data=json.dumps(batch_data))
            response_json = response.json()

            # Check for rate limit error
            if 'detail' in response_json and 'rate limit' in response_json['detail'].lower():
                retry_count += 1
                delay = min(BASE_DELAY * (2 ** retry_count), MAX_DELAY)  # Exponential backoff
                print(f"Rate limit hit. Retrying in {delay} seconds (attempt {retry_count}/{MAX_RETRIES})")
                time.sleep(delay)
                continue

            # Check for other errors
            elif 'detail' in response_json:
                print(f"Error in batch {batch_idx + 1}: {response_json['detail']}")
                # For non-rate-limit errors, we'll still delay but mark as failed
                time.sleep(BASE_DELAY)
                break

            # No errors - process the embeddings
            success = True

            # Identify where the embeddings are in the response
            embedding_key = None
            if 'data' in response_json:
                embedding_key = 'data'
            elif 'embeddings' in response_json:
                embedding_key = 'embeddings'
            else:
                print(f"Warning: Could not find embeddings in response. Keys: {list(response_json.keys())}")
                print(f"Response sample: {str(response_json)[:100]}...")
                break

            # Store embeddings in dataframe (carefully)
            embeddings_batch = response_json[embedding_key]

            # Safety check
            if len(embeddings_batch) != len(original_indices):
                print(f"Warning: Got {len(embeddings_batch)} embeddings for {len(original_indices)} inputs")
                # Process only what we can
                process_count = min(len(embeddings_batch), len(original_indices))
            else:
                process_count = len(original_indices)

            # Now properly store the embeddings
            for i in range(process_count):
                idx = original_indices[i]
                embedding = embeddings_batch[i]

                # Store embedding directly using numeric iloc indexing
                df.iat[idx, df.columns.get_loc('embeddings')] = embedding
                current_session_count += 1

            print(f"Successfully processed batch {batch_idx + 1} - stored {process_count} embeddings")
            successful_batches += 1

            # Save progress periodically
            if successful_batches % SAVE_FREQUENCY == 0:
                print(f"Saving intermediate progress ({current_session_count} total new embeddings)...")
                df.to_pickle(output_path)
                print("Progress saved")

            # Add a delay between successful requests to avoid hitting rate limits
            time.sleep(2)  # Small delay between batches

        except Exception as e:
            print(f"Error processing batch {batch_idx + 1}: {str(e)}")
            import traceback
            traceback.print_exc()  # Print full error details for debugging
            time.sleep(BASE_DELAY)  # Wait before retrying or moving to next batch
            break

# Final save
print(f"Processing complete! Saving final results...")
df.to_pickle(output_path)

# Verify how many embeddings we've collected in total
embeddings_count = df['embeddings'].notna().sum()
print(f"Generated {embeddings_count} embeddings out of {len(df)} records")
print(f"Added {current_session_count} new embeddings in this session")
print(f"Results saved to {output_path}")
print("Done!")
