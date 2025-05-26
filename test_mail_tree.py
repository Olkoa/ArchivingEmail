"""
Test script for the mail directory tree functionality
"""

import sys
import os
import pandas as pd

# Add the necessary paths
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.visualization.mail_directory_tree import (
    generate_mermaid_folder_graph,
    get_sample_folder_data,
    save_mermaid_graph
)

def test_mail_directory_tree():
    """Test the mail directory tree functionality."""
    
    print("Testing mail directory tree functionality...")
    
    # Test 1: Get sample data
    print("\n1. Getting sample folder data...")
    df = get_sample_folder_data()
    print(f"   - Sample data loaded: {len(df)} folders")
    print(f"   - Columns: {list(df.columns)}")
    print(f"   - Sample folders: {df['folders'].head(3).tolist()}")
    
    # Test 2: Generate Mermaid graph
    print("\n2. Generating Mermaid graph...")
    mermaid_code = generate_mermaid_folder_graph(df, folder_column='folders', count_column='count')
    print(f"   - Graph generated successfully")
    print(f"   - Graph length: {len(mermaid_code)} characters")
    print(f"   - First few lines:")
    for line in mermaid_code.split('\n')[:5]:
        print(f"     {line}")
    
    # Test 3: Save the graph
    print("\n3. Testing save functionality...")
    project_name = "Test_Project"
    saved_path = save_mermaid_graph(mermaid_code, project_name, project_root)
    if saved_path:
        print(f"   - Graph saved to: {saved_path}")
        
        # Check if file exists
        if os.path.exists(saved_path):
            print(f"   - File exists and is {os.path.getsize(saved_path)} bytes")
        else:
            print("   - Warning: File was not created")
    else:
        print("   - Error: Failed to save graph")
    
    print("\n✅ Tests completed!")
    
    return mermaid_code

if __name__ == "__main__":
    test_mail_directory_tree()
