# Initialize visualization module

from .email_network import create_network_graph
from .timeline import create_timeline
from .mail_directory_tree import (
    generate_mermaid_folder_graph,
    get_folder_structure_from_project,
    save_mermaid_graph,
    load_existing_mermaid_graph
)
from .mermaid_display import (
    display_mermaid_diagram,
    display_mermaid_with_fallback,
    show_mermaid_fallback
)

__all__ = [
    'create_network_graph',
    'create_timeline',
    'generate_mermaid_folder_graph',
    'get_folder_structure_from_project',
    'save_mermaid_graph',
    'load_existing_mermaid_graph',
    'display_mermaid_diagram',
    'display_mermaid_with_fallback',
    'show_mermaid_fallback'
]
