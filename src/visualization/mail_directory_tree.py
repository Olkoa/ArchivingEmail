"""
Mail Directory Tree Visualization

This module provides functionality to create and display mail folder structure 
visualizations using Mermaid diagrams.
"""

import pandas as pd
import os
import sys
import json
from pathlib import Path


def generate_mermaid_folder_graph(df, folder_column='folders', count_column=None, 
                                  orientation='horizontal', font_size='large'):
    """
    Generate a Mermaid graph diagram from folder structure data.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the folder paths
    folder_column : str, default='folders'
        Name of the column containing folder paths
    count_column : str or None, default=None
        Name of the column containing counts. If None, will use value_counts
    orientation : str, default='vertical'
        Graph orientation: 'vertical' (TD) or 'horizontal' (LR)
    font_size : str, default='normal'
        Font size: 'small', 'normal', 'large', or 'xlarge'

    Returns:
    --------
    str
        Mermaid diagram code
    """
    # Get folder counts
    if count_column is None:
        folder_counts = df[folder_column].value_counts()
    else:
        folder_counts = df.groupby(folder_column)[count_column].sum()

    # Set graph direction based on orientation
    graph_direction = "graph TD" if orientation == 'vertical' else "graph LR"
    
    # Set font size based on parameter
    font_sizes = {
        'tiny': '8px',        # ← New tiny size
        'small': '10px',
        'normal': '12px', 
        'large': '14px',
        'xlarge': '16px',
        'huge': '20px'        # ← New huge size
    }
    
    selected_font_size = font_sizes.get(font_size, '12px')
    
    # Start building the Mermaid diagram
    mermaid_code = [
        graph_direction,
        f"    classDef inbox fill:#4285F4,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef sent fill:#34A853,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef trash fill:#EA4335,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef spam fill:#8E24AA,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef drafts fill:#FBBC05,color:black,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef archive fill:#0097A7,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef root fill:#757575,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        f"    classDef subFolder fill:#78909C,color:white,stroke:#fff,stroke-width:1px,font-size:{selected_font_size}",
        ""
    ]

    # Process folder paths to create nodes and relationships
    nodes = {}
    node_classes = {}
    relationships = []

    # Helper function to create safe node IDs
    def create_node_id(path):
        # Replace characters that might cause issues in Mermaid
        safe_id = path.replace('/', '_').replace(' ', '_').replace('-', '_')
        safe_id = safe_id.replace('à', 'a').replace('é', 'e').replace('è', 'e')
        safe_id = safe_id.replace('ç', 'c').replace('ô', 'o').replace('î', 'i')
        return safe_id

    # Helper function to determine node class
    def determine_node_class(folder_name):
        folder_name_lower = folder_name.lower()
        if 'boîte de réception' in folder_name_lower or 'inbox' in folder_name_lower:
            return 'inbox'
        elif 'éléments envoyés' in folder_name_lower or 'sent' in folder_name_lower:
            return 'sent'
        elif 'éléments supprimés' in folder_name_lower or 'trash' in folder_name_lower:
            return 'trash'
        elif 'courrier indésirable' in folder_name_lower or 'spam' in folder_name_lower:
            return 'spam'
        elif 'brouillons' in folder_name_lower or 'drafts' in folder_name_lower:
            return 'drafts'
        elif 'archive' in folder_name_lower:
            return 'archive'
        elif folder_name_lower == 'root' or 'celine.guyon' in folder_name_lower:
            return 'root'
        else:
            return 'subFolder'

    # Process each path
    for path, count in folder_counts.items():
        parts = path.split('/')

        # Process each part of the path
        for i in range(len(parts)):
            # Current node info
            current_path = '/'.join(parts[:i+1])
            current_name = parts[i]
            current_id = create_node_id(current_path)

            # Parent node info
            if i > 0:
                parent_path = '/'.join(parts[:i])
                parent_id = create_node_id(parent_path)
                relationships.append(f"    {parent_id} --> {current_id}")

            # Only add node if not already added
            if current_id not in nodes:
                # Get count for this exact path
                node_count = count if current_path == path else ""

                # Format count if present
                count_str = f" ({node_count})" if node_count else ""

                # Create node
                nodes[current_id] = f'    {current_id}["{current_name}{count_str}"]'

                # Determine node class
                node_class = determine_node_class(current_name)
                node_classes[current_id] = node_class

    # Add nodes to diagram
    mermaid_code.extend(nodes.values())
    mermaid_code.append("")

    # Add relationships
    mermaid_code.extend(relationships)
    mermaid_code.append("")

    # Add styling
    for node_id, node_class in node_classes.items():
        mermaid_code.append(f"    {node_id}:::{node_class}")

    return "\n".join(mermaid_code)


