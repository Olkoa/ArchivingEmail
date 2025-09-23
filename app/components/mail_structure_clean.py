"""Mail structure view driven by the current ACTIVE_PROJECT."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


def _resolve_active_project(constants_module=None) -> str:
    if "active_project" in st.session_state:
        value = st.session_state["active_project"]
        if value:
            return value

    env_value = os.getenv("ACTIVE_PROJECT")
    if env_value:
        return env_value

    if constants_module and hasattr(constants_module, "ACTIVE_PROJECT"):
        return getattr(constants_module, "ACTIVE_PROJECT")

    return "Projet Demo"


def render_mail_structure_page() -> None:
    """Render a mail-folder structure diagram for the active project."""

    load_dotenv()

    project_root = Path(__file__).resolve().parents[2]

    # Ensure project root is on sys.path before local imports
    import sys

    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))

    try:
        import constants  # type: ignore
        from src.visualization.mail_directory_tree import (
            generate_mermaid_folder_graph,
            get_folder_structure_from_project,
            save_mermaid_graph,
        )
        from src.visualization.mermaid_display import display_mermaid_with_fallback
    except ImportError as exc:  # pragma: no cover - surface to UI
        st.error(f"Impossible de charger les dépendances de visualisation: {exc}")
        return

    project_name = _resolve_active_project(constants)

    st.title("📁 Structure de la boîte mail")
    st.markdown(
        """
        Visualisez la hiérarchie actuelle des dossiers pour le projet actif. Les compteurs
        indiquent le nombre d'emails présents dans chaque dossier et sous-dossier.
        """
    )

    col_graph, col_options = st.columns([4, 1])

    selected_mailbox = st.session_state.get('selected_mailbox', 'All Mailboxes')
    mailbox_filter = None if not selected_mailbox or selected_mailbox == 'All Mailboxes' else selected_mailbox

    with col_options:
        st.subheader("🎨 Options")

        orientation = st.radio(
            "Orientation",
            options=["horizontal", "vertical"],
            format_func=lambda x: "📈 Horizontal" if x == "horizontal" else "📊 Vertical",
            key="mail_structure_orientation",
        )

        font_size = st.selectbox(
            "Taille du texte",
            options=["très petit", "petit", "assez petit", "normal", "large", "très large"],
            index=3,
            key="mail_structure_font_size",
        )

        st.markdown("---")
        if st.button("💾 Sauvegarder le diagramme", use_container_width=True):
            with st.spinner("Sauvegarde du diagramme..."):
                folder_df = get_folder_structure_from_project(
                    project_name,
                    str(project_root),
                    mailbox=mailbox_filter,
                )
                if folder_df.empty:
                    st.error("Aucune structure détectée pour ce projet.")
                else:
                    mermaid_code = generate_mermaid_folder_graph(
                        folder_df,
                        folder_column="folders",
                        count_column="count",
                        orientation=orientation,
                        font_size=font_size,
                    )
                    saved = save_mermaid_graph(mermaid_code, project_name, str(project_root))
                    if saved:
                        st.success("Diagramme sauvegardé avec succès.")
                    else:
                        st.error("Erreur lors de la sauvegarde du fichier.")

    with col_graph:
        folder_df = get_folder_structure_from_project(
            project_name,
            str(project_root),
            mailbox=mailbox_filter,
        )

        context_label = (
            f"toutes les boîtes" if mailbox_filter is None else f"boîte '{mailbox_filter}'"
        )
        st.caption(f"Structure affichée pour {context_label} du projet {project_name}.")

        if folder_df.empty:
            st.info("Aucune structure de dossiers n'a été trouvée pour ce projet.")
            return

        mermaid_code = generate_mermaid_folder_graph(
            folder_df,
            folder_column="folders",
            count_column="count",
            orientation=orientation,
            font_size=font_size,
        )

        display_mermaid_with_fallback(mermaid_code, height=600)

        st.download_button(
            label="⬇️ Télécharger (.mermaid)",
            data=mermaid_code,
            file_name=f"{project_name}_structure_{orientation}_{font_size}.mermaid",
            mime="text/plain",
            help="Télécharger le code Mermaid généré",
        )


if __name__ == "__main__":  # pragma: no cover - manual testing helper
    render_mail_structure_page()
