"""
Colbert RAG implementation for the Okloa project.

This module provides functionality for creating a RAG system using the
RAGAtouille library with ColBERTv2.0 retriever for email data.
"""

import os
import time
# import mailbox
from typing import List, Dict, Any, Tuple
import pickle
# from pathlib import Path
import textwrap
import sys

from ragatouille import RAGPretrainedModel

# import email
# import tempfile
# import shutil
# from datetime import datetime

# import pandas as pd
# import json

# Import RAGAtouille library
RAGATOUILLE_AVAILABLE = True

# try:
#     from ragatouille import RAGPretrainedModel
# except ImportError:
#     print("RAGAtouille not installed. Please install it with 'pip install ragatouille'")
#     RAGATOUILLE_AVAILABLE = False

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


from constants import ACTIVE_PROJECT

# Parse email functionality from the loading module
# from src.data.loading import parse_email_message, load_mbox_file

# def prepare_email_for_rag(email_data: Dict[str, Any]) -> str:
#     """
#     Format an email for indexing in the RAG system.

#     Args:
#         email_data: Dictionary containing parsed email data

#     Returns:
#         Formatted string representation of the email
#     """
#     formatted_email = f"From: {email_data.get('from', '')}\n"
#     formatted_email += f"To: {email_data.get('to', '')}\n"

#     if email_data.get('cc'):
#         formatted_email += f"Cc: {email_data.get('cc', '')}\n"

#     formatted_email += f"Subject: {email_data.get('subject', '')}\n"
#     formatted_email += f"Date: {email_data.get('date', '')}\n"

#     # Add body
#     if email_data.get('body'):
#         formatted_email += f"\n{email_data.get('body', '')}"

#     return formatted_email

# def prepare_email_for_rag(email_row) -> str:
#     """
#     Format an email row from DataFrame for indexing in the RAG system.
    
#     Args:
#         email_row: pandas Series or dict containing email data from get_rag_email_dataset()
    
#     Returns:
#         Formatted string representation of the email
#     """
#     # Handle both pandas Series and dict input
#     if hasattr(email_row, 'get'):
#         get_func = email_row.get
#     else:
#         get_func = lambda key, default='': getattr(email_row, key, default) if hasattr(email_row, key) else default
    
#     formatted_email = f"From: {get_func('from', '')}\n"
    
#     # Add To recipients
#     to_recipients = get_func('to_recipients', '')
#     if to_recipients:
#         formatted_email += f"To: {to_recipients}\n"
    
#     # Add CC recipients if present
#     cc_recipients = get_func('cc_recipients', '')
#     if cc_recipients:
#         formatted_email += f"Cc: {cc_recipients}\n"
    
#     # Add BCC recipients if present
#     bcc_recipients = get_func('bcc_recipients', '')
#     if bcc_recipients:
#         formatted_email += f"Bcc: {bcc_recipients}\n"
    
#     formatted_email += f"Subject: {get_func('subject', '')}\n"
#     formatted_email += f"Date: {get_func('date', '')}\n"
    
#     # Add body with last message extraction
#     body = get_func('body', '')
#     if body:
#         # Extract last message from email thread (basic implementation)
#         last_message = extract_last_message(body)
#         formatted_email += f"\n{last_message}"
    
#     return formatted_email

