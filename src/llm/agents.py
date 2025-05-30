"""
Agentic components for the Okloa RAG system.

This module implements intelligent agents that determine:
1. Whether RAG is needed to answer a user question
2. The optimal 'k' value for document retrieval

The agents use the existing OpenRouter LLM API to make decisions with custom prompts.
"""

import json
import re
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from .openrouter import openrouter_llm_api_call


@dataclass
class AgentDecision:
    """Data class to hold agent decision results."""
    needs_rag: bool
    k_value: int
    reasoning: str
    confidence: float


class RAGDecisionAgent:
    """
    Agent that determines whether a user question requires RAG search 
    through the email archives or can be answered by the LLM alone.
    """
    
    def __init__(self, model: str = "openai/gpt-4.1-mini"):
        """
        Initialize the RAG Decision Agent.
        
        Args:
            model: The LLM model to use for decision making
        """
        self.model = model
        self.system_prompt = """You are a specialized AI agent that determines whether a user question requires searching through email archives (RAG) or can be answered directly.

Your task is to analyze user questions and decide if they:
1. NEED RAG: Questions about specific emails, people, events, dates, projects, or information that would be found in email archives
2. DON'T NEED RAG: General knowledge questions, how-to questions, definitions, or questions unrelated to the specific email archives

You must respond with a valid JSON object in this exact format:
{
    "needs_rag": true/false,
    "reasoning": "Brief explanation of your decision",
    "confidence": 0.0-1.0
}

Examples:
- "What did Marie say about the project?" → needs_rag: true (specific person/content)
- "When is the next meeting?" → needs_rag: true (specific event in emails)
- "How do I write a good email?" → needs_rag: false (general knowledge)
- "What is Python programming?" → needs_rag: false (general knowledge)
- "Who sent emails about budget?" → needs_rag: true (specific email content)
- "What are the benefits of remote work?" → needs_rag: false (general topic)

Be decisive and confident in your analysis."""

    def decide(self, user_question: str) -> Dict[str, Any]:
        """
        Determine if the user question needs RAG search.
        
        Args:
            user_question: The user's question
            
        Returns:
            Dictionary with decision, reasoning, and confidence
        """
        print(f"🤖 RAG Decision Agent: Analyzing question: '{user_question}'")
        
        user_prompt = f"""Analyze this user question and determine if it requires searching through email archives:

Question: "{user_question}"

Consider:
- Does it ask about specific people, emails, events, or content that would be in email archives?
- Is it asking about general knowledge that doesn't require email search?
- Is it asking about specific dates, meetings, projects, or communications?

Respond with valid JSON only."""
        
        try:
            response = openrouter_llm_api_call(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                model=self.model
            )
            
            # Extract JSON from response
            decision_data = self._parse_json_response(response)
            
            print(f"🤖 RAG Decision Agent: Decision = {decision_data}")
            return decision_data
            
        except Exception as e:
            print(f"❌ RAG Decision Agent error: {e}")
            # Fallback: assume RAG is needed if uncertain
            return {
                "needs_rag": True,
                "reasoning": f"Error in decision making: {str(e)}. Defaulting to RAG search.",
                "confidence": 0.5
            }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from the LLM, handling various formats.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Parsed JSON data
        """
        try:
            # Try to parse directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or other formatting
            json_match = re.search(r'\{[^}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback parsing with regex for key values
            needs_rag = "true" in response.lower() if "needs_rag" in response.lower() else True
            
            # Extract reasoning if possible
            reasoning_match = re.search(r'"reasoning":\s*"([^"]*)"', response)
            reasoning = reasoning_match.group(1) if reasoning_match else "Could not parse reasoning"
            
            # Extract confidence if possible
            confidence_match = re.search(r'"confidence":\s*([0-9.]+)', response)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.7
            
            return {
                "needs_rag": needs_rag,
                "reasoning": reasoning,
                "confidence": confidence
            }


class KValueAgent:
    """
    Agent that determines the optimal 'k' value (number of documents to retrieve)
    based on the user question and context.
    """
    
    def __init__(self, model: str = "openai/gpt-4.1-mini"):
        """
        Initialize the K-Value Agent.
        
        Args:
            model: The LLM model to use for decision making
        """
        self.model = model
        self.system_prompt = """You are a specialized AI agent that determines the optimal number of email documents (k) to retrieve for answering user questions.

Your task is to analyze user questions and determine how many emails should be retrieved:

