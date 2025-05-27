"""
Debug script to test and fix the arrow duplication issue
"""

import sys
import os
import pandas as pd

# Add the necessary paths
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.visualization.mail_directory_tree import generate_mermaid_folder_graph

def debug_arrow_duplication():
    """Debug the exact duplication issue with real data."""
    print("🔍 Debugging Arrow Duplication Issue")
    print("=" * 50)
    
    # Use the exact data structure that's causing problems
    test_data = {
        "celine.guyon/Boîte de réception": 12499,
        "celine.guyon/Éléments envoyés": 5559,
        "celine.guyon/Boîte de réception/Archives classifiées": 423,
        "celine.guyon/Éléments supprimés": 277,
        "celine.guyon/Boîte de réception/gestioncrise": 75,
        "celine.guyon/Boîte de réception/Instances": 60,
        "celine.guyon/Courrier indésirable": 45,
        "celine.guyon/Brouillons": 41,
        "celine.guyon/Boîte de réception/RH": 40,
        "celine.guyon/Boîte de réception/Plaidoyer": 38,
        "celine.guyon/Boîte de réception/gestioncrise/Ateliers": 28,
        "root": 20,
        "celine.guyon/Boîte de réception/Idees": 18,
        "celine.guyon/Archive": 10,
        "celine.guyon/Boîte de réception/Gazette": 10,
        "celine.guyon/Boîte de réception/AG": 6,
        "celine.guyon/Boîte de réception/Conflit": 6,
        "celine.guyon/Boîte de réception/Formation à distance": 2
    }
    
    df = pd.DataFrame({'folders': list(test_data.keys()), 'count': list(test_data.values())})
    
    print(f"Input data: {len(df)} folders")
    
    # Generate the graph
    mermaid_code = generate_mermaid_folder_graph(
        df, 
        folder_column='folders', 
        count_column='count',
        orientation='horizontal',
        font_size='normal'
    )
    
    # Analyze the relationships
    lines = mermaid_code.split('\\n')
    arrow_lines = [line.strip() for line in lines if '-->' in line and line.strip()]
    
    print(f"Generated {len(arrow_lines)} relationship lines")
    
    # Count duplicates
    relationship_counts = {}
    for arrow in arrow_lines:
        relationship_counts[arrow] = relationship_counts.get(arrow, 0) + 1
    
    # Find duplicates
    duplicates = {rel: count for rel, count in relationship_counts.items() if count > 1}
    
    if duplicates:
        print(f"FOUND {len(duplicates)} DUPLICATE RELATIONSHIPS:")
        for rel, count in duplicates.items():
            print(f"   {rel} appears {count} times")
        return False
    else:
        print(f"SUCCESS: No duplicate relationships found!")
        return True

if __name__ == "__main__":
    debug_arrow_duplication()