def prepare_email_for_rag(df) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Format emails from DataFrame for indexing in the RAG system.
    """
    emails_data = []
    
    for index, row in df.iterrows():
        # Format the email content
        formatted_email = f"From: {row.get('from', '')}\n"
        
        # Add recipients
        to_recipients = row.get('to_recipients', '')
        if to_recipients:
            formatted_email += f"To: {to_recipients}\n"
        
        cc_recipients = row.get('cc_recipients', '')
        if cc_recipients:
            formatted_email += f"Cc: {cc_recipients}\n"
        
        bcc_recipients = row.get('bcc_recipients', '')
        if bcc_recipients:
            formatted_email += f"Bcc: {bcc_recipients}\n"
        
        formatted_email += f"Subject: {row.get('subject', '')}\n"
        formatted_email += f"Date: {row.get('date', '')}\n"
        
        # Add body with aggressive truncation
        body = row.get('body', '')
        if body:
            last_message = extract_last_message(body)
            # Truncate to reasonable length (aim for ~300-400 tokens max)
            # Rough estimate: 1 token ≈ 4 characters
            max_chars = 1200  # This should be safe for 512 token limit
            if len(last_message) > max_chars:
                last_message = last_message[:max_chars] + "..."
            formatted_email += f"\n{last_message}"
        
        # Final safety check - truncate entire email if too long
        max_total_chars = 1500  # Conservative limit
        if len(formatted_email) > max_total_chars:
            formatted_email = formatted_email[:max_total_chars] + "..."
        
        # Create metadata dictionary
        metadata = {
            'email_id': row.get('email_id', ''),
            'from': row.get('from', ''),
            'to_recipients': row.get('to_recipients', ''),
            'cc_recipients': row.get('cc_recipients', ''),
            'bcc_recipients': row.get('bcc_recipients', ''),
            'subject': row.get('subject', ''),
            'date': str(row.get('date', '')),
            'original_index': index
        }
        
        emails_data.append((formatted_email, metadata))
    
    return emails_data

def extract_last_message(body: str) -> str:
    """
    Extract the last message from an email body (cuts threading).
    
    Args:
        body: Full email body potentially containing threaded messages
    
    Returns:
        Last message content
    """
    if not body:
        return ""
    
    # Common patterns that indicate start of previous messages
    thread_indicators = [
        "-----Original Message-----",
        "From:",
        "Le ", # French date format
        "On ", # English date format
        "> ", # Quote indicators
        "---",
        "________________________________", # Outlook separator
        "Sent from my iPhone",
        "Sent from my iPad",
        "Get Outlook for"
    ]
    
    lines = body.split('\n')
    last_message_lines = []
    
    for line in lines:
        # Check if this line indicates start of previous message
        line_stripped = line.strip()
        is_thread_start = False
        
        for indicator in thread_indicators:
            if line_stripped.startswith(indicator):
                is_thread_start = True
                break
        
        if is_thread_start:
            break
        
        last_message_lines.append(line)
    
    return '\n'.join(last_message_lines).strip()

# def load_and_prepare_emails(mailbox_paths: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
#     """
#     Load emails from multiple mailbox files and prepare them for RAG.

#     Args:
#         mailbox_paths: List of paths to mailbox files

#     Returns:
#         List of tuples with (formatted_email, metadata)
#     """
#     all_emails = []

#     for mbox_path in mailbox_paths:
#         try:
#             # Process each mbox file
#             mbox = mailbox.mbox(mbox_path)

#             for i, message in enumerate(mbox):
#                 try:
#                     # Parse the email message
#                     email_data = parse_email_message(message)

#                     # Generate a unique ID
#                     email_id = email_data.get("message_id", f"email_{Path(mbox_path).stem}_{i}")

#                     # Format the email for RAG
#                     formatted_email = prepare_email_for_rag(email_data)

#                     # Create metadata for retrieval
#                     metadata = {
#                         "id": email_id,
#                         "from": email_data.get("from", ""),
#                         "to": email_data.get("to", ""),
#                         "subject": email_data.get("subject", ""),
#                         "date": str(email_data.get("date", "")),
#                         "mailbox": Path(mbox_path).parent.name,
#                         "direction": email_data.get("direction", ""),
#                         "has_attachments": email_data.get("has_attachments", False),
#                     }

#                     # Add to the collection
#                     all_emails.append((formatted_email, metadata))

#                 except Exception as e:
#                     print(f"Error processing email: {e}")

#         except Exception as e:
#             print(f"Error loading mailbox {mbox_path}: {e}")

#     return all_emails