K VALUE GUIDELINES:
- k=5-12: Simple, specific questions about one topic/person/event
  - "Les mails font-ils mention de recrutements ?"
  - "Y a-t-il des échanges concernant un incident technique précis ?"

- k=13-20: Moderate complexity questions that might need multiple perspectives
  - "Des mails concernent-ils des discussions autour du télétravail ?"
  - "Quels sujets sont évoqués dans les échanges liés à la direction financière ?"

- k=21-30: Complex questions requiring comprehensive information
  - "Résume les conversations entre Claire et Thomas sur le dernier trimestre."
  - "Quels sont les points évoqués dans les discussions autour de la stratégie 2025 ?"

- k=50-100: Very complex questions needing extensive context or analysis
  - "Peux-tu faire un résumé de l’activité de cette boîte mail sur les 12 derniers mois ?"
  - "Quels grands thèmes émergent dans l’ensemble des échanges depuis janvier 2023 ?"

QUESTION TYPE EXAMPLES:
- "What did John say about X?" → k=3-5 (specific person/topic)
- "When is the meeting?" → k=3-5 (specific event)
- "Summary of project discussions" → k=8-12 (comprehensive overview)
- "Who are all the stakeholders in project X?" → k=10-15 (broad information gathering)
- "What are the different opinions about Y?" → k=8-12 (multiple perspectives)

You must respond with a valid JSON object in this exact format:
{
    "k_value": integer_between_3_and_15,
    "reasoning": "Brief explanation of why this k value is appropriate",
    "confidence": 0.0-1.0
}

Be practical and consider that more documents provide more context but also more noise."""

    def determine_k(self, user_question: str, max_k: int = 100) -> Dict[str, Any]:
        """
        Determine the optimal k value for the user question.
        
        Args:
            user_question: The user's question
            max_k: Maximum allowed k value
            
        Returns:
            Dictionary with k_value, reasoning, and confidence
        """
        print(f"🎯 K-Value Agent: Determining k for question: '{user_question}'")
        
        user_prompt = f"""Analyze this user question and determine the optimal number of email documents (k) to retrieve:

Question: "{user_question}"

Consider:
- Specificity: Is this asking about one specific thing or requiring broad information?
- Complexity: How much context is needed to answer well?
- Scope: Is this about one person/event or multiple entities?

Maximum allowed k: {max_k}
Minimum k: 5

