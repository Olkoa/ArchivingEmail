# Structure de la boîte mail - Mail Directory Tree Visualization

## Overview

This module provides functionality to visualize the hierarchical structure of email folders using Mermaid diagrams. It creates an interactive tree visualization that shows the organization of email folders and the number of emails in each folder.

## Features

- ✅ **Clean and functional implementation** moved from root to `src/visualization/`
- ✅ **Proper integration** with the main Streamlit app
- ✅ **Mermaid graph generation** with color-coded folder types
- ✅ **Customizable orientation** - vertical (top-down) or horizontal (left-right)
- ✅ **Adjustable font sizes** - small (10px), normal (12px), large (14px), xlarge (16px)
- ✅ **Automatic saving** to project data directories
- ✅ **Dynamic data loading** from DuckDB or sample data
- ✅ **New page integration** in the app navigation
- ✅ **Robust fallback system** for Mermaid display

## Files Created/Modified

### New Files:
1. `src/visualization/mail_directory_tree.py` - Clean, functional module
2. `app/pages/mail_structure.py` - New page for mail structure visualization
3. `data/Projects/{PROJECT_NAME}/mail_folder_structure.mermaid` - Generated graphs

### Modified Files:
1. `app/app.py` - Added navigation for "Structure de la boîte mail"
2. `src/visualization/__init__.py` - Updated imports
3. `mail_directory_tree.py` - Renamed to `mail_directory_tree_old.py` (backup)

## How to Use

### 1. Access the Page
1. Run the Streamlit app: `streamlit run app/app.py`
2. Navigate to **Visualization** > **Structure de la boîte mail**

### 2. Customize the Diagram
1. **Choose orientation:**
   - 📊 **Vertical**: Traditional top-down hierarchy (recommended for deep structures)
   - 📈 **Horizontal**: Left-to-right flow (better for wide structures)

2. **Select font size:**
   - 🔤 **Petit (10px)**: For complex structures with many folders
   - 🔤 **Normal (12px)**: Default recommended size
   - 🔤 **Grand (14px)**: For better readability
   - 🔤 **Très grand (16px)**: For presentations and accessibility

### 3. Generate the Diagram
1. Click the **"🔄 Générer le graphique"** button
2. The system will:
   - Extract folder data from the project's DuckDB database
   - Generate a Mermaid diagram with proper formatting
   - Save the graph to `data/Projects/{Active_PROJECT}/mail_folder_structure.mermaid`
   - Display the interactive diagram

### 3. View and Download
- View the hierarchical structure with color-coded folders
- Download the Mermaid file for external use
- The graph persists between sessions

## Customization Options

### Orientation Options

| Orientation | Mermaid Code | Best For | Use Cases |
|-------------|--------------|----------|----------|
| **Vertical** | `graph TD` | Deep hierarchies | Complex folder structures, traditional org charts |
| **Horizontal** | `graph LR` | Wide structures | Presentations, wide screens, process flows |

### Font Size Options

| Size | CSS Value | Best For | Use Cases |
|------|-----------|----------|----------|
| **Small** | 10px | Complex diagrams | Many folders, detailed structures |
| **Normal** | 12px | General use | Default recommended size |
| **Large** | 14px | Better readability | Presentations, accessibility |
| **XLarge** | 16px | Maximum readability | Large displays, visual presentations |

### Folder Color Coding

