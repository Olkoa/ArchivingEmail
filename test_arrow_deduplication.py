"""
Test to verify no duplicate arrows in Mermaid diagrams
"""

import sys
import os

# Add the necessary paths
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.visualization.mail_directory_tree import (
    generate_mermaid_folder_graph,
    get_sample_folder_data
)

def test_no_duplicate_arrows():
    """Test that there are no duplicate arrows in the generated graph."""
    print("🧪 Testing for duplicate arrows...")
    
    # Get sample data
    df = get_sample_folder_data()
    
    # Generate graph
    mermaid_code = generate_mermaid_folder_graph(
        df, 
        folder_column='folders', 
        count_column='count'
    )
    
    # Extract arrow lines (relationships)
    lines = mermaid_code.split('\n')
    arrow_lines = [line for line in lines if '-->' in line]
    
    print(f"\n📊 Found {len(arrow_lines)} arrow relationships:")
    for arrow in sorted(arrow_lines):
        print(f"   {arrow.strip()}")
    
    # Check for duplicates
    unique_arrows = set(arrow_lines)
    
    print(f"\n✅ Unique arrows: {len(unique_arrows)}")
    print(f"📊 Total arrows: {len(arrow_lines)}")
    
    if len(unique_arrows) == len(arrow_lines):
        print("🎉 SUCCESS: No duplicate arrows found!")
        return True
    else:
        print(f"❌ PROBLEM: Found {len(arrow_lines) - len(unique_arrows)} duplicate arrows")
        
        # Show duplicates
        arrow_counts = {}
        for arrow in arrow_lines:
            arrow_counts[arrow] = arrow_counts.get(arrow, 0) + 1
        
        duplicates = {arrow: count for arrow, count in arrow_counts.items() if count > 1}
        if duplicates:
            print("\n🔍 Duplicate arrows found:")
            for arrow, count in duplicates.items():
                print(f"   {arrow.strip()} (appears {count} times)")
        
        return False

def test_relationships_make_sense():
    """Test that the relationships are logical."""
    print("\n🔍 Testing relationship logic...")
    
    # Get sample data
    df = get_sample_folder_data()
    
    # Generate graph
    mermaid_code = generate_mermaid_folder_graph(
        df, 
        folder_column='folders', 
        count_column='count'
    )
    
    # Extract arrow lines
    lines = mermaid_code.split('\n')
    arrow_lines = [line.strip() for line in lines if '-->' in line]
    
    print(f"\nAnalyzing {len(arrow_lines)} relationships:")
    
    valid_relationships = 0
    for arrow in sorted(arrow_lines):
        # Parse the relationship
        parts = arrow.split(' --> ')
        if len(parts) == 2:
            parent = parts[0].strip()
            child = parts[1].strip()
            print(f"   ✅ {parent} → {child}")
            valid_relationships += 1
        else:
            print(f"   ❌ Invalid format: {arrow}")
    
    print(f"\n📊 Valid relationships: {valid_relationships}/{len(arrow_lines)}")
    return valid_relationships == len(arrow_lines)

def test_different_scenarios():
    """Test with different data scenarios."""
    print("\n🎯 Testing different scenarios...")
    
    # Scenario 1: Simple structure
    simple_data = {
        "root/inbox": 100,
        "root/sent": 50,
        "root/inbox/work": 30,
        "root/inbox/personal": 20
    }
    
    df_simple = pd.DataFrame({'folders': list(simple_data.keys()), 'count': list(simple_data.values())})
    
    graph_simple = generate_mermaid_folder_graph(df_simple, folder_column='folders', count_column='count')
    arrows_simple = [line for line in graph_simple.split('\n') if '-->' in line]
    unique_simple = set(arrows_simple)
    
    print(f"📁 Simple structure: {len(arrows_simple)} arrows, {len(unique_simple)} unique")
    
    # Scenario 2: Complex structure with multiple levels
    complex_data = {
        "user/inbox": 1000,
        "user/inbox/project1": 100,
        "user/inbox/project1/docs": 50,
        "user/inbox/project2": 80,
        "user/sent": 500,
        "user/sent/project1": 30,
        "user/archive": 200
    }
    
    df_complex = pd.DataFrame({'folders': list(complex_data.keys()), 'count': list(complex_data.values())})
    
    graph_complex = generate_mermaid_folder_graph(df_complex, folder_column='folders', count_column='count')
    arrows_complex = [line for line in graph_complex.split('\n') if '-->' in line]
    unique_complex = set(arrows_complex)
    
    print(f"📁 Complex structure: {len(arrows_complex)} arrows, {len(unique_complex)} unique")
    
    # Both should have no duplicates
    return len(arrows_simple) == len(unique_simple) and len(arrows_complex) == len(unique_complex)

def main():
    """Run all tests."""
    print("🧪 Testing Arrow Deduplication in Mermaid Graphs")
    print("=" * 50)
    
    # Import pandas here since we need it for the test
    import pandas as pd
    globals()['pd'] = pd
    
    tests = [
        test_no_duplicate_arrows,
        test_relationships_make_sense, 
        test_different_scenarios
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! No duplicate arrows found.")
    else:
        print("\n⚠️ Some tests failed. Please check the output above.")
    
    print("\n💡 The fix ensures each relationship appears only once in the Mermaid diagram.")

if __name__ == "__main__":
    main()
