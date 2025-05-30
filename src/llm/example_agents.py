"""
Example demonstration of the Okloa agentic components.

This script shows how to use the agents in your own applications
and demonstrates the decision-making process.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.llm.agents import RAGOrchestrator, get_rag_parameters, should_use_rag


def demonstrate_agents():
    """Demonstrate the agentic components with example questions."""
    
    print("🎯 Okloa Agentic Components Demonstration")
    print("=" * 50)
    
    # Example questions
    examples = [
        "What did Marie say about the new project timeline?",
        "How do I write effective emails?",
        "Summarize all discussions about the budget approval",
        "What is machine learning?",
        "Who are the key stakeholders mentioned in recent emails?"
    ]
    
    # Initialize the orchestrator
    orchestrator = RAGOrchestrator(model="openai/gpt-4o-mini")
    
    for i, question in enumerate(examples, 1):
        print(f"\n🔍 Example {i}: {question}")
        print("-" * 40)
        
        # Method 1: Using the orchestrator (recommended)
        decision = orchestrator.analyze_question(question, max_k=15)
        
        print(f"🤖 Agent Decision:")
        print(f"   RAG Needed: {decision.needs_rag}")
        if decision.needs_rag:
            print(f"   K Value: {decision.k_value}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Reasoning: {decision.reasoning}")
        
        # Show what would happen next
        if decision.needs_rag:
            print(f"   ➡️  Next: Search {decision.k_value} emails → LLM processing")
        else:
            print(f"   ➡️  Next: Direct LLM response (no RAG search)")
        
        # Method 2: Using convenience functions
        needs_rag, k_value = should_use_rag(question)
        print(f"   🔧 Quick check: RAG={needs_rag}, k={k_value}")


def integration_example():
    """Show how to integrate agents into a chatbot workflow."""
    
    print("\n\n🔄 Integration Example: Chat Workflow")
    print("=" * 45)
    
    def process_user_question(question: str) -> dict:
        """
        Example function showing how to integrate agents into a chat system.
        """
        print(f"\n📝 Processing: '{question}'")
        
        # Step 1: Agent decision
        print("   🤖 Step 1: Agent analysis...")
        params = get_rag_parameters(question, max_k=12)
        
        # Step 2: Conditional processing
        if params["needs_rag"]:
            print(f"   🔍 Step 2: RAG search (k={params['k_value']})...")
            # In real implementation: retrieved_emails = search_with_colbert(...)
            print(f"   📧 Step 3: Found {params['k_value']} relevant emails")
            print(f"   🧠 Step 4: LLM processing with email context...")
            result_type = "RAG-enhanced response"
        else:
            print(f"   🧠 Step 2: Direct LLM response...")
            result_type = "Direct LLM response"
        
        return {
            "question": question,
            "agent_decision": params,
            "result_type": result_type,
            "processing_path": "agent -> rag -> llm" if params["needs_rag"] else "agent -> llm"
        }
    
    # Example questions
    test_questions = [
        "What meetings are scheduled this week?",
        "How to improve team communication?",
        "What did the CEO say about the quarterly results?"
    ]
    
    results = []
    for question in test_questions:
        result = process_user_question(question)
        results.append(result)
        print(f"   ✅ Result: {result['result_type']}")
    
    # Summary
    print(f"\n📊 Summary:")
    rag_count = sum(1 for r in results if r['agent_decision']['needs_rag'])
    direct_count = len(results) - rag_count
    print(f"   RAG responses: {rag_count}")
    print(f"   Direct responses: {direct_count}")
    print(f"   Efficiency gain: {direct_count}/{len(results)} questions avoided RAG search")


def custom_agent_example():
    """Show how to customize agent behavior."""
    
    print("\n\n⚙️ Customization Example")
    print("=" * 30)
    
    # Custom model configuration
    fast_orchestrator = RAGOrchestrator(model="openai/gpt-4o-mini")
    accurate_orchestrator = RAGOrchestrator(model="openai/gpt-4o")
    
    question = "Analyze the feedback from all stakeholders about the new product"
    
    print(f"📝 Question: {question}")
    print("\n🏃‍♂️ Fast Model (gpt-4o-mini):")
    fast_decision = fast_orchestrator.analyze_question(question, max_k=15)
    print(f"   RAG: {fast_decision.needs_rag}, K: {fast_decision.k_value}, Confidence: {fast_decision.confidence:.2f}")
    
    print("\n🎯 Accurate Model (gpt-4o):")
    accurate_decision = accurate_orchestrator.analyze_question(question, max_k=15)
    print(f"   RAG: {accurate_decision.needs_rag}, K: {accurate_decision.k_value}, Confidence: {accurate_decision.confidence:.2f}")
    
    # Compare decisions
    if fast_decision.needs_rag == accurate_decision.needs_rag:
        print("\n✅ Both models agree on RAG necessity")
    else:
        print("\n⚠️ Models disagree on RAG necessity")
    
    if fast_decision.needs_rag and accurate_decision.needs_rag:
        k_diff = abs(fast_decision.k_value - accurate_decision.k_value)
        if k_diff <= 2:
            print(f"✅ K values are close (difference: {k_diff})")
        else:
            print(f"⚠️ K values differ significantly (difference: {k_diff})")


def performance_comparison():
    """Compare performance with and without agents."""
    
    print("\n\n⚡ Performance Comparison")
    print("=" * 30)
    
    questions = [
        "What is Python?",  # Should not need RAG
        "When is the project deadline?",  # Should need RAG
        "How to write clean code?",  # Should not need RAG
        "What did John say about the budget?",  # Should need RAG
    ]
    
    print("📊 Without Agents (traditional approach):")
    print("   - All questions go through RAG search")
    print("   - Fixed k=10 for all questions")
    print(f"   - Total RAG searches: {len(questions)}")
    print(f"   - Total documents retrieved: {len(questions) * 10}")
    
    print("\n🤖 With Agents (intelligent approach):")
    orchestrator = RAGOrchestrator()
    
    total_rag_searches = 0
    total_documents = 0
    
    for question in questions:
        decision = orchestrator.analyze_question(question, max_k=15)
        if decision.needs_rag:
            total_rag_searches += 1
            total_documents += decision.k_value
            print(f"   - '{question[:30]}...' → RAG (k={decision.k_value})")
        else:
            print(f"   - '{question[:30]}...' → Direct LLM")
    
    print(f"\n📈 Results:")
    print(f"   - RAG searches: {total_rag_searches} (vs {len(questions)} without agents)")
    print(f"   - Documents retrieved: {total_documents} (vs {len(questions) * 10} without agents)")
    
    if total_rag_searches < len(questions):
        efficiency = (1 - total_rag_searches / len(questions)) * 100
        print(f"   - Efficiency gain: {efficiency:.1f}% fewer RAG searches")
    
    if total_documents < len(questions) * 10:
        doc_efficiency = (1 - total_documents / (len(questions) * 10)) * 100
        print(f"   - Document efficiency: {doc_efficiency:.1f}% fewer documents processed")


if __name__ == "__main__":
    try:
        # Main demonstration
        demonstrate_agents()
        
        # Integration example
        integration_example()
        
        # Customization example
        custom_agent_example()
        
        # Performance comparison
        performance_comparison()
        
        print("\n🎉 Demonstration complete!")
        print("\n💡 Key Takeaways:")
        print("   - Agents automatically determine RAG necessity")
        print("   - K values are optimized for question complexity")
        print("   - System is more efficient and cost-effective")
        print("   - Easy to integrate into existing workflows")
        print("   - Transparent decision-making with confidence scores")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demonstration interrupted")
    except Exception as e:
        print(f"\n💥 Error during demonstration: {str(e)}")
        print("\nPlease check your OpenRouter API configuration.")
