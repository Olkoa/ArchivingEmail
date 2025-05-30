# Agentic Components for Okloa RAG System

## Overview

The Okloa RAG system now includes intelligent agentic components that automatically determine:
1. **Whether RAG is needed** to answer a user question
2. **The optimal 'k' value** (number of documents to retrieve) for RAG search

This enhancement makes the system more efficient and user-friendly by automatically adapting to different types of questions.

## Architecture

```
User Question
     ↓
🤖 RAG Decision Agent
     ↓
[RAG Needed?] → No → Direct LLM Response
     ↓ Yes
🎯 K-Value Agent
     ↓
🔍 RAG Search (with optimal k)
     ↓
🧠 LLM Response Generation
     ↓
📧 Final Response with Sources
```

## Components

### 1. RAGDecisionAgent

**Purpose**: Determines if a question requires searching through email archives or can be answered directly by the LLM.

**Logic**:
- ✅ **NEEDS RAG**: Questions about specific emails, people, events, dates, projects, or information found in email archives
- ❌ **DOESN'T NEED RAG**: General knowledge questions, how-to questions, definitions, or questions unrelated to email archives

**Examples**:
```python
# Questions that NEED RAG
"What did Marie say about the project?"          → needs_rag: True
"When is the next meeting?"                      → needs_rag: True
"Who sent emails about budget?"                  → needs_rag: True

# Questions that DON'T NEED RAG
"How do I write a good email?"                   → needs_rag: False
"What is Python programming?"                    → needs_rag: False
"What are the benefits of remote work?"          → needs_rag: False
```

### 2. KValueAgent

**Purpose**: Determines the optimal number of emails (k) to retrieve for comprehensive answers.

**Guidelines**:
- **k=3-5**: Simple, specific questions about one topic/person/event
- **k=5-8**: Moderate complexity questions that might need multiple perspectives
- **k=8-12**: Complex questions requiring comprehensive information
- **k=12-15**: Very complex questions needing extensive context or analysis

**Examples**:
```python
"What did John say about X?"                     → k=3-5   (specific person/topic)
"When is the meeting?"                           → k=3-5   (specific event)
"Summary of project discussions"                 → k=8-12  (comprehensive overview)
"Who are all stakeholders in project X?"        → k=10-15 (broad information gathering)
"What are different opinions about Y?"           → k=8-12  (multiple perspectives)
```

### 3. RAGOrchestrator

**Purpose**: Combines both agents to make comprehensive decisions about RAG usage and parameters.

**Workflow**:
1. Analyze question with RAGDecisionAgent
2. If RAG needed, determine k value with KValueAgent
3. Return complete decision with reasoning and confidence scores

## Implementation Details

### File Structure
```
src/llm/
├── agents.py              # Main agentic components
├── openrouter.py          # LLM API calls (existing)
└── test_agents.py         # Test suite for agents

app/components/
└── chat_rag_component.py  # Updated with agent integration
```

### Key Features

#### 1. Tracing and Logging
The system includes comprehensive logging for debugging:
```python
print(f\"🤖 Agent > RAG > LLM: Analyzing question: '{user_question}'\")
print(f\"🤖 Agent decision: {rag_params}\")
print(f\"🔍 RAG search: Searching with k={final_k}\")
print(f\"✅ RAG search: Found {len(retrieved_emails)} emails\")
print(f\"🧠 LLM processing: Complete. Total time: {total_time:.2f}s\")
```

#### 2. Flexible Configuration
Users can:
- Enable/disable agent mode
- Set maximum k limits
- Choose different LLM models for agents
- View agent decisions and reasoning

#### 3. Error Handling
Robust fallback mechanisms:
- If agents fail, default to RAG with moderate k value
- JSON parsing with regex fallbacks
- Graceful degradation to manual mode

#### 4. Performance Tracking
Detailed timing information:
- Agent decision time
- RAG search time
- LLM processing time
- Total response time

## Usage

### In the Streamlit Interface

1. **Enable Agents**: Check \"Utiliser les agents intelligents\" in the sidebar
2. **Set Limits**: Configure maximum number of emails (5-20)
3. **Ask Questions**: The agents automatically determine RAG needs and k values
4. **View Decisions**: Expand \"Décision des agents\" to see reasoning

### Programmatic Usage

```python
from src.llm.agents import RAGOrchestrator, get_rag_parameters

# Quick decision
orchestrator = RAGOrchestrator()
decision = orchestrator.analyze_question(\"What did Marie say?\")

print(f\"RAG needed: {decision.needs_rag}\")
print(f\"K value: {decision.k_value}\")
print(f\"Confidence: {decision.confidence}\")

# Comprehensive parameters
params = get_rag_parameters(\"Summarize project discussions\", max_k=15)
```

### Testing

Run the test suite to verify agent functionality:
```bash
cd src/llm
python test_agents.py
```

The test suite covers:
- Basic agent decision accuracy
- K-value logic verification
- Edge case handling
- Error recovery

## Configuration

### Environment Variables
Agents use the same OpenRouter configuration as the main system:
```env
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=your_openrouter_key
```

### Model Selection
Recommended models for agents:
- **Fast & Cost-effective**: `openai/gpt-4o-mini`
- **High Accuracy**: `openai/gpt-4o`
- **Alternative**: `anthropic/claude-3.5-sonnet`

## Benefits

### 1. Efficiency
- No unnecessary RAG searches for general questions
- Optimal k values reduce noise and improve relevance
- Faster responses for non-RAG questions

### 2. Better User Experience
- Automatic adaptation to question types
- Transparent decision-making process
- Consistent high-quality responses

### 3. Cost Optimization
- Reduced RAG computations for irrelevant questions
- Optimized document retrieval counts
- Efficient LLM usage

### 4. Maintainability
- Modular agent design
- Easy to extend and modify
- Comprehensive testing suite

## Future Enhancements

### Planned Improvements
1. **Learning from User Feedback**: Adapt agent decisions based on user satisfaction
2. **Dynamic K Adjustment**: Modify k based on search result quality
3. **Context Awareness**: Consider conversation history in decisions
4. **Custom Agent Prompts**: Allow user-defined decision criteria
5. **Performance Analytics**: Track agent accuracy and optimize prompts

### Extension Points
- Additional specialized agents (e.g., sentiment analysis, urgency detection)
- Integration with other search backends
- Multi-language support for agent reasoning
- Advanced confidence scoring mechanisms

## Troubleshooting

### Common Issues

**Agent not making decisions**:
- Check OpenRouter API configuration
- Verify model availability
- Review agent prompt responses

**Inconsistent k values**:
- Agents may interpret complexity differently
- Consider adjusting k value guidelines
- Check for edge cases in question phrasing

**Performance issues**:
- Agent decisions add ~1-3 seconds overhead
- Consider caching for repeated questions
- Use faster models for agent decisions

### Debug Mode
Enable detailed logging by setting environment variable:
```bash
export OKLOA_DEBUG=true
```

This provides verbose output for agent decision-making processes.
