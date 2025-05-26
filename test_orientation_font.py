"""
Test script for the new orientation and font size features
"""

import sys
import os
import pandas as pd

# Add the necessary paths
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.visualization.mail_directory_tree import (
    generate_mermaid_folder_graph,
    get_sample_folder_data
)

def test_orientation_options():
    """Test different orientation options."""
    print("🧪 Testing orientation options...")
    
    # Get sample data
    df = get_sample_folder_data()
    
    # Test vertical orientation
    print("\n📊 Testing vertical orientation...")
    vertical_graph = generate_mermaid_folder_graph(
        df, 
        folder_column='folders', 
        count_column='count',
        orientation='vertical'
    )
    
    if "graph TD" in vertical_graph:
        print("✅ Vertical orientation works (graph TD)")
    else:
        print("❌ Vertical orientation failed")
    
    # Test horizontal orientation
    print("\n📈 Testing horizontal orientation...")
    horizontal_graph = generate_mermaid_folder_graph(
        df, 
        folder_column='folders', 
        count_column='count',
        orientation='horizontal'
    )
    
    if "graph LR" in horizontal_graph:
        print("✅ Horizontal orientation works (graph LR)")
    else:
        print("❌ Horizontal orientation failed")
    
    return vertical_graph, horizontal_graph

def test_font_size_options():
    """Test different font size options."""
    print("\n🔤 Testing font size options...")
    
    # Get sample data
    df = get_sample_folder_data()
    
    font_sizes = ['small', 'normal', 'large', 'xlarge']
    expected_sizes = ['10px', '12px', '14px', '16px']
    
    results = {}
    
    for font_size, expected_px in zip(font_sizes, expected_sizes):
        print(f"\n   Testing {font_size} ({expected_px})...")
        
        graph = generate_mermaid_folder_graph(
            df, 
            folder_column='folders', 
            count_column='count',
            font_size=font_size
        )
        
        if f"font-size:{expected_px}" in graph:
            print(f"   ✅ {font_size} size works ({expected_px})")
            results[font_size] = True
        else:
            print(f"   ❌ {font_size} size failed (expected {expected_px})")
            results[font_size] = False
        
        # Store for return
        results[f"{font_size}_graph"] = graph
    
    return results

def test_combined_options():
    """Test combining orientation and font size options."""
    print("\n🎨 Testing combined options...")
    
    # Get sample data
    df = get_sample_folder_data()
    
    # Test horizontal + large font
    print("\n   Testing horizontal + large font...")
    combined_graph = generate_mermaid_folder_graph(
        df,
        folder_column='folders',
        count_column='count',
        orientation='horizontal',
        font_size='large'
    )
    
    has_horizontal = "graph LR" in combined_graph
    has_large_font = "font-size:14px" in combined_graph
    
    if has_horizontal and has_large_font:
        print("   ✅ Combined options work (horizontal + large)")
    else:
        print(f"   ❌ Combined options failed (horizontal: {has_horizontal}, large font: {has_large_font})")
    
    return combined_graph

def save_test_examples():
    """Save example graphs with different options."""
    print("\n💾 Saving test examples...")
    
    # Get sample data
    df = get_sample_folder_data()
    
    # Create examples directory
    examples_dir = os.path.join(project_root, "examples")
    os.makedirs(examples_dir, exist_ok=True)
    
    # Generate different combinations
    combinations = [
        ("vertical", "normal", "vertical_normal"),
        ("horizontal", "normal", "horizontal_normal"),
        ("vertical", "large", "vertical_large"),
        ("horizontal", "small", "horizontal_small"),
        ("vertical", "xlarge", "vertical_xlarge")
    ]
    
    for orientation, font_size, filename in combinations:
        print(f"   Generating {filename}...")
        
        graph = generate_mermaid_folder_graph(
            df,
            folder_column='folders',
            count_column='count',
            orientation=orientation,
            font_size=font_size
        )
        
        file_path = os.path.join(examples_dir, f"mail_structure_{filename}.mermaid")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(graph)
            print(f"   ✅ Saved: {file_path}")
        except Exception as e:
            print(f"   ❌ Failed to save {filename}: {e}")

def main():
    """Run all tests."""
    print("🧪 Testing New Orientation and Font Size Features")
    print("=" * 55)
    
    # Test orientation
    vertical_graph, horizontal_graph = test_orientation_options()
    
    # Test font sizes
    font_results = test_font_size_options()
    
    # Test combined options
    combined_graph = test_combined_options()
    
    # Save examples
    save_test_examples()
    
    # Summary
    print("\n" + "=" * 55)
    print("📊 Test Summary:")
    
    # Check orientation results
    vertical_ok = "graph TD" in vertical_graph
    horizontal_ok = "graph LR" in horizontal_graph
    print(f"   📊 Vertical orientation: {'✅' if vertical_ok else '❌'}")
    print(f"   📈 Horizontal orientation: {'✅' if horizontal_ok else '❌'}")
    
    # Check font size results
    font_success = sum(1 for k, v in font_results.items() if k in ['small', 'normal', 'large', 'xlarge'] and v)
    print(f"   🔤 Font sizes working: {font_success}/4")
    
    # Check combined
    combined_ok = "graph LR" in combined_graph and "font-size:14px" in combined_graph
    print(f"   🎨 Combined options: {'✅' if combined_ok else '❌'}")
    
    print(f"\n📁 Example files saved in: {os.path.join(project_root, 'examples')}")
    
    # Usage recommendations
    print("\n💡 Usage Recommendations:")
    print("   📊 Vertical: Best for deep folder hierarchies")
    print("   📈 Horizontal: Best for wide structures and presentations")
    print("   🔤 Small font: For complex structures with many folders")
    print("   🔤 Large font: For presentations and accessibility")
    
    print("\n🚀 Ready to test in the app!")
    print("   Go to: Visualization > Structure de la boîte mail")
    print("   Try different combinations of orientation and font size")

if __name__ == "__main__":
    main()
