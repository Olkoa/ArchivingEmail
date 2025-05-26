"""
Chat + RAG Component for Okloa.

This component combines the Chat interface with RAG functionality,
providing a question-answer interface that uses Colbert RAG to retrieve
relevant emails and then processes them through an LLM for comprehensive answers.
"""

import streamlit as st
import pandas as pd
import os
import sys
import time
from typing import List, Dict, Any, Tuple, Optional

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules from the project
from src.rag.colbert_rag import search_with_colbert, format_result_preview
from src.llm.openrouter import openrouter_llm_api_call
from constants import ACTIVE_PROJECT

# Check if RAGAtouille is available
RAGATOUILLE_AVAILABLE = True
try:
    from src.rag.colbert_initialization import initialize_colbert_rag_system
except ImportError as e:
    print(f"RAGAtouille import failed: {e}")
    RAGATOUILLE_AVAILABLE = False


def create_professional_prompt(user_question: str, retrieved_emails: List[Dict[str, Any]]) -> str:
    """
    Create a professional prompt for the LLM based on user question and retrieved emails.
    
    Args:
        user_question: The user's original question
        retrieved_emails: List of emails retrieved by RAG
    
    Returns:
        Complete prompt for the LLM
    """
    system_prompt = """Vous êtes un assistant professionnel spécialisé dans l'analyse d'archives d'emails. 
Votre rôle est de répondre aux questions des utilisateurs en vous basant UNIQUEMENT sur les informations 
présentes dans la collection d'emails fournie.

INSTRUCTIONS IMPORTANTES:
1. Répondez UNIQUEMENT à partir des informations présentes dans les emails fournis
2. Si les informations ne sont pas suffisantes pour répondre, indiquez-le clairement
3. Citez les emails pertinents en mentionnant l'expéditeur et le sujet quand possible
4. Soyez précis et factuel
5. N'inventez aucune information qui ne serait pas dans les emails
6. Structurez votre réponse de manière claire et professionnelle"""

    # Construct the email context
    emails_context = "\n\n=== EMAILS RÉCUPÉRÉS ===\n"
    
    for i, email in enumerate(retrieved_emails, 1):
        metadata = email.get('metadata', {})
        text_content = email.get('text', '')
        
        emails_context += f"\n--- EMAIL {i} ---\n"
        emails_context += f"De: {metadata.get('from', 'Inconnu')}\n"
        emails_context += f"À: {metadata.get('to_recipients', 'Inconnu')}\n"
        emails_context += f"Sujet: {metadata.get('subject', 'Pas de sujet')}\n"
        emails_context += f"Date: {metadata.get('date', 'Date inconnue')}\n"
        emails_context += f"Contenu:\n{text_content}\n"
    
    user_prompt = f"""Question de l'utilisateur: {user_question}

{emails_context}

=== CONSIGNE ===
En vous basant UNIQUEMENT sur les emails ci-dessus, répondez à la question de l'utilisateur. 
Si les informations ne permettent pas de répondre complètement, indiquez-le clairement."""

    return system_prompt, user_prompt