def get_folder_data_from_db(db_path):
    """
    Extract folder structure data from DuckDB.
    
    Parameters:
    -----------
    db_path : str
        Path to the DuckDB database
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with folders and their email counts
    """
    try:
        # Add project root to path to import EmailAnalyzer
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        from src.data.email_analyzer import EmailAnalyzer
        
        # Initialize analyzer and get folder structure
        analyzer = EmailAnalyzer(db_path=db_path)
        
        # Get folder structure query
        folder_query = """
        SELECT 
            folder_path as folders,
            COUNT(*) as count
        FROM emails 
        WHERE folder_path IS NOT NULL 
        GROUP BY folder_path 
        ORDER BY count DESC
        """
        
        df = analyzer.execute_query(folder_query)
        return df
        
    except Exception as e:
        print(f"Error extracting folder data from database: {e}")
        # Return sample data for demonstration
        return get_sample_folder_data()


def get_sample_folder_data():
    """
    Return sample folder data for demonstration purposes.
    
    Returns:
    --------
    pandas.DataFrame
        Sample DataFrame with folder structure
    """
    data = {
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
    
    return pd.DataFrame({'folders': list(data.keys()), 'count': list(data.values())})


def save_mermaid_graph(mermaid_code, project_name, project_root):
    """
    Save the generated Mermaid graph to the project data folder.
    
    Parameters:
    -----------
    mermaid_code : str
        The Mermaid diagram code
    project_name : str
        Name of the active project
    project_root : str
        Path to the project root directory
        
    Returns:
    --------
    str
        Path to the saved file
    """
    try:
        # Create the data directory path for the project
        data_dir = Path(project_root) / "data" / "Projects" / project_name
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the Mermaid graph
        graph_file = data_dir / "mail_folder_structure.mermaid"
        
        with open(graph_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)
        
        print(f"Mermaid graph saved to: {graph_file}")
        return str(graph_file)
        
    except Exception as e:
        print(f"Error saving Mermaid graph: {e}")
        return None


def load_existing_mermaid_graph(project_name, project_root):
    """
    Load an existing Mermaid graph from the project data folder.
    
    Parameters:
    -----------
    project_name : str
        Name of the active project
    project_root : str
        Path to the project root directory
        
    Returns:
    --------
    str or None
        The Mermaid diagram code if found, None otherwise
    """
    try:
        graph_file = Path(project_root) / "data" / "Projects" / project_name / "mail_folder_structure.mermaid"
        
        if graph_file.exists():
            with open(graph_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
        
    except Exception as e:
        print(f"Error loading existing Mermaid graph: {e}")
        return None


def get_folder_structure_from_project(project_name, project_root):
    """
    Get folder structure data for a specific project.
    
    Parameters:
    -----------
    project_name : str
        Name of the project
    project_root : str
        Path to the project root directory
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with folder structure data
    """
    try:
        # Try to get data from DuckDB first
        db_path = Path(project_root) / "data" / "Projects" / project_name / f"{project_name}.duckdb"
        
        if db_path.exists():
            return get_folder_data_from_db(str(db_path))
        else:
            print(f"Database not found at {db_path}, using sample data")
            return get_sample_folder_data()
            
    except Exception as e:
        print(f"Error getting folder structure from project: {e}")
        return get_sample_folder_data()
