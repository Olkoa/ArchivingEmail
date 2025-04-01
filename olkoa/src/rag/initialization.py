"""
Initialization script for the Okloa RAG system.

This script builds the initial index from email data for the RAG system.
"""

import os
import pandas as pd
from typing import Optional

from .indexing import create_email_index


def initialize_rag_system(
    emails_df: pd.DataFrame,
    project_root: Optional[str] = None,
    force_rebuild: bool = False
) -> str:
    """
    Initialize the RAG system by creating necessary indexes.
    
    Args:
        emails_df: DataFrame containing email data
        project_root: Project root directory (if None, auto-detect)
        force_rebuild: Whether to force rebuilding the index even if it exists
        
    Returns:
        Path to the index directory
    """
    # Determine project root if not provided
    if project_root is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    
    # Set index directory
    index_dir = os.path.join(project_root, 'data', 'processed', 'index')
    
    # Check if index already exists
    index_exists = os.path.exists(os.path.join(index_dir, 'faiss_index.bin'))
    
    # Create index if it doesn't exist or if forced rebuild
    if not index_exists or force_rebuild:
        os.makedirs(os.path.dirname(index_dir), exist_ok=True)
        
        # Create index
        print(f"Building email index (this may take a while)...")
        create_email_index(emails_df, index_dir)
        print(f"Index built successfully at {index_dir}")
    else:
        print(f"Using existing index at {index_dir}")
    
    return index_dir


if __name__ == "__main__":
    # Test initialization
    import os
    from src.data.loading import load_mailboxes
    
    # Load sample data
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    base_dir = os.path.join(project_root, 'data', 'raw')
    emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"], base_dir=base_dir)
    
    # Initialize RAG system
    index_dir = initialize_rag_system(emails_df, project_root, force_rebuild=True)
    
    print(f"RAG system initialized with index at {index_dir}")