def render_chat_rag_component(emails_df: pd.DataFrame):
    """
    Render the Chat + RAG component.
    
    Args:
        emails_df: DataFrame containing email data
    """
    
    # Check if RAGAtouille is available
    if not RAGATOUILLE_AVAILABLE:
        st.error("RAGAtouille n'est pas installé ou introuvable dans l'environnement Python actuel.")
        st.info("""
        Pour utiliser Chat + RAG, vous devez installer la bibliothèque RAGAtouille.

        Veuillez exécuter ces commandes dans votre terminal:
        ```
        pip install ragatouille
        pip install -r requirements.txt
        ```

        Assurez-vous de l'installer dans le même environnement Python que votre application Streamlit.
        Après l'installation, redémarrez votre application Streamlit.
        """)
        return

    # Page title and description
    st.title("Chat + RAG - Assistant IA pour vos emails")
    
    st.markdown("""
    Cette interface combine le chat conversationnel avec la recherche RAG avancée.
    Posez vos questions et obtenez des réponses basées sur vos archives d'emails.
    
    **Comment ça fonctionne:**
    1. 🔍 Votre question déclenche une recherche RAG dans vos emails
    2. 🤖 Un LLM analyse les emails trouvés et formule une réponse complète
    3. 📧 Vous voyez la réponse et pouvez consulter les emails sources
    """)

    # Set up paths for the indexes
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    path_to_metadata = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'colbert_indexes')
    ragatouille_index_path = os.path.join(project_root, '.ragatouille', 'colbert', 'indexes', f'{ACTIVE_PROJECT}_emails_index')

    # Check if index exists
    index_exists = os.path.exists(os.path.join(path_to_metadata, 'email_metadata.pkl'))

    if not index_exists:
        st.warning("⚠️ L'index ColBERT n'a pas encore été créé.")
        st.info("Veuillez d'abord créer l'index dans la page 'Colbert RAG' avant d'utiliser Chat + RAG.")
        
        if st.button("🚀 Créer l'index maintenant"):
            with st.spinner("Création de l'index ColBERT en cours..."):
                try:
                    initialize_colbert_rag_system(project_root=project_root, force_rebuild=True)
                    st.success("✅ Index créé avec succès")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création de l'index: {str(e)}")
        return

    # Configuration section in sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # RAG parameters
    st.sidebar.subheader("Paramètres RAG")
    num_emails = st.sidebar.slider(
        "Nombre d'emails à récupérer",
        min_value=3,
        max_value=15,
        value=10,
        step=1,
        help="Nombre d'emails pertinents à récupérer pour répondre à la question"
    )
    
    # LLM parameters
    st.sidebar.subheader("Paramètres LLM")
    model_options = [
        "openai/gpt-4o",
        "openai/gpt-4o-mini", 
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    selected_model = st.sidebar.selectbox(
        "Modèle LLM",
        options=model_options,
        index=0,
        help="Modèle de langage à utiliser pour générer les réponses"
    )

    # Initialize conversation history in session state
    if "chat_rag_history" not in st.session_state:
        st.session_state.chat_rag_history = []

    # Display conversation history
    st.subheader("💬 Conversation")
    
    for message in st.session_state.chat_rag_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                
                # Display sources if available
                if "sources" in message and message["sources"]:
                    with st.expander("📧 Voir les emails sources"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"**Email {i}:**")
                            st.markdown(source)
                            st.markdown("---")

    # Chat input
    user_question = st.chat_input("Posez votre question sur vos emails...")

    if user_question:
        # Display user message
        st.chat_message("user").write(user_question)
        
        # Add to history
        st.session_state.chat_rag_history.append({
            "role": "user", 
            "content": user_question
        })

        # Process the question
        with st.chat_message("assistant"):
            # Show processing steps
            status_placeholder = st.empty()
            
            try:
                # Step 1: RAG Search
                status_placeholder.info("🔍 Recherche d'emails pertinents...")
                
                start_time = time.time()
                retrieved_emails = search_with_colbert(
                    query=user_question,
                    path_to_metadata=path_to_metadata,
                    ragatouille_index_path=ragatouille_index_path,
                    top_k=num_emails
                )
                search_time = time.time() - start_time
                
                if not retrieved_emails:
                    status_placeholder.warning("⚠️ Aucun email pertinent trouvé")
                    response = "Je n'ai pas trouvé d'emails pertinents pour répondre à votre question."
                    st.write(response)
                    
                    # Add to history
                    st.session_state.chat_rag_history.append({
                        "role": "assistant",
                        "content": response,
                        "sources": []
                    })
                    return

                status_placeholder.info(f"✅ {len(retrieved_emails)} emails trouvés ({search_time:.2f}s)")
                
                # Step 2: LLM Processing
                status_placeholder.info("🤖 Génération de la réponse par IA...")
                
                # Create the prompt
                system_prompt, user_prompt = create_professional_prompt(user_question, retrieved_emails)
                
                # Call LLM
                llm_start_time = time.time()
                llm_response = openrouter_llm_api_call(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=selected_model
                )
                llm_time = time.time() - llm_start_time
                
                # Clear status and show final response
                status_placeholder.empty()
                
                # Display the response
                st.write(llm_response)
                
                # Show timing information
                total_time = time.time() - start_time
                st.caption(f"⏱️ Temps total: {total_time:.2f}s (Recherche: {search_time:.2f}s, LLM: {llm_time:.2f}s)")
                
                # Prepare source previews
                source_previews = [format_result_preview(email) for email in retrieved_emails]
                
                # Display sources in expandable section
                with st.expander(f"📧 Voir les {len(retrieved_emails)} emails sources"):
                    for i, preview in enumerate(source_previews, 1):
                        st.markdown(f"**Email {i}:**")
                        st.markdown(preview)
                        if i < len(source_previews):
                            st.markdown("---")
                
                # Add to conversation history
                st.session_state.chat_rag_history.append({
                    "role": "assistant",
                    "content": llm_response,
                    "sources": source_previews,
                    "metadata": {
                        "num_sources": len(retrieved_emails),
                        "search_time": search_time,
                        "llm_time": llm_time,
                        "total_time": total_time,
                        "model": selected_model
                    }
                })

            except Exception as e:
                status_placeholder.error(f"❌ Erreur: {str(e)}")
                error_response = f"Je rencontre une erreur lors du traitement de votre question: {str(e)}"
                st.write(error_response)
                
                # Add error to history
                st.session_state.chat_rag_history.append({
                    "role": "assistant",
                    "content": error_response,
                    "sources": []
                })

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.chat_rag_history = []
            st.rerun()
    
    with col2:
        if st.session_state.chat_rag_history:
            if st.button("📋 Exporter la conversation"):
                # Create export content
                export_content = "# Conversation Chat + RAG\n\n"
                for i, message in enumerate(st.session_state.chat_rag_history):
                    if message["role"] == "user":
                        export_content += f"**Utilisateur:** {message['content']}\n\n"
                    else:
                        export_content += f"**Assistant:** {message['content']}\n\n"
                        if "sources" in message and message["sources"]:
                            export_content += "**Sources:**\n"
                            for j, source in enumerate(message["sources"], 1):
                                export_content += f"Email {j}:\n{source}\n\n"
                        export_content += "---\n\n"
                
                st.download_button(
                    label="💾 Télécharger",
                    data=export_content,
                    file_name=f"conversation_chat_rag_{int(time.time())}.md",
                    mime="text/markdown"
                )
    
    with col3:
        if st.button("ℹ️ Aide"):
            st.info("""
            **Conseils d'utilisation:**
            
            • Posez des questions spécifiques sur le contenu de vos emails
            • Utilisez des termes clés pertinents pour améliorer la recherche
            • Vous pouvez demander des résumés, des dates, des personnes mentionnées
            
            **Exemples de questions:**
            • "Quand est prévue la prochaine réunion ?"
            • "Qui a envoyé des informations sur le projet X ?"
            • "Quelles sont les tâches mentionnées cette semaine ?"
            • "Résume-moi les emails de Marie Durand"
            """)

    # System status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Statut du système")
    
    # Index status
    if index_exists:
        st.sidebar.success("✅ Index ColBERT prêt")
        
        # Show index stats if available
        try:
            import pickle
            metadata_path = os.path.join(path_to_metadata, "email_metadata.pkl")
            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as f:
                    email_metadata = pickle.load(f)
                st.sidebar.info(f"📧 {len(email_metadata)} emails indexés")
        except:
            pass
    else:
        st.sidebar.error("❌ Index non créé")
    
    # Conversation stats
    if st.session_state.chat_rag_history:
        user_messages = [m for m in st.session_state.chat_rag_history if m["role"] == "user"]
        st.sidebar.info(f"💬 {len(user_messages)} questions posées")
