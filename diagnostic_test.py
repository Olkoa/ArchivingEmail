"""
Simple diagnostic script to understand the RAGAtouille result format
"""

import os
import sys

# Add project to path
sys.path.append('C:\\Users\\julie\\Lab_IA_Project\\olkoa')

try:
    from constants import ACTIVE_PROJECT
    print(f"Active project: {ACTIVE_PROJECT}")
    
    # Try to import and test RAGAtouille
    from ragatouille import RAGPretrainedModel
    print("RAGAtouille imported successfully")
    
    # Test paths
    project_root = 'C:\\Users\\julie\\Lab_IA_Project\\olkoa'
    path_to_metadata = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'colbert_indexes')
    ragatouille_index_path = os.path.join(project_root, '.ragatouille', 'colbert', 'indexes', f"{ACTIVE_PROJECT}_emails_index")
    
    print(f"Metadata path exists: {os.path.exists(path_to_metadata)}")
    print(f"Index path exists: {os.path.exists(ragatouille_index_path)}")
    
    # If index exists, try to load and run a simple search
    if os.path.exists(ragatouille_index_path):
        print("\\nTrying to load index...")
        rag_model = RAGPretrainedModel.from_index(ragatouille_index_path)
        print("Index loaded successfully!")
        
        print("\\nRunning a simple search...")
        results = rag_model.search(query="email", k=2, index_name=f"{ACTIVE_PROJECT}_emails_index")
        
        print(f"Results type: {type(results)}")
        print(f"Number of results: {len(results) if results else 0}")
        
        if results:
            print("\\nFirst result structure:")
            result = results[0]
            print(f"Result type: {type(result)}")
            print(f"Result keys: {list(result.keys()) if hasattr(result, 'keys') else 'No keys'}")
            print(f"Result: {result}")
            
    else:
        print("Index does not exist - cannot test search")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