Respond with valid JSON only."""
        
        try:
            response = openrouter_llm_api_call(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                model=self.model
            )
            
            # Extract JSON from response
            k_data = self._parse_json_response(response, max_k)
            
            print(f"🎯 K-Value Agent: Decision = {k_data}")
            return k_data
            
        except Exception as e:
            print(f"❌ K-Value Agent error: {e}")
            # Fallback: use moderate k value
            return {
                "k_value": 7,
                "reasoning": f"Error in k determination: {str(e)}. Using default k=7.",
                "confidence": 0.5
            }

    def _parse_json_response(self, response: str, max_k: int) -> Dict[str, Any]:
        """
        Parse JSON response and validate k value.
        
        Args:
            response: Raw response from LLM
            max_k: Maximum allowed k value
            
        Returns:
            Parsed and validated JSON data
        """
        try:
            # Try to parse directly
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or other formatting
            json_match = re.search(r'\{[^}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    data = self._regex_parse_k_response(response)
            else:
                data = self._regex_parse_k_response(response)
        
        # Validate and constrain k_value
        k_value = data.get("k_value", 7)
        if not isinstance(k_value, int):
            k_value = 7
        k_value = max(3, min(max_k, k_value))  # Constrain between 3 and max_k
        
        return {
            "k_value": k_value,
            "reasoning": data.get("reasoning", "K value determined"),
            "confidence": data.get("confidence", 0.7)
        }

    def _regex_parse_k_response(self, response: str) -> Dict[str, Any]:
        """
        Fallback parsing using regex when JSON parsing fails.
        
        Args:
            response: Raw response string
            
        Returns:
            Parsed data dictionary
        """
        # Try to extract k_value
        k_match = re.search(r'"k_value":\s*(\d+)', response)
        k_value = int(k_match.group(1)) if k_match else 7
        
        # Extract reasoning if possible
        reasoning_match = re.search(r'"reasoning":\s*"([^"]*)"', response)
        reasoning = reasoning_match.group(1) if reasoning_match else "Could not parse reasoning"
        
        # Extract confidence if possible
        confidence_match = re.search(r'"confidence":\s*([0-9.]+)', response)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7
        
        return {
            "k_value": k_value,
            "reasoning": reasoning,
            "confidence": confidence
        }


class RAGOrchestrator:
    """
    Orchestrator that combines both agents to make comprehensive decisions
    about RAG usage and parameters.
    """
    
    def __init__(self, model: str = "openai/gpt-4.1-mini"):
        """
        Initialize the RAG Orchestrator with both agents.
        
        Args:
            model: The LLM model to use for both agents
        """
        self.rag_decision_agent = RAGDecisionAgent(model=model)
        self.k_value_agent = KValueAgent(model=model)
        
    def analyze_question(self, user_question: str, max_k: int = 15) -> AgentDecision:
        """
        Analyze a user question and return comprehensive RAG decisions.
        
        Args:
            user_question: The user's question
            max_k: Maximum allowed k value
            
        Returns:
            AgentDecision object with all decisions
        """
        print(f"🧠 RAG Orchestrator: Analyzing question: '{user_question}'")
        
        # Step 1: Determine if RAG is needed
        rag_decision = self.rag_decision_agent.decide(user_question)
        needs_rag = rag_decision["needs_rag"]
        
        print(f"🧠 RAG Orchestrator: RAG needed = {needs_rag}")
        
        # Step 2: If RAG is needed, determine k value
        k_value = 0
        k_reasoning = "RAG not needed"
        k_confidence = 1.0
        
        if needs_rag:
            k_decision = self.k_value_agent.determine_k(user_question, max_k)
            k_value = k_decision["k_value"]
            k_reasoning = k_decision["reasoning"]
            k_confidence = k_decision["confidence"]
            
            print(f"🧠 RAG Orchestrator: k value = {k_value}")
        
        # Combine reasoning and confidence
        combined_reasoning = f"RAG Decision: {rag_decision['reasoning']}. K Value: {k_reasoning}"
        combined_confidence = (rag_decision["confidence"] + k_confidence) / 2
        
        result = AgentDecision(
            needs_rag=needs_rag,
            k_value=k_value,
            reasoning=combined_reasoning,
            confidence=combined_confidence
        )
        
        print(f"🧠 RAG Orchestrator: Final decision = {result}")
        return result

    def get_decision_summary(self, decision: AgentDecision) -> str:
        """
        Get a human-readable summary of the agent decision.
        
        Args:
            decision: AgentDecision object
            
        Returns:
            Formatted summary string
        """
        if decision.needs_rag:
            return f"✅ RAG Required | k={decision.k_value} | Confidence: {decision.confidence:.2f}"
        else:
            return f"❌ RAG Not Needed | LLM Only | Confidence: {decision.confidence:.2f}"


# Convenience functions for easy integration
def should_use_rag(user_question: str, model: str = "openai/gpt-4.1-mini") -> Tuple[bool, int]:
    """
    Simple function to determine if RAG should be used and with what k value.
    
    Args:
        user_question: The user's question
        model: LLM model to use for decision making
        
    Returns:
        Tuple of (needs_rag, k_value)
    """
    orchestrator = RAGOrchestrator(model=model)
    decision = orchestrator.analyze_question(user_question)
    return decision.needs_rag, decision.k_value


def get_rag_parameters(user_question: str, model: str = "openai/gpt-4.1-mini", max_k: int = 15) -> Dict[str, Any]:
    """
    Get comprehensive RAG parameters for a user question.
    
    Args:
        user_question: The user's question
        model: LLM model to use for decision making
        max_k: Maximum allowed k value
        
    Returns:
        Dictionary with RAG parameters and metadata
    """
    orchestrator = RAGOrchestrator(model=model)
    decision = orchestrator.analyze_question(user_question, max_k)
    
    return {
        "needs_rag": decision.needs_rag,
        "k_value": decision.k_value,
        "reasoning": decision.reasoning,
        "confidence": decision.confidence,
        "summary": orchestrator.get_decision_summary(decision),
        "user_question": user_question
    }


if __name__ == "__main__":
    # Test the agents
    test_questions = [
        "What did Marie say about the project?",
        "How do I write a good email?",
        "When is the next meeting?",
        "What is Python programming?",
        "Who sent emails about budget this month?",
        "Summarize all discussions about the new product launch"
    ]
    
    orchestrator = RAGOrchestrator()
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Testing: {question}")
        print('='*60)
        
        decision = orchestrator.analyze_question(question)
        summary = orchestrator.get_decision_summary(decision)
        
        print(f"Result: {summary}")
        print(f"Reasoning: {decision.reasoning}")
        print(f"Confidence: {decision.confidence:.2f}")