def initialize_colbert_rag(emails_data: List[Tuple[str, Dict[str, Any]]], output_dir: str) -> str:
    """
    Initialize the Colbert RAG system with email data.

    Args:
        emails_data: List of tuples with (formatted_email, metadata)
        output_dir: Path to save metadata (actual index is saved by RAGAtouille internally)

    Returns:
        Path to the index directory
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Separate emails and metadata
    email_texts = [email[0] for email in emails_data]
    email_ids = [f"email_{i}" for i in range(len(emails_data))]
    email_metadata = [email[1] for email in emails_data]

    try:
        # Initialize the RAG model with ColBERTv2.0

        print("pretraining")
        rag_model = RAGPretrainedModel.from_pretrained("jinaai/jina-colbert-v2") # jinaai/jina-colbert-v2

        print("past pretrained")

        # Index the email collection
        print(f"Indexing {len(email_texts)} emails...")
        rag_model.index(
            collection=email_texts,
            document_ids=email_ids,
            document_metadatas=email_metadata,
            index_name="emails_index",  # This name is important - we'll use it to access the index
            max_document_length=480,
            split_documents=True
        )

        print("Done indexing!")

        # Save the email metadata mapping for later use
        metadata_path = os.path.join(output_dir, "email_metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump(email_metadata, f)

        return output_dir

    except Exception as e:
        print(f"Error initializing Colbert RAG: {e}")
        raise


# def load_colbert_rag(index_path: str):
#     """
#     Load a previously initialized Colbert RAG model.

#     Args:
#         index_path: Path to the saved index directory (unused in this implementation)

#     Returns:
#         Loaded RAG model
#     """
#     try:
#         # Initialize the RAG model directly - RAGAtouille will automatically use the last created index
#         rag_model = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0", verbose=True)
#         print("Loaded RAG model with index 'emails_index'")
#         return rag_model
#     except Exception as e:
#         print(f"Error loading Colbert RAG model: {e}")
#         raise

# def load_colbert_rag(index_path: str):
#     """
#     Load a previously initialized Colbert RAG model.

#     Args:
#         index_path: Path to the saved index directory (unused in this implementation)

#     Returns:
#         Loaded RAG model
#     """
#     try:
#         rag_model = RAGPretrainedModel.from_index("emails_index")
#         print("Loaded RAG model with index 'emails_index'")
#         return rag_model
#     except Exception as e:
#         print(f"Error loading Colbert RAG model: {e}")
#         raise

def load_colbert_rag(ragatouille_index_path: str):
    try:
        rag_model = RAGPretrainedModel.from_index(ragatouille_index_path)
        print(f"Loaded RAG model with index from: {ragatouille_index_path}")
        return rag_model
    except Exception as e:
        print(f"Error loading Colbert RAG model: {e}")
        raise

