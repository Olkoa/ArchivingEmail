import streamlit as st
from streamlit_modal import Modal

st.title("Test de Modal")

# Create a button to trigger the modal
if st.button("Ouvrir Modal"):
    # Create and configure the modal
    modal = Modal(
        "Modal de Test",
        key="test_modal"
    )

    # Modal content
    with modal.container():
        st.write("Ceci est un test de modal.")
        st.write("Si vous voyez ce texte, la bibliothèque fonctionne correctement.")

        if st.button("Fermer"):
            st.rerun()
