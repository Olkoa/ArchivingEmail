#!/usr/bin/env python3
"""
Exemple d'utilisation programmatique de Chat + RAG.

Ce script montre comment utiliser les composants Chat + RAG 
sans l'interface Streamlit, utile pour des intégrations ou des tests.
"""

import os
import sys
import time

# Add project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

def example_chat_rag_workflow():
    """
    Exemple complet du workflow Chat + RAG.
    """
    print("🤖 Exemple d'utilisation Chat + RAG")
    print("=" * 50)
    
    # Step 1: Import required modules
    try:
        from src.rag.colbert_rag import search_with_colbert, format_result_preview
        from src.llm.openrouter import openrouter_llm_api_call
        from app.components.chat_rag_component import create_professional_prompt
        from constants import ACTIVE_PROJECT
        print("✅ Modules importés avec succès")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Step 2: Setup paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    path_to_metadata = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'colbert_indexes')
    ragatouille_index_path = os.path.join(project_root, '.ragatouille', 'colbert', 'indexes', f'{ACTIVE_PROJECT}_emails_index')
    
    # Check if index exists
    index_exists = os.path.exists(os.path.join(path_to_metadata, 'email_metadata.pkl'))
    if not index_exists:
        print("❌ Index ColBERT non trouvé")
        print("   Créez l'index via la page 'Colbert RAG' dans l'interface")
        return False
    
    print("✅ Index ColBERT trouvé")
    
    # Step 3: Example question
    user_question = "Quels sont les projets mentionnés dans les emails récents ?"
    print(f"\n📝 Question d'exemple: {user_question}")
    
    # Step 4: RAG Search
    print("\n🔍 Recherche RAG...")
    start_time = time.time()
    
    try:
        retrieved_emails = search_with_colbert(
            query=user_question,
            path_to_metadata=path_to_metadata,
            ragatouille_index_path=ragatouille_index_path,
            top_k=5
        )
        search_time = time.time() - start_time
        print(f"✅ {len(retrieved_emails)} emails trouvés en {search_time:.2f}s")
        
        # Show preview of first result
        if retrieved_emails:
            print("\n📧 Premier email trouvé:")
            preview = format_result_preview(retrieved_emails[0])
            print(preview[:300] + "..." if len(preview) > 300 else preview)
        
    except Exception as e:
        print(f"❌ Erreur recherche RAG: {e}")
        return False
    
    # Step 5: Create LLM prompt
    print("\n🤖 Création du prompt pour LLM...")
    try:
        system_prompt, user_prompt = create_professional_prompt(user_question, retrieved_emails)
        print(f"✅ Prompt créé ({len(user_prompt)} caractères)")
    except Exception as e:
        print(f"❌ Erreur création prompt: {e}")
        return False
    
    # Step 6: LLM Call
    print("\n🧠 Appel LLM...")
    llm_start_time = time.time()
    
    try:
        # Use a fast model for this example
        llm_response = openrouter_llm_api_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="openai/gpt-4o-mini"  # Fast and economical
        )
        llm_time = time.time() - llm_start_time
        print(f"✅ Réponse reçue en {llm_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Erreur appel LLM: {e}")
        print("   Vérifiez votre fichier .env et votre clé API OpenRouter")
        return False
    
    # Step 7: Display results
    print("\n" + "=" * 50)
    print("📋 RÉSULTAT FINAL")
    print("=" * 50)
    print(f"❓ Question: {user_question}")
    print(f"📧 Sources: {len(retrieved_emails)} emails")
    print(f"⏱️ Temps total: {search_time + llm_time:.2f}s")
    print(f"\n🤖 Réponse IA:")
    print("-" * 30)
    print(llm_response)
    print("-" * 30)
    
    return True

def example_batch_questions():
    """
    Exemple de traitement de plusieurs questions en lot.
    """
    print("\n\n🔄 Exemple de traitement en lot")
    print("=" * 50)
    
    questions = [
        "Qui a envoyé le plus d'emails récemment ?",
        "Y a-t-il des réunions planifiées ?",
        "Quels sont les projets en cours ?"
    ]
    
    print(f"📝 {len(questions)} questions à traiter...")
    
    # Note: Dans un vrai scenario, vous pourriez optimiser
    # en réutilisant la même session RAG
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/{len(questions)} ---")
        print(f"❓ {question}")
        
        # Ici, vous pourriez appeler le même workflow que ci-dessus
        # mais de manière optimisée pour le traitement en lot
        print("   (Traitement simulé pour cet exemple)")
        time.sleep(0.5)  # Simulation
        print("   ✅ Traitée")

def main():
    """
    Fonction principale d'exemple.
    """
    print("🚀 Chat + RAG - Exemples d'utilisation programmatique")
    print("=" * 60)
    
    # Check environment
    if not os.path.exists(".env"):
        print("⚠️ Fichier .env manquant")
        print("   Créez un fichier .env avec votre clé API OpenRouter")
        return
    
    # Run examples
    examples = [
        ("Workflow complet", example_chat_rag_workflow),
        ("Traitement en lot", example_batch_questions)
    ]
    
    for example_name, example_func in examples:
        print(f"\n🎯 {example_name}")
        print("-" * 40)
        
        try:
            success = example_func()
            if success is False:
                print(f"❌ Exemple '{example_name}' échoué")
                break
        except Exception as e:
            print(f"❌ Erreur dans '{example_name}': {e}")
            break
    
    print("\n" + "=" * 60)
    print("✨ Exemples terminés!")
    print("\n💡 Utilisations possibles:")
    print("- Scripts d'analyse automatique d'emails")
    print("- Intégration dans d'autres applications")
    print("- API REST pour services web")
    print("- Traitement en lot de grandes quantités de questions")

if __name__ == "__main__":
    main()
