"""
Initialization script for the Colbert RAG system in Okloa.

This module handles the initial setup and loading of the Colbert RAG system,
including processing mbox files and creating the necessary indexes.
"""

import os
import sys
import pandas as pd
import mailbox
from typing import List, Dict, Any, Optional, Tuple
import time

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# from src.data.loading import load_mailboxes
# Check if RAGAtouille is available
# try:
from src.rag.colbert_rag import (
    load_and_prepare_emails,
    initialize_colbert_rag,
    get_all_mbox_paths
)

from src.data.email_analyzer import EmailAnalyzer

from constants import ACTIVE_PROJECT



# except ImportError:
#     RAGATOUILLE_AVAILABLE = False
#     def load_and_prepare_emails(*args, **kwargs):
#         raise ImportError("RAGAtouille not installed")

#     def initialize_colbert_rag(*args, **kwargs):
#         raise ImportError("RAGAtouille not installed")

#     def get_all_mbox_paths(*args, **kwargs):
#         raise ImportError("RAGAtouille not installed")


def initialize_colbert_rag_system(
    emails_df: Optional[pd.DataFrame] = None,
    project_root: Optional[str] = None,
    force_rebuild: bool = False,
    test_mode: bool = False,
) -> str:
    """
    Initialize the Colbert RAG system by processing emails and creating the index.

    Args:
        emails_df: DataFrame containing email data (if None, all mailboxes will be loaded)
        project_root: Project root directory (if None, auto-detect)
        force_rebuild: Whether to force rebuilding the index even if it exists

    Returns:
        Path to the index directory
    """
    # Check if RAGAtouille is available
    # if not RAGATOUILLE_AVAILABLE:
    #     raise ImportError(
    #         "RAGAtouille not installed. Please install it with 'pip install ragatouille'"
    #     )
    # Determine project root if not provided
    if project_root is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    # Set index directory - using a different name to avoid conflicts
    index_dir = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'colbert_indexes')

    # Check if index already exists
    # The actual index is stored by RAGAtouille in the user's home directory
    # We just need to check if we've already saved metadata
    index_exists = os.path.exists(os.path.join(index_dir, "email_metadata.pkl"))

    # Create index if it doesn't exist or if forced rebuild
    if not index_exists or force_rebuild:
        os.makedirs(index_dir, exist_ok=True)

        start_time = time.time()
        print(f"Building Colbert RAG index (this may take a while)...")

        # Get paths to all mbox files
        base_dir = os.path.join(project_root, 'data', 'raw')
        mbox_paths = get_all_mbox_paths(base_dir)

        if not mbox_paths:
            raise ValueError(f"No mbox files found in {base_dir}")

        print(f"Found {len(mbox_paths)} mbox files")

        # if test_mode:
        #     # Load and prepare emails from all mbox files
        #     colbert_df = EmailAnalyzer.get_mail_bodies_for_embedding_DataFrame(max_body_chars = 8000, limit = 3)
        # else:
        #     colbert_df = EmailAnalyzer.get_mail_bodies_for_embedding_DataFrame(max_body_chars = 8000, limit = 10)

        emails_data = load_and_prepare_emails(mbox_paths)

        print("mails loaded")

        # print(emails_data)

        # print(f"Loaded {colbert_df.shape[0]} emails for indexing\nStarting Indexing...")

        # Initialize the Colbert RAG system
        # initialize_colbert_rag(colbert_df, index_dir)
        initialize_colbert_rag(emails_data, index_dir)


        end_time = time.time()
        print(f"Colbert RAG index built successfully at {index_dir}")
        print(f"Indexing completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"Using existing Colbert RAG index")

    return index_dir

if __name__ == "__main__":
    # Test initialization

    # Initialize Colbert RAG system
    index_dir = initialize_colbert_rag_system(project_root=project_root, force_rebuild=True, test_mode=True)

    print(f"Colbert RAG system initialized with index at {index_dir}")
