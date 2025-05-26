"""
Installation helper for streamlit-mermaid

This script helps install streamlit-mermaid for better Mermaid diagram rendering.
"""

import subprocess
import sys
import os

def check_streamlit_mermaid():
    """Check if streamlit-mermaid is already installed."""
    try:
        import streamlit_mermaid
        return True
    except ImportError:
        return False

def install_streamlit_mermaid():
    """Install streamlit-mermaid using pip."""
    try:
        print("Installing streamlit-mermaid...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "streamlit-mermaid"
        ], check=True, capture_output=True, text=True)
        
        print("✅ streamlit-mermaid installed successfully!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main installation flow."""
    print("🔧 Streamlit-Mermaid Installation Helper")
    print("=" * 45)
    
    # Check if already installed
    if check_streamlit_mermaid():
        print("✅ streamlit-mermaid is already installed!")
        print("   Your Mail Structure page will use the optimized renderer.")
        return
    
    # Ask user if they want to install
    print("📊 streamlit-mermaid is not currently installed.")
    print("\nBenefits of installing streamlit-mermaid:")
    print("  • Better performance for Mermaid diagrams")
    print("  • Native Streamlit integration")
    print("  • Enhanced interactivity")
    print("\nNote: The application works fine without it (using HTML fallback)")
    
    while True:
        choice = input("\nWould you like to install streamlit-mermaid? (y/n): ").lower().strip()
        
        if choice in ['y', 'yes']:
            success = install_streamlit_mermaid()
            if success:
                print("\n🎉 Installation complete!")
                print("   Restart your Streamlit app to use the new renderer.")
                print("   Go to: Visualization > Structure de la boîte mail")
            else:
                print("\n⚠️ Installation failed, but don't worry!")
                print("   The HTML fallback will still work perfectly.")
            break
            
        elif choice in ['n', 'no']:
            print("\n👍 No problem!")
            print("   The Mail Structure page will use HTML rendering.")
            print("   This works just as well, just slightly different rendering.")
            break
            
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    
    print("\n📖 For more information, see: STREAMLIT_MERMAID_SETUP.md")

if __name__ == "__main__":
    main()
