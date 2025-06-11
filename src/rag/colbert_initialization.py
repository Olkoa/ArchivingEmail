"""
Initialization script for the Colbert RAG system in Okloa.

This module handles the initial setup and loading of the Colbert RAG system,
including processing mbox files and creating the necessary indexes.
"""

import os
import sys
import pandas as pd
from typing import Optional
import time

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


from src.rag.colbert_rag import (
    initialize_colbert_rag,
    prepare_email_for_rag
    # load_and_prepare_emails,
    # get_all_mbox_paths
)

from src.data.email_analyzer import EmailAnalyzer

from constants import ACTIVE_PROJECT

# from src.data.loading import load_mailboxes
# Check if RAGAtouille is available
# try:

# except ImportError:
#     RAGATOUILLE_AVAILABLE = False
#     def load_and_prepare_emails(*args, **kwargs):
#         raise ImportError("RAGAtouille not installed")

#     def initialize_colbert_rag(*args, **kwargs):
#         raise ImportError("RAGAtouille not installed")

#     def get_all_mbox_paths(*args, **kwargs):
#         raise ImportError("RAGAtouille not installed")


def initialize_colbert_rag_system(
    ids_series: Optional[pd.DataFrame] = None,
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
        print("Building Colbert RAG index (this may take a while)...")

        # Get paths to all mbox files
        # base_dir = os.path.join(project_root, 'data', 'raw')
        # mbox_paths = get_all_mbox_paths(base_dir)
        # if not mbox_paths:
        #     raise ValueError(f"No mbox files found in {base_dir}")
        # print(f"Found {len(mbox_paths)} mbox files")

        db_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, f"{ACTIVE_PROJECT}.duckdb")
        email_analyzer = EmailAnalyzer(db_path)

        if test_mode:
            # Load and prepare emails from all mbox files
            colbert_df = email_analyzer.get_rag_email_dataset(limit = 100)
        else:
            colbert_df = email_analyzer.get_rag_email_dataset(limit = 500000)

        # emails_data = load_and_prepare_emails(mbox_paths)

        # Faire cette fonction ensuite (df avec mail ID, puis dans l'ordre
        # expediteur - Destinataire - date - sujet - body cut au dernier message)
        # emails_data = prepare_mails_for_rag()
        print(colbert_df.columns)
        print(colbert_df.shape[0])
        # Prepare for RAG (returns List[Tuple[str, Dict[str, Any]]])
        emails_data = prepare_email_for_rag(colbert_df)
        print("mails ready")

        print("mails ready")

        # print(emails_data)

        # print(f"Loaded {colbert_df.shape[0]} emails for indexing\nStarting Indexing...")

        # Initialize the Colbert RAG system
        # initialize_colbert_rag(colbert_df, index_dir)
        initialize_colbert_rag(emails_data, index_dir)

        end_time = time.time()
        print(f"Colbert RAG index built successfully at {index_dir}")
        print(f"Indexing completed in {end_time - start_time:.2f} seconds")
    else:
        print("Using existing Colbert RAG index")

    return index_dir

if __name__ == "__main__":
    # Test initialization

    # Initialize Colbert RAG system
    index_dir = initialize_colbert_rag_system(project_root=project_root, force_rebuild=True, test_mode=True)

    print(f"Colbert RAG system initialized with index at {index_dir}")