| Folder Type | Color | Description |
|-------------|-------|-------------|
| 🔵 Inbox | Blue (#4285F4) | Boîte de réception / Inbox |
| 🟢 Sent | Green (#34A853) | Éléments envoyés / Sent |
| 🔴 Trash | Red (#EA4335) | Éléments supprimés / Trash |
| 🟣 Spam | Purple (#8E24AA) | Courrier indésirable / Spam |
| 🟡 Drafts | Yellow (#FBBC05) | Brouillons / Drafts |
| 🔷 Archive | Cyan (#0097A7) | Archive |
| ⚫ Root | Gray (#757575) | Root folders |
| ⚪ Custom | Light Gray (#78909C) | Custom/Other folders |

## Technical Implementation

### Core Functions

### Core Functions

#### `generate_mermaid_folder_graph(df, folder_column='folders', count_column=None, orientation='vertical', font_size='normal')`
- Generates Mermaid diagram code from folder structure data
- **New**: `orientation` parameter - 'vertical' (TD) or 'horizontal' (LR)
- **New**: `font_size` parameter - 'small', 'normal', 'large', or 'xlarge'
- Handles hierarchical folder paths
- Creates safe node IDs and proper styling with custom font sizes

#### `get_folder_structure_from_project(project_name, project_root)`
- Extracts folder data from project's DuckDB database
- Falls back to sample data if database unavailable
- Returns pandas DataFrame with folder paths and counts

#### `save_mermaid_graph(mermaid_code, project_name, project_root)`
- Saves generated Mermaid code to project directory
- Creates directory structure if needed
- Returns path to saved file

#### `load_existing_mermaid_graph(project_name, project_root)`
- Loads previously generated graph from file
- Returns None if no existing graph found

### Path Structure

```
project_root/
├── src/visualization/
│   ├── mail_directory_tree.py       # Main module
│   └── __init__.py                  # Updated imports
├── app/pages/
│   └── mail_structure.py            # New page implementation
├── data/Projects/{PROJECT_NAME}/
│   └── mail_folder_structure.mermaid # Generated graph
└── app/app.py                       # Updated navigation
```

## Sample Output

The generated Mermaid diagram creates a hierarchical tree like this:

```
📧 celine.guyon
├── 📥 Boîte de réception (12,499)
│   ├── 📁 Archives classifiées (423)
│   ├── 📁 Gestion crise (75)
│   │   └── 📁 Ateliers (28)
│   ├── 📁 Instances (60)
│   ├── 📁 RH (40)
│   ├── 📁 Plaidoyer (38)
│   ├── 📁 Idées (18)
│   ├── 📁 Gazette (10)
│   ├── 📁 AG (6)
│   ├── 📁 Conflit (6)
│   └── 📁 Formation à distance (2)
├── 📤 Éléments envoyés (5,559)
├── 🗑️ Éléments supprimés (277)
├── 📧 Courrier indésirable (45)
├── 📝 Brouillons (41)
└── 📁 Archive (10)
```

## Integration with Main App

The new page is integrated into the main navigation:

```python
navigation_categories = {
    "Overview": ["Dashboard"],
    "Exploration": ["Email Explorer", "Network Analysis", "Timeline"],
    "Visualization": ["Structure de la boîte mail"],  # New category
    "Search": ["Recherche", "Recherche ElasticSearch"],
    "Graph": ["Graph"],
    "AI Assistants": ["Chat", "Colbert RAG", "Chat + RAG"]
}
```

## Error Handling

The system includes comprehensive error handling:
- Database connection failures fall back to sample data
- File I/O errors are caught and logged
- Missing directories are created automatically
- Invalid folder paths are sanitized for Mermaid compatibility

## Future Enhancements

Potential improvements:
- Click-to-navigate functionality from graph nodes
- Filter/search within the folder structure
- Export to other formats (PNG, SVG)
- Real-time updates when email data changes
- Folder statistics (size, recent activity)

## Dependencies

- `pandas` - Data manipulation
- `streamlit` - Web interface
- `pathlib` - Path handling
- Built-in DuckDB integration through `EmailAnalyzer`

## Testing

A test file is provided at `test_mail_tree.py` to verify functionality:
- Tests sample data generation
- Validates Mermaid code generation
- Checks file saving operations

## Troubleshooting

### Common Issues:

1. **No graph appears**: Check that the project has a valid DuckDB database
2. **File not saved**: Verify write permissions to the data directory
3. **Malformed graph**: Check for special characters in folder names
4. **Import errors**: Ensure all dependencies are installed

### Debug Steps:

1. Check console output for error messages
2. Verify project directory structure exists
3. Test with sample data using the test script
4. Check file permissions in the data directory
