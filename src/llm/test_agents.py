"""
Test script for the agentic components in Olkoa.

This script tests the RAG decision agent and K-value agent to ensure
they work correctly with the OpenRouter LLM API.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.llm.agents import RAGOrchestrator, get_rag_parameters, should_use_rag
import time


def test_agents():
    """Test the agentic components with various question types."""
    
    print("🧪 Testing Olkoa Agentic Components")
    print("=" * 60)
    
    # Test questions of different types
    test_questions = [
        # Questions that should need RAG
        ("What did Marie say about the project?", True),
        ("When is the next meeting scheduled?", True),
        ("Who sent emails about budget this month?", True),
        ("Summarize all discussions about the new product launch", True),
        ("What are the pending tasks mentioned in recent emails?", True),
        
        # Questions that should NOT need RAG
        ("How do I write a good email?", False),
        ("What is Python programming?", False),
        ("What are the benefits of remote work?", False),
        ("How to improve communication skills?", False),
        ("What is artificial intelligence?", False),
    ]
    
    orchestrator = RAGOrchestrator(model="openai/gpt-4o-mini")
    
    for i, (question, expected_rag) in enumerate(test_questions, 1):
        print(f"\n🔍 Test {i}: {question}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            
            # Test the orchestrator
            decision = orchestrator.analyze_question(question, max_k=15)
            
            # Test the convenience function
            needs_rag, k_value = should_use_rag(question)
            
            # Test the comprehensive function
            params = get_rag_parameters(question, max_k=15)
            
            elapsed = time.time() - start_time
            
            print(f"⏱️  Time: {elapsed:.2f}s")
            print(f"🤖 Agent Decision:")
            print(f"   - RAG Needed: {decision.needs_rag} (expected: {expected_rag})")
            print(f"   - K Value: {decision.k_value}")
            print(f"   - Confidence: {decision.confidence:.2f}")
            print(f"   - Reasoning: {decision.reasoning}")
            
            # Verify consistency
            assert decision.needs_rag == needs_rag, "Inconsistent RAG decision"
            assert decision.k_value == k_value, "Inconsistent K value"
            assert decision.needs_rag == params["needs_rag"], "Inconsistent parameters"
            
            # Check if expectation matches
            if decision.needs_rag == expected_rag:
                print("✅ Expectation met!")
            else:
                print(f"⚠️  Unexpected result (expected RAG={expected_rag})")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Agent testing complete!")


def test_k_value_logic():
    """Test the K-value determination logic specifically."""
    
    print("\n🎯 Testing K-Value Logic")
    print("=" * 40)
    
    # Questions that should get different k values
    k_test_cases = [
        ("What did John say?", "low", 3, 6),  # Simple, specific
        ("Summarize project discussions", "high", 8, 15),  # Complex, comprehensive
        ("Who are the stakeholders?", "medium", 6, 10),  # Moderate complexity
        ("When is the meeting?", "low", 3, 6),  # Simple, specific
        ("Analyze all feedback on the proposal", "high", 10, 15),  # Very complex
    ]
    
    orchestrator = RAGOrchestrator(model="openai/gpt-4o-mini")
    
    for question, complexity, min_expected, max_expected in k_test_cases:
        print(f"\n📊 Question: {question}")
        print(f"   Expected complexity: {complexity} (k={min_expected}-{max_expected})")
        
        try:
            decision = orchestrator.analyze_question(question, max_k=15)
            
            if decision.needs_rag:
                k_value = decision.k_value
                print(f"   Actual k: {k_value}")
                
                if min_expected <= k_value <= max_expected:
                    print("   ✅ K value in expected range")
                else:
                    print(f"   ⚠️ K value outside expected range")
            else:
                print("   ℹ️ RAG not needed for this question")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


def test_edge_cases():
    """Test edge cases and error handling."""
    
    print("\n🧪 Testing Edge Cases")
    print("=" * 30)
    
    edge_cases = [
        "",  # Empty string
        "?",  # Single character
        "a" * 500,  # Very long string
        "Email email EMAIL",  # Repetitive keywords
        "What? When? Who? How?",  # Multiple questions
    ]
    
    orchestrator = RAGOrchestrator(model="openai/gpt-4o-mini")
    
    for i, question in enumerate(edge_cases, 1):
        print(f"\n🔍 Edge Case {i}: '{question[:50]}{'...' if len(question) > 50 else ''}'")
        
        try:
            decision = orchestrator.analyze_question(question)
            print(f"   ✅ Handled successfully")
            print(f"   RAG: {decision.needs_rag}, K: {decision.k_value}, Confidence: {decision.confidence:.2f}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


if __name__ == "__main__":
    try:
        # Test the agents
        test_agents()
        
        # Test K-value logic
        test_k_value_logic()
        
        # Test edge cases
        test_edge_cases()
        
        print("\n🎉 All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
