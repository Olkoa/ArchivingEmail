"""
Test script for Chat + RAG component.

This script verifies that all necessary dependencies are available
and tests the component functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_imports():
    """Test all necessary imports for Chat + RAG functionality."""
    print("Testing imports...")

    try:
        # Test core dependencies
        import streamlit as st
        print("✅ Streamlit imported successfully")

        import pandas as pd
        print("✅ Pandas imported successfully")

        # Test project modules
        from constants import ACTIVE_PROJECT
        print(f"✅ Constants imported successfully (Active project: {ACTIVE_PROJECT})")

        from src.llm.openrouter import openrouter_llm_api_call
        print("✅ OpenRouter LLM module imported successfully")

        # Test RAG modules
        try:
            from src.rag.colbert_rag import search_with_colbert, format_result_preview
            print("✅ ColBERT RAG modules imported successfully")
        except ImportError as e:
            print(f"❌ ColBERT RAG import failed: {e}")
            return False

        try:
            from src.rag.colbert_initialization import initialize_colbert_rag_system
            print("✅ ColBERT initialization module imported successfully")
        except ImportError as e:
            print(f"❌ ColBERT initialization import failed: {e}")
            return False

        # Test RAGAtouille (optional, will show warning if not available)
        try:
            from ragatouille import RAGPretrainedModel
            print("✅ RAGAtouille imported successfully")
        except ImportError as e:
            print(f"⚠️ RAGAtouille not available: {e}")
            print("   Install with: pip install ragatouille")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_component_import():
    """Test importing the Chat + RAG component."""
    print("\nTesting Chat + RAG component import...")

    try:
        from app.components.chat_rag_component import render_chat_rag_component
        print("✅ Chat + RAG component imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Chat + RAG component import failed: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set."""
    print("\nTesting environment variables...")

    required_env_vars = [
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY"
    ]

    all_vars_set = True
    for var in required_env_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is not set")
            all_vars_set = False

    if not all_vars_set:
        print("\n⚠️ Missing environment variables. Please create a .env file with:")
        print("   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1")
        print("   OPENROUTER_API_KEY=your_api_key_here")

    return all_vars_set

def test_project_structure():
    """Test if required project directories exist."""
    print("\nTesting project structure...")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    required_dirs = [
        os.path.join(project_root, 'data', 'Projects', 'Projet Demo'),
        os.path.join(project_root, 'data', 'Projects', 'Projet Demo', 'colbert_indexes'),
        os.path.join(project_root, '.ragatouille')
    ]

    all_dirs_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"⚠️ Directory missing: {dir_path}")
            # Create the directory if it doesn't exist
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   Created directory: {dir_path}")
            except Exception as e:
                print(f"   Failed to create directory: {e}")
                all_dirs_exist = False

    return all_dirs_exist

def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        from src.data.email_analyzer import EmailAnalyzer

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        db_path = os.path.join(project_root, 'data', 'Projects', 'Projet Demo', 'Projet Demo.duckdb')

        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")

            # Try to connect
            analyzer = EmailAnalyzer(db_path=db_path)
            df = analyzer.get_app_DataFrame()
            print(f"✅ Database connection successful, {len(df)} emails found")
            return True
        else:
            print(f"❌ Database file not found: {db_path}")
            return False

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Chat + RAG Component Setup")
    print("=" * 50)

    tests = [
        ("Core Imports", test_imports),
        ("Component Import", test_component_import),
        ("Environment Variables", test_environment_variables),
        ("Project Structure", test_project_structure),
        ("Database Connection", test_database_connection)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Chat + RAG component is ready to use.")
    else:
        print("⚠️ Some tests failed. Please fix the issues above before using Chat + RAG.")
        print("\n📝 Next steps:")
        if not results.get("Environment Variables", True):
            print("   1. Set up your .env file with OpenRouter credentials")
        if not results.get("Core Imports", True):
            print("   2. Install missing Python packages")
        if not results.get("Database Connection", True):
            print("   3. Ensure your email database is properly set up")

    print("=" * 50)

if __name__ == "__main__":
    main()
