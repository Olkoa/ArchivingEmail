import requests
import json
import os
import time
import re
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from src.data.email_analyzer import EmailAnalyzer
import html
import unicodedata

def process_embeddings(batch_size=60, batch_delay=61, sample_mode=False):
    """
    Process email data and generate embeddings using Jina AI.

    Parameters:
    - batch_size: Number of emails to process in each batch (default: 60)
    - batch_delay: Seconds to wait between batches (default: 61)
    - sample_mode: If True, only process up to 10 batches for testing (default: False)

    Returns:
    - DataFrame with embeddings and path where it was saved
    """
    # Load project settings
    ACTIVE_PROJECT = "Projet Demo"  # Replace with your actual project ID

    # Load data
    db_path = os.path.join('data', "Projects", ACTIVE_PROJECT, 'célineETjoel.duckdb')
    print(f"Loading data from: {db_path}")
    email_analyzer = EmailAnalyzer(db_path)
    df = email_analyzer.get_mail_bodies_for_embedding_DataFrame(max_body_chars = 8000)
    print(f"DataFrame shape before preprocessing: {df.shape}")

    # IMPORTANT: Reset the index to ensure we have a sequential integer index
    df = df.reset_index(drop=True)
    print("DataFrame index type:", type(df.index))
    print("First 5 indices:", df.index[:5].tolist())

    # ============================================================================
    # TEXT PREPROCESSING FUNCTIONS
    # ============================================================================

    def clean_text_format(text):
        """Fix format issues with email text"""
        if pd.isna(text) or not isinstance(text, str):
            return ""

        # Decode HTML entities (like &nbsp;)
        text = html.unescape(text)

        # Normalize Unicode (convert different forms to standard form)
        text = unicodedata.normalize('NFKC', text)

        # Replace problematic non-breaking spaces with regular spaces
        text = text.replace('\xa0', ' ')

        # Convert multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)

        # Remove extra line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        return text.strip()

    def remove_nested_conversations(text):
        """Remove nested forwarded/replied email content"""
        if pd.isna(text) or not isinstance(text, str):
            return ""

        # Common email forwarding/reply patterns
        patterns = [
            r'-----Original Message-----.*',
            r'From:.*?Sent:.*?To:.*?Subject:.*?',
            r'De\s*:.*?Envoyé\s*:.*?À\s*:.*?',  # French version
            r'Von:.*?Gesendet:.*?An:.*?Betreff:.*?',  # German version
            r'On.*wrote:.*',
            r'Le.*a écrit :.*',  # French version
            r'>.*',  # Quoted text in replies
        ]

        # Try to find the first occurrence of any pattern
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                # Keep only the text before the nested content
                text = text[:match.start()].strip()

        return text

    def cut_at_sentence_end(text, max_length=8000):
        """Truncate text at the end of the last complete sentence within max_length"""
        if pd.isna(text) or not isinstance(text, str):
            return ""

        if len(text) <= max_length:
            return text

        # Cut at max_length
        truncated = text[:max_length]

        # Find the last sentence boundary (., !, ?)
        sentence_end_match = re.search(r'[.!?]["\'\)\]]?\s*$', truncated)
        if not sentence_end_match:
            # If no sentence boundary is found, try to find the last one
            sentence_ends = list(re.finditer(r'[.!?]["\'\)\]]?\s+', truncated))
            if sentence_ends:
                # Use the position of the last found sentence end
                last_end = sentence_ends[-1]
                return truncated[:last_end.end()].strip()

        # If there are no sentence boundaries at all, just return the truncated text
        return truncated.strip()

    # ============================================================================
    # PREPROCESS THE DATAFRAME
    # ============================================================================

    print("Preprocessing email texts...")

    # Apply all text preprocessing functions
    df['original_body'] = df['body'].copy()  # Keep original for reference
    df['body'] = df['body'].apply(clean_text_format)
    df['body'] = df['body'].apply(remove_nested_conversations)
    df['body'] = df['body'].apply(cut_at_sentence_end)

    # Remove empty texts after preprocessing
    non_empty_mask = df['body'].astype(str).str.strip().str.len() > 0
    df = df[non_empty_mask].reset_index(drop=True)

    print(f"DataFrame shape after preprocessing: {df.shape}")

    # ============================================================================
    # EMBEDDING GENERATION CODE
    # ============================================================================

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

    # Process in batches with more conservative rate limits
    BATCH_SIZE = batch_size
    BATCH_DELAY = batch_delay
    MAX_RETRIES = 5   # Number of retries for rate limit errors
    BASE_DELAY = 40   # Initial delay in seconds
    MAX_DELAY = 120   # Maximum delay in seconds

    # Determine output file name based on mode
    file_suffix = "_sample" if sample_mode else "_improved"
    output_path = os.path.join('data', "Projects", ACTIVE_PROJECT, f'emails_with_embeddings{file_suffix}.pkl')
    print(f"Will save results to {output_path}")

    # Calculate batches
    num_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division

    # If in sample mode, limit to 10 batches
    if sample_mode and num_batches > 10:
        print(f"Sample mode enabled: Will process only 5 batches instead of {num_batches}")
        num_batches = 10

    print(f"Will process {min(num_batches * BATCH_SIZE, len(df))} emails in {num_batches} batches of up to {BATCH_SIZE} emails each")

    # Lists to collect successful embeddings for current session
    current_session_count = 0

    # Save progress periodically
    SAVE_FREQUENCY = 2  # Save more frequently (after every 2 successful batches)

    # Track successful batches for periodic saving
    successful_batches = 0

    # For debugging
    print(f"Will start processing from batch 1 to {num_batches}")

    # Create a temporary list to store embeddings for each batch
    for batch_idx in range(0, num_batches):
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min((batch_idx + 1) * BATCH_SIZE, len(df))

        print(f"Processing batch {batch_idx + 1}/{num_batches} (items {start_idx} to {end_idx-1})")

        # Get slice of dataframe for this batch
        batch_df = df.iloc[start_idx:end_idx].copy()

        # Get all rows in this batch (no need to check for existing embeddings in new file)
        texts_to_process = batch_df['body'].tolist()
        original_indices = batch_df.index.tolist()

        print(f"Processing {len(texts_to_process)} rows in this batch")

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

                    # Store the embedding using index location
                    df.iat[idx, df.columns.get_loc('embeddings')] = embedding
                    current_session_count += 1

                print(f"Successfully processed batch {batch_idx + 1} - stored {process_count} embeddings")
                successful_batches += 1

                # Save progress periodically
                if successful_batches % SAVE_FREQUENCY == 0:
                    print(f"Saving intermediate progress ({current_session_count} total new embeddings)...")
                    df.to_pickle(output_path)
                    print("Progress saved")

                # Add the requested delay between batches to avoid rate limits
                if batch_idx < num_batches - 1:  # Skip delay after the last batch
                    print(f"Waiting {BATCH_DELAY} seconds before processing next batch...")
                    time.sleep(BATCH_DELAY)

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

    return df, output_path

if __name__ == "__main__":
    # You can call the function with different parameters
    import argparse

    parser = argparse.ArgumentParser(description='Process emails and generate embeddings.')
    parser.add_argument('--batch-size', type=int, default=70, help='Number of emails per batch')
    parser.add_argument('--batch-delay', type=int, default=30, help='Seconds to wait between batches')
    parser.add_argument('--sample', action='store_true', help='Process only 10 batches for testing')

    args = parser.parse_args()

    process_embeddings(
        batch_size=args.batch_size,
        batch_delay=args.batch_delay,
        sample_mode=args.sample
    )
