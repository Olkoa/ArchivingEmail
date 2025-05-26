#!/usr/bin/env python3
"""
Quick verification script for Chat + RAG setup.
"""

import os
import sys

def main():
    print("🔍 Vérification rapide de Chat + RAG")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("app/app.py"):
        print("❌ Veuillez exécuter ce script depuis le répertoire racine d'Olkoa")
        return False
    
    # Check main files exist
    files_to_check = [
        "app/components/chat_rag_component.py",
        "src/llm/openrouter.py", 
        "src/rag/colbert_rag.py",
        "src/rag/colbert_initialization.py",
        "constants.py"
    ]
    
    print("📁 Vérification des fichiers...")
    all_files_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MANQUANT")
            all_files_exist = False
    
    # Check if app.py contains our new page
    print("\n🔧 Vérification de l'intégration dans app.py...")
    try:
        with open("app/app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
            
        if "Chat + RAG" in app_content:
            print("✅ Page 'Chat + RAG' ajoutée à app.py")
        else:
            print("❌ Page 'Chat + RAG' pas trouvée dans app.py")
            all_files_exist = False
            
        if "render_chat_rag_component" in app_content:
            print("✅ Import du composant trouvé dans app.py")
        else:
            print("❌ Import du composant manquant dans app.py")
            all_files_exist = False
            
    except Exception as e:
        print(f"❌ Erreur lecture app.py: {e}")
        all_files_exist = False
    
    # Check environment
    print("\n🌍 Vérification de l'environnement...")
    if os.path.exists(".env"):
        print("✅ Fichier .env trouvé")
        
        try:
            with open(".env", "r") as f:
                env_content = f.read()
            
            if "OPENROUTER_API_KEY" in env_content:
                print("✅ OPENROUTER_API_KEY configuré")
            else:
                print("⚠️ OPENROUTER_API_KEY manquant dans .env")
                
            if "OPENROUTER_BASE_URL" in env_content:
                print("✅ OPENROUTER_BASE_URL configuré")
            else:
                print("⚠️ OPENROUTER_BASE_URL manquant dans .env")
                
        except Exception as e:
            print(f"❌ Erreur lecture .env: {e}")
    else:
        print("⚠️ Fichier .env manquant")
        print("   Créez un fichier .env avec:")
        print("   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1")
        print("   OPENROUTER_API_KEY=votre_clé_ici")
    
    # Check project structure
    print("\n📂 Vérification de la structure du projet...")
    project_dirs = [
        "data/Projects/Projet Demo",
        ".ragatouille"
    ]
    
    for dir_path in project_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"⚠️ {dir_path} - sera créé au besoin")
    
    print("\n" + "=" * 40)
    if all_files_exist:
        print("🎉 Configuration de base OK!")
        print("\n📋 Prochaines étapes:")
        print("1. Lancez Streamlit: streamlit run app/app.py")
        print("2. Allez dans 'AI Assistants' > 'Chat + RAG'")
        print("3. Créez l'index ColBERT si nécessaire")
        print("4. Testez avec une question!")
    else:
        print("⚠️ Certains fichiers manquent")
        print("Veuillez vérifier l'installation")
    
    return all_files_exist

if __name__ == "__main__":
    main()
