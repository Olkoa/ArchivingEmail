"""
Clean mail structure page that shows the graph by default with debug options hidden
"""

import streamlit as st
from dotenv import load_dotenv
import os


load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

def render_mail_structure_page():
    """Render a clean mail structure page with the graph shown by default."""

    # Import everything inside the function to avoid import-time conflicts
    import pandas as pd
    import os
    import sys
    import json
    from pathlib import Path

    # Add the necessary paths
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    # Import the required functions
    try:
        from src.visualization.mail_directory_tree import (
            generate_mermaid_folder_graph,
            get_folder_structure_from_project,
            save_mermaid_graph,
            load_existing_mermaid_graph
        )
        from src.visualization.mermaid_display import display_mermaid_with_fallback
    except ImportError as e:
        st.error(f"Error importing required modules: {str(e)}")

        # # Show debug options if imports fail
        # with st.expander("🔧 Debug Options", expanded=True):
        #     st.error("Import failed. Use debug options below:")
        #     col1, col2, col3 = st.columns(3)
        #     with col1:
        #         if st.button("Run Step-by-Step Debug"):
        #             st.session_state.use_step_debug_mail_structure = True
        #             st.rerun()
        #     with col2:
        #         if st.button("Try Ultimate Solution"):
        #             st.session_state.use_ultimate_mail_structure = True
        #             st.rerun()
        #     with col3:
        #         if st.button("Run Full Diagnostic"):
        #             st.session_state.use_diagnostic_mail_structure = True
        #             st.rerun()
        return

    # Main title and description
    st.title("📁 Structure de la boîte mail")
    st.markdown("""
    Cette page affiche la structure hiérarchique des dossiers de votre boîte mail.
    Le diagramme montre l'organisation des dossiers et le nombre d'emails dans chacun.
    """)

    # Get the active project name
    project_name = ACTIVE_PROJECT

    # Check if a Mermaid graph already exists
    existing_graph = load_existing_mermaid_graph(project_name, project_root)

    # Create layout with sidebar for controls
    col1, col2 = st.columns([4, 1])

    with col2:
        st.subheader("🎨 Options")

        # Graph customization options
        orientation = st.radio(
            "Orientation:",
            options=['horizontal', 'vertical'],
            format_func=lambda x: '📈 Horizontal' if x == 'horizontal' else '📊 Vertical',
            key="graph_orientation"
        )

        font_size = st.selectbox(
            "Taille du texte:",
            options=['très petit', 'petit', 'assez petit', 'normal', 'large', 'très large'],
            format_func=lambda x: {
                'très petit': '🔤 Très petit',
                'petit': '🔤 Petit',
                'assez petit': '🔤 Assez petit',
                'normal': '🔤 Normal',
                'large': '🔤 Large',
                'très large': '🔤 Très large'
            }[x],
            index=3,  # Default to 'normal'
            key="graph_font_size"
        )

        st.markdown("---")

        # Action buttons
        if st.button("🔄 Générer le graphique", help="Créer ou mettre à jour le diagramme"):
            with st.spinner("Génération en cours..."):
                try:
                    folder_df = get_folder_structure_from_project(project_name, project_root)

                    if folder_df.empty:
                        st.error("Aucune donnée trouvée.")
                        return

                    mermaid_code = generate_mermaid_folder_graph(
                        folder_df,
                        folder_column='folders',
                        count_column='count',
                        orientation=orientation,
                        font_size=font_size
                    )

                    saved_path = save_mermaid_graph(mermaid_code, project_name, project_root)

                    if saved_path:
                        st.success("✅ Diagramme généré!")
                        st.session_state.current_mermaid_graph = mermaid_code
                        st.session_state.graph_generated = True
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde.")

                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

        # Status info
        if existing_graph:
            st.success("✅ Diagramme disponible")
        else:
            st.info("ℹ️ Cliquez sur 'Générer' pour créer le diagramme")

        st.markdown("---")

        # # Debug options (collapsed by default)
        # with st.expander("🔧 Options de debug"):
        #     st.caption("Utilisez ces options en cas de problème")

        #     if st.button("🔍 Debug étape par étape", help="Test chaque composant individuellement"):
        #         st.session_state.use_step_debug_mail_structure = True
        #         st.rerun()

        #     if st.button("🛠️ Version corrigée", help="Version avec imports sécurisés"):
        #         st.session_state.use_fixed_mail_structure = True
        #         st.rerun()

        #     if st.button("🏆 Solution ultime", help="Version la plus robuste"):
        #         st.session_state.use_ultimate_mail_structure = True
        #         st.rerun()

        #     if st.button("📊 Diagnostic complet", help="Analyse complète du système"):
        #         st.session_state.use_diagnostic_mail_structure = True
        #         st.rerun()

    with col1:
        st.subheader("Diagramme de structure")

        # Determine which graph to display
        graph_to_display = None

        # Check if we just generated a new graph
        if hasattr(st.session_state, 'current_mermaid_graph') and st.session_state.get('graph_generated', False):
            graph_to_display = st.session_state.current_mermaid_graph
            st.session_state.graph_generated = False  # Clear flag
        elif existing_graph:
            graph_to_display = existing_graph

        if graph_to_display:
            # Display the Mermaid diagram
            try:
                display_mermaid_with_fallback(graph_to_display, height=600)

                # Download button
                st.download_button(
                    label="💾 Télécharger (.mermaid)",
                    data=graph_to_display,
                    file_name=f"{project_name}_structure_{orientation}_{font_size}.mermaid",
                    mime="text/plain",
                    help="Télécharger le code Mermaid"
                )

            except Exception as e:
                st.error(f"Erreur d'affichage: {str(e)}")
                st.code(graph_to_display[:500] + "..." if len(graph_to_display) > 500 else graph_to_display)
        else:
            # Show placeholder
            st.info("👆 Générez le diagramme en utilisant le bouton à droite")

            # Show example structure
            with st.expander("📖 Exemple de structure"):
                st.markdown("""
                Le diagramme affichera la hiérarchie de vos dossiers:

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


# Main execution for standalone testing
if __name__ == "__main__":
    render_mail_structure_page()
