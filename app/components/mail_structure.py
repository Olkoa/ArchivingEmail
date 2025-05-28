"""
Structure de la boîte mail - Page de visualisation

Cette page affiche la structure hiérarchique des dossiers de la boîte mail
sous forme de diagramme Mermaid interactif.
"""

import streamlit as st
import pandas as pd
import os
import sys
import json
from pathlib import Path

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the mail directory tree functions
from src.visualization.mail_directory_tree import (
    generate_mermaid_folder_graph,
    get_folder_structure_from_project,
    save_mermaid_graph,
    load_existing_mermaid_graph
)
from src.visualization.mermaid_display import display_mermaid_with_fallback


def render_mail_structure_page():
    """Render the mail structure visualization page."""
    
    st.title("📁 Structure de la boîte mail")
    st.markdown("""
    Cette page affiche la structure hiérarchique des dossiers de votre boîte mail.
    Le diagramme montre l'organisation des dossiers et le nombre d'emails dans chacun.
    """)
    
    # Get the active project name
    # For now, we'll use the same logic as in the main app
    project_name = "Projet Demo"
    
    # Check if a Mermaid graph already exists
    existing_graph = load_existing_mermaid_graph(project_name, project_root)
    
    # Create columns for the interface
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Actions")
        
        # Graph customization options
        st.subheader("🎨 Options de personnalisation")
        
        # Orientation selection
        orientation = st.radio(
            "Orientation du graphique:",
            options=['vertical', 'horizontal'],
            format_func=lambda x: '📊 Vertical (haut en bas)' if x == 'vertical' else '📈 Horizontal (gauche à droite)',
            key="graph_orientation"
        )
        
        # Font size selection
        font_size = st.selectbox(
            "Taille du texte:",
            options=['très petit', 'petit', 'assez petit', 'normal', 'large', 'très large'],
            format_func=lambda x: {
                'très petit': '🔤 Très petit (14px)',
                'petit': '🔤 Petit (16px)',
                'assez petit': '🔤 Assez petit (18px)',
                'normal': '🔤 Normal (20px)', 
                'large': '🔤 Large (24px)',
                'très large': '🔤 Très large (28px)'
            }[x],
            index=3,  # Default to 'normal'
            key="graph_font_size"
        )
        
        st.markdown("---")
        
        # Button to generate/regenerate the graph
        if st.button("🔄 Générer le graphique", help="Créer ou mettre à jour le diagramme de structure"):
            with st.spinner("Génération du diagramme en cours..."):
                try:
                    # Get folder structure data from the project
                    folder_df = get_folder_structure_from_project(project_name, project_root)
                    
                    if folder_df.empty:
                        st.error("Aucune donnée de dossier trouvée pour ce projet.")
                        return
                    
                    # Generate the Mermaid diagram with custom options
                    mermaid_code = generate_mermaid_folder_graph(
                        folder_df, 
                        folder_column='folders', 
                        count_column='count',
                        orientation=orientation,
                        font_size=font_size
                    )
                    
                    # Save the graph to the project directory
                    saved_path = save_mermaid_graph(mermaid_code, project_name, project_root)
                    
                    if saved_path:
                        st.success(f"✅ Diagramme généré et sauvegardé!")
                        st.info(f"📁 Fichier sauvé dans: `{saved_path}`")
                        st.info(f"🎨 Options: {orientation.title()}, Taille: {font_size}")
                        
                        # Store in session state to display immediately
                        st.session_state.current_mermaid_graph = mermaid_code
                        st.session_state.graph_generated = True
                        st.session_state.graph_orientation = orientation
                        st.session_state.graph_font_size = font_size
                        
                        # Rerun to display the new graph
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde du diagramme.")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération du diagramme: {str(e)}")
        
        # Show information about the current graph
        if existing_graph:
            st.success("✅ Diagramme existant trouvé")
            
            # Get graph file info
            graph_file = Path(project_root) / "data" / "Projects" / project_name / "mail_folder_structure.mermaid"
            if graph_file.exists():
                file_size = graph_file.stat().st_size
                st.info(f"📊 Taille du fichier: {file_size} bytes")
                
                # Try to detect current settings from the existing graph
                if "graph LR" in existing_graph:
                    st.info("📈 Orientation actuelle: Horizontal")
                elif "graph TD" in existing_graph:
                    st.info("📊 Orientation actuelle: Vertical")
                    
                # Show current font size if detectable
                if "font-size:" in existing_graph:
                    if "14px" in existing_graph:
                        st.info("🔤 Taille actuelle: Très petit")
                    elif "16px" in existing_graph:
                        st.info("🔤 Taille actuelle: Petit")
                    elif "18px" in existing_graph:
                        st.info("🔤 Taille actuelle: Assez petit")
                    elif "20px" in existing_graph:
                        st.info("🔤 Taille actuelle: Normal")
                    elif "24px" in existing_graph:
                        st.info("🔤 Taille actuelle: Large")
                    elif "28px" in existing_graph:
                        st.info("🔤 Taille actuelle: Très large")
                    else:
                        st.info("🔤 Taille actuelle: Normal")
        else:
            st.warning("⚠️ Aucun diagramme existant trouvé")
            st.info("Cliquez sur 'Générer le graphique' pour créer le diagramme.")
    
    with col1:
        st.subheader("Diagramme de structure")
        
        # Display the graph
        graph_to_display = None
        
        # Check if we just generated a new graph
        if hasattr(st.session_state, 'current_mermaid_graph') and st.session_state.get('graph_generated', False):
            graph_to_display = st.session_state.current_mermaid_graph
            # Clear the flag to avoid redisplaying on every rerun
            st.session_state.graph_generated = False
        elif existing_graph:
            graph_to_display = existing_graph
        
        if graph_to_display:
            # Display the Mermaid diagram using our helper function
            display_mermaid_with_fallback(graph_to_display, height=600)
            
            # Add download button for the graph
            st.download_button(
                label="💾 Télécharger le diagramme (.mermaid)",
                data=graph_to_display,
                file_name=f"{project_name}_mail_structure_{st.session_state.get('graph_orientation', 'vertical')}_{st.session_state.get('graph_font_size', 'normal')}.mermaid",
                mime="text/plain",
                help="Télécharger le code Mermaid du diagramme"
            )
        else:
            # Show placeholder when no graph is available
            st.info("👆 Générez le diagramme en cliquant sur le bouton 'Générer le graphique'")
            
            # Show a sample/preview
            st.subheader("Exemple de structure")
            st.markdown("""
            Le diagramme affichera la structure hiérarchique de vos dossiers email, comme:
            
            ```
            📧 celine.guyon
            ├── 📥 Boîte de réception (12,499)
            │   ├── 📁 Archives classifiées (423)
            │   ├── 📁 Gestion crise (75)
            │   └── 📁 RH (40)
            ├── 📤 Éléments envoyés (5,559)
            ├── 🗑️ Éléments supprimés (277)
            └── 📁 Archive (10)
            ```
            """)
    
    # Additional information section
    st.markdown("---")
    
    with st.expander("ℹ️ Informations sur le diagramme"):
        st.markdown("""
        ### À propos du diagramme de structure
        
        - **Orientation du graphique:**
          - 📊 Vertical: Structure hiérarchique de haut en bas (recommandé)
          - 📈 Horizontal: Structure de gauche à droite (pour les grands écrans)
        
        - **Taille du texte:**
          - 🔤 Très petit (14px): Pour les structures très complexes
          - 🔤 Petit (16px): Pour les structures complexes
          - 🔤 Assez petit (18px): Taille compacte
          - 🔤 Normal (20px): Taille par défaut recommandée
          - 🔤 Large (24px): Pour une meilleure lisibilité
          - 🔤 Très large (28px): Pour les présentations
        
        - **Couleurs des nœuds:**
          - 🔵 Bleu: Boîte de réception / Inbox
          - 🟢 Vert: Éléments envoyés / Sent
          - 🔴 Rouge: Éléments supprimés / Trash
          - 🟣 Violet: Courrier indésirable / Spam
          - 🟡 Jaune: Brouillons / Drafts
          - 🔷 Cyan: Archive
          - ⚫ Gris: Dossiers personnalisés
        
        - **Format du fichier:** Le diagramme est sauvé en format Mermaid (.mermaid)
        - **Emplacement:** `data/Projects/{project_name}/mail_folder_structure.mermaid`
        - **Mise à jour:** Cliquez sur 'Générer le graphique' pour actualiser les données
        
        ### Utilisation du diagramme
        
        - Visualisez la hiérarchie complète de vos dossiers
        - Identifiez les dossiers contenant le plus d'emails
        - Analysez l'organisation de votre boîte mail
        - Exportez le diagramme pour documentation
        """)
    
    # Technical information
    with st.expander("🔧 Informations techniques"):
        st.markdown(f"""
        ### Configuration actuelle
        
        - **Projet actif:** `{project_name}`
        - **Répertoire projet:** `{project_root}`
        - **Base de données:** `{project_root}/data/Projects/{project_name}/{project_name}.duckdb`
        - **Fichier graphique:** `{project_root}/data/Projects/{project_name}/mail_folder_structure.mermaid`
        
        ### Dépendances
        
        - Mermaid.js via HTML component
        - Pandas pour le traitement des données
        - DuckDB pour l'accès aux données
        """)


# Main execution for standalone testing
if __name__ == "__main__":
    render_mail_structure_page()
