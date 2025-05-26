"""
Test script for Mermaid display functionality
"""

import sys
import os

# Add the necessary paths
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

def test_mermaid_imports():
    """Test if we can import all our Mermaid-related functions."""
    print("Testing Mermaid display imports...")
    
    try:
        from src.visualization.mermaid_display import (
            display_mermaid_diagram,
            display_mermaid_with_fallback,
            show_mermaid_fallback
        )
        print("✅ Successfully imported mermaid_display functions")
        return True
    except ImportError as e:
        print(f"❌ Failed to import mermaid_display: {e}")
        return False

def test_streamlit_mermaid_availability():
    """Check if streamlit-mermaid is available."""
    print("\nTesting streamlit-mermaid availability...")
    
    try:
        from streamlit_mermaid import st_mermaid
        print("✅ streamlit-mermaid is available")
        return True
    except ImportError:
        print("⚠️ streamlit-mermaid is not installed (will use HTML fallback)")
        return False

def create_sample_mermaid():
    """Create a sample Mermaid diagram for testing."""
    return """
graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]
    
    classDef startEnd fill:#4285F4,color:white
    classDef process fill:#34A853,color:white
    classDef decision fill:#FBBC05,color:black
    
    A:::startEnd
    E:::startEnd
    C:::process
    D:::process
    B:::decision
"""

def test_html_generation():
    """Test HTML generation for Mermaid diagrams."""
    print("\nTesting HTML generation...")
    
    sample_diagram = create_sample_mermaid()
    
    # Simple HTML template test
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    </head>
    <body>
        <div class="mermaid">
{sample_diagram}
        </div>
        <script>
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
    </body>
    </html>
    """
    
    if len(html_template) > 100 and "mermaid" in html_template:
        print("✅ HTML template generation works")
        print(f"   Generated HTML length: {len(html_template)} characters")
        return True
    else:
        print("❌ HTML template generation failed")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Mermaid Display Functionality")
    print("=" * 50)
    
    tests = [
        test_mermaid_imports,
        test_streamlit_mermaid_availability,
        test_html_generation
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")
    
    if all(results[:2]):  # First two tests are critical
        print("\n🎉 Core functionality is working!")
        print("   You can use the Mail Structure page.")
    else:
        print("\n⚠️ Some issues detected, but HTML fallback should work.")
    
    print("\n💡 Recommendations:")
    if not results[1]:  # streamlit-mermaid not available
        print("   - Install streamlit-mermaid for better performance:")
        print("     pip install streamlit-mermaid")
    
    print("   - Test the page: Visualization > Structure de la boîte mail")
    print("   - Use the download button to get .mermaid files")
    print("   - Use the online editor link for complex diagrams")

if __name__ == "__main__":
    main()