def search_with_colbert(query: str, path_to_metadata: str, ragatouille_index_path: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search emails using the Colbert RAG model.

    Args:
        query: Query string
        index_path: Path to the index directory
        top_k: Number of results to return

    Returns:
        List of search results with metadata
    """
    try:
        # Load the RAG model
        rag_model = load_colbert_rag(ragatouille_index_path = ragatouille_index_path, )
        

        # Search for the query
        print(f"Searching for: '{query}'")
        results = rag_model.search(query=query, k=top_k, index_name="emails_index")

        # Make sure we have results
        if results is None or len(results) == 0:
            print("No results found")
            return []

        print(f"Found {len(results)} results")

        # Load the email metadata
        metadata_path = os.path.join(path_to_metadata, "email_metadata.pkl")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "rb") as f:
                    email_metadata = pickle.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
                email_metadata = []
        else:
            print(f"Metadata file not found at {metadata_path}, results will have limited metadata")
            email_metadata = []

        # Enrich results with metadata
        enriched_results = []
        for result in results:
            # Extract index from text_id (format: "email_X_chunk_Y")
            try:
                # DEBUG: Print what we actually got
                print(f"Result structure: {result}")
                print(f"Result type: {type(result)}")
                print(f"Result keys: {result.keys() if hasattr(result, 'keys') else 'No keys method'}")
                
                # Handle different ID formats
                if "_chunk_" in result["text_id"]:
                    email_id = result["text_id"].split("_chunk_")[0]
                    email_index = int(email_id.replace("email_", ""))
                else:
                    email_index = int(result["text_id"].replace("email_", ""))

                # Get metadata if available
                metadata = {}
                if email_index < len(email_metadata):
                    metadata = email_metadata[email_index]

                # Create enriched result
                enriched_result = {
                    "text": result["text"],
                    "text_id": result["text_id"],
                    "score": result["score"],
                    "metadata": metadata
                }

                enriched_results.append(enriched_result)

            except (ValueError, IndexError, KeyError) as e:
                print(f"Error enriching result: {e}")
                # Still include the result without enrichment
                enriched_results.append(result)

        return enriched_results

    except Exception as e:
        print(f"Error searching with Colbert: {e}")
        raise


def get_all_mbox_paths(data_dir: str) -> List[str]:
    """
    Get paths to all mbox files in the data directory.

    Args:
        data_dir: Path to the data directory

    Returns:
        List of paths to mbox files
    """
    mbox_paths = []

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.mbox'):
                mbox_paths.append(os.path.join(root, file))

    return mbox_paths


def format_result_preview(result: Dict[str, Any]) -> str:
    """
    Format a search result for preview display.

    Args:
        result: Search result dictionary with metadata

    Returns:
        Formatted preview string
    """
    metadata = result.get('metadata', {})
    preview = f"**De:** {metadata.get('from', 'Inconnu')}\n"
    preview += f"**À:** {metadata.get('to', 'Inconnu')}\n"
    preview += f"**Sujet:** {metadata.get('subject', 'Pas de sujet')}\n"
    preview += f"**Date:** {metadata.get('date', 'Date inconnue')}\n"

    # Include the text content
    if result.get('text'):
        # Wrap to multiple lines for better readability
        wrapped_text = textwrap.fill(result['text'], width=80)
        preview += f"**Contenu:**\n```\n{wrapped_text}\n```\n"

    # Add relevance score if available
    if 'score' in result:
        preview += f"**Score de pertinence:** {result['score']:.2f}\n"

    return preview


def generate_answer(query: str, results: List[Dict[str, Any]]) -> str:
    """
    Generate an answer based on the search results.

    Args:
        query: User query
        results: Search results from Colbert

    Returns:
        Generated answer
    """
    
    if not results:
        return "Je n'ai pas trouvé d'informations pertinentes dans les archives d'emails pour répondre à votre question."

    # Simple approach to generate a response based on the retrieved information
    answer = "D'après les emails récupérés, voici ce que j'ai trouvé concernant votre question:\n\n"

    for i, result in enumerate(results[:3]):  # Use top 3 results
        metadata = result.get('metadata', {})
        sender = metadata.get('from', 'Expéditeur inconnu')
        subject = metadata.get('subject', 'Pas de sujet')
        date = metadata.get('date', 'Date inconnue')

        answer += f"**Email {i+1}:** De {sender}, sujet \"{subject}\" (le {date})\n"

        # Include a snippet of the content
        if result.get('text'):
            text = result.get('text')
            # Get a relevant excerpt (around 200 characters)
            if len(text) > 200:
                excerpt = text[:200] + "..."
            else:
                excerpt = text
            answer += f"Contenu: \"{excerpt}\"\n\n"



    return answer


def colbert_rag_answer(query: str, path_to_metadata: str, ragatouille_index_path:str, top_k: int = 5) -> Tuple[str, List[str]]:
    """
    Get an answer to a query using Colbert RAG.

    Args:
        query: User query
        index_path: Path to the index directory
        top_k: Number of results to consider

    Returns:
        Tuple of (answer, formatted source previews)
    """

    # Start timer
    start_time = time.time()
    # End timer and print duration

    # Search with Colbert
    results = search_with_colbert(
    query = query,
    path_to_metadata = path_to_metadata,
    ragatouille_index_path = ragatouille_index_path,
    top_k=top_k)

    # Generate answer
    answer = generate_answer(query, results)

    # Format sources for display
    source_previews = [format_result_preview(result) for result in results]

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n🕐 Total answer operation completed in {duration:.2f} seconds")
    
    return answer, source_previews


if __name__ == "__main__":
    # Set path to the index of the active project
    path_to_metadata = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'colbert_indexes')
    ragatouille_index_path = os.path.join(project_root, '.ragatouille', 'colbert', 'indexes', 'emails_index')

    colbert_rag_answer(query = "Quel mail parle d'Olkoa ?", path_to_metadata = path_to_metadata, ragatouille_index_path = ragatouille_index_path)


