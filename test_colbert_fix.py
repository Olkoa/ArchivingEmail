"""
Test script to verify the ColBERT RAG fixes
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.rag.colbert_rag import colbert_rag_answer
from constants import ACTIVE_PROJECT

def test_colbert_rag():
    """Test the ColBERT RAG functionality with our fixes."""
    print("Testing ColBERT RAG functionality...")
    
    # Set paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    path_to_metadata = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'colbert_indexes')
    ragatouille_index_path = os.path.join(project_root, '.ragatouille', 'colbert', 'indexes', f"{ACTIVE_PROJECT}_emails_index")
    
    print(f"Metadata path: {path_to_metadata}")
    print(f"Index path: {ragatouille_index_path}")
    print(f"Active project: {ACTIVE_PROJECT}")
    
    # Check if paths exist
    if not os.path.exists(path_to_metadata):
        print(f"WARNING: Metadata path does not exist: {path_to_metadata}")
    
    if not os.path.exists(ragatouille_index_path):
        print(f"WARNING: Index path does not exist: {ragatouille_index_path}")
    
    try:
        # Test the search functionality
        query = "Quel mail parle d'Olkoa ?"
        print(f"\nTesting query: {query}")
        
        answer, source_previews = colbert_rag_answer(
            query=query,
            path_to_metadata=path_to_metadata,
            ragatouille_index_path=ragatouille_index_path,
            top_k=3
        )
        
        print(f"\nAnswer: {answer}")
        print(f"\nNumber of source previews: {len(source_previews)}")
        
        for i, preview in enumerate(source_previews):
            print(f"\n--- Source {i+1} ---")
            print(preview)
            
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_colbert_rag()
