"""
Mermaid Display Helper

This module provides helper functions to display Mermaid diagrams in Streamlit,
with fallback options if streamlit-mermaid is not available.
"""

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse


def display_mermaid_diagram(mermaid_code, height=600):
    """
    Display a Mermaid diagram in Streamlit using the best available method.
    
    Parameters:
    -----------
    mermaid_code : str
        The Mermaid diagram code
    height : int
        Height of the diagram display area
        
    Returns:
    --------
    bool
        True if diagram was displayed successfully, False otherwise
    """
    
    # Method 1: Try streamlit-mermaid if available
    try:
        from streamlit_mermaid import st_mermaid
        st_mermaid(mermaid_code, height=height)
        return True
    except ImportError:
        pass
    
    # Method 2: Use HTML component with Mermaid.js CDN
    try:
        mermaid_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #ffffff;
                }}
                .mermaid {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: {height - 100}px;
                }}
                .error {{
                    color: #d32f2f;
                    background-color: #ffebee;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid">
{mermaid_code}
            </div>
            <script>
                try {{
                    mermaid.initialize({{ 
                        startOnLoad: true, 
                        theme: 'default',
                        flowchart: {{
                            useMaxWidth: true,
                            htmlLabels: true
                        }},
                        securityLevel: 'loose'
                    }});
                }} catch (error) {{
                    document.body.innerHTML = '<div class="error">Erreur lors du rendu du diagramme: ' + error.message + '</div>';
                }}
            </script>
        </body>
        </html>
        """
        
        components.html(mermaid_html, height=height, scrolling=True)
        return True
        
    except Exception as e:
        st.error(f"Erreur lors de l'affichage HTML: {str(e)}")
        return False


def show_mermaid_fallback(mermaid_code):
    """
    Show fallback options when Mermaid diagram cannot be displayed.
    
    Parameters:
    -----------
    mermaid_code : str
        The Mermaid diagram code
    """
    
    st.subheader("📝 Code Mermaid")
    st.info("Le diagramme ne peut pas être affiché directement. Voici le code Mermaid :")
    
    # Show the code
    st.code(mermaid_code, language="text")
    
    # Provide link to online editor
    try:
        encoded_graph = urllib.parse.quote(mermaid_code)
        mermaid_live_url = f"https://mermaid.live/edit#{encoded_graph}"
        st.markdown(f"🌐 [Voir dans l'éditeur Mermaid en ligne]({mermaid_live_url})")
    except Exception:
        st.markdown("🌐 [Éditeur Mermaid en ligne](https://mermaid.live/)")
    
    # Installation instructions
    with st.expander("💡 Comment améliorer l'affichage"):
        st.markdown("""
        ### Options pour un meilleur affichage:
        
        1. **Installer streamlit-mermaid:**
           ```bash
           pip install streamlit-mermaid
           ```
        
        2. **Utiliser l'éditeur en ligne:**
           - Cliquez sur le lien ci-dessus
           - Copiez-collez le code Mermaid
           - Exportez en PNG/SVG si nécessaire
        
        3. **Intégration dans d'autres outils:**
           - GitHub/GitLab: Support natif des diagrammes Mermaid
           - Notion: Support via blocs de code
           - VS Code: Extensions Mermaid disponibles
        """)


def display_mermaid_with_fallback(mermaid_code, height=600):
    """
    Display a Mermaid diagram with comprehensive fallback options.
    
    Parameters:
    -----------
    mermaid_code : str
        The Mermaid diagram code
    height : int
        Height of the diagram display area
    """
    
    # Try to display the diagram
    success = display_mermaid_diagram(mermaid_code, height)
    
    # If display failed, show fallback options
    if not success:
        show_mermaid_fallback(mermaid_code)
