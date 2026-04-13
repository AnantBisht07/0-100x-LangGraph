# WEEK 15 - SUNDAY: External APIs & Parallel Branching Flows

## Overview

This project combines two advanced LangGraph patterns:

1. **External API Integration**: Real News API calls via ToolNode
2. **Parallel Branching Flows**: Multiple summarizers run simultaneously

### What Makes This Special

- **Single API Call**: News fetched ONCE, results shared via state
- **True Parallelism**: Three summarizers run simultaneously (not sequentially)
- **Multi-Perspective Analysis**: Same data, three different analytical lenses
- **Efficient Design**: No redundant API calls or recomputation

## Architecture

```
START
  ↓
qna_agent (reformulate query)
  ↓
news_search_agent (decide to call tool)
  ↓
news_tool_node (fetch from News API - ONCE)
  ↓
┌─────────────────────────────────────────────┐
│ PARALLEL EXECUTION (simultaneous)           │
│                                             │
│  ├─ summarizer_key_facts                    │
│  ├─ summarizer_trends_themes                │
│  └─ summarizer_implications_impact          │
└─────────────────────────────────────────────┘
  ↓
merge_summaries (consolidate all perspectives)
  ↓
END
```

## Node Responsibilities

### Sequential Setup (1 → 2 → 3)

1. **qna_agent**: Extracts clean research query from user question
2. **news_search_agent**: Decides to use the search tool
3. **news_tool_node**: Executes News API call (ToolNode wrapper)

### Parallel Processing (4a, 4b, 4c - simultaneous)

4a. **summarizer_key_facts**: Extracts core facts and events
4b. **summarizer_trends_themes**: Identifies patterns and themes
4c. **summarizer_implications_impact**: Analyzes future implications

### Merge Point (5)

5. **merge_summaries**: Combines all three analyses into final research brief

## Key Concepts

### 1. Parallel Execution

```python
# From news_tool_node, three edges create parallel execution
workflow.add_edge("news_tool_node", "summarizer_key_facts")
workflow.add_edge("news_tool_node", "summarizer_trends_themes")
workflow.add_edge("news_tool_node", "summarizer_implications_impact")

# All three summarizers start simultaneously
# No dependencies between them = true parallelism
```

**How it works**:
- All three nodes receive the same trigger (news_tool_node completion)
- No dependencies between summarizers
- LangGraph executes them in parallel
- Continues when ALL complete (barrier synchronization)

### 2. State Sharing (No Redundant API Calls)

```python
# API called ONCE in news_tool_node
# Results stored in state["messages"]
# All three summarizers READ from state
# No re-fetching, no duplication
```

**Benefits**:
- Faster execution (no redundant API calls)
- Cost-effective (one API call instead of three)
- Consistent data (all summarizers analyze same articles)

### 3. ToolNode Pattern

```python
@tool
def search_news(query: str) -> str:
    """Tool implementation"""
    # Calls News API
    return results

# Wrapped in ToolNode for LangGraph
workflow.add_node("news_tool_node", ToolNode([search_news]))
```

**Why ToolNode?**
- Separates tool execution from agent decision
- Automatic error handling
- Proper state management
- Single execution point (no accidental duplication)

### 4. Merge Pattern

```python
# All three summarizers converge to merge node
workflow.add_edge("summarizer_key_facts", "merge_summaries")
workflow.add_edge("summarizer_trends_themes", "merge_summaries")
workflow.add_edge("summarizer_implications_impact", "merge_summaries")

# merge_summaries waits for ALL to complete
```

**Why needed?**
- Parallel branches must reconverge
- Ensures all perspectives are included
- Creates cohesive final output

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

**News API** (Free):
- Visit: https://newsapi.org/register
- Register for free account
- Copy API key

**OpenRouter** (for LLM):
- Visit: https://openrouter.ai/keys
- Get API key

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys
```

Your `.env` should contain:
```
NEWS_API_KEY=your_actual_news_api_key
OPENAI_API_KEY=your_actual_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

## Usage

### Run Locally

```bash
python agent.py
```

Example:
```
What topic would you like to research? climate change

🚀 Starting research workflow...

📋 Workflow stages:
  1. Reformulating query
  2. Fetching news from API (once)
  3. Parallel analysis (3 perspectives)
  4. Merging results

⏳ Processing... (this may take 20-30 seconds)

================================================================================
📊 FINAL RESEARCH BRIEF
================================================================================

# Research Brief: Climate Change

## Overview
Recent reporting highlights accelerating impacts of climate change...

## Key Findings
• Global temperatures continue to rise...
• Policy initiatives announced in multiple countries...
• Scientific consensus strengthens...

## Emerging Trends
• Increased corporate climate commitments...
• Growing youth activism...
• Renewable energy adoption accelerating...

## Implications
• Policy changes likely in next 12 months...
• Economic shifts toward green technology...
• International cooperation critical...

## Conclusion
Climate action entering critical phase...

================================================================================
```

### Run in LangGraph Studio

1. Open LangGraph Studio
2. Load this project directory
3. Graph will visualize with parallel branches
4. Click "Run" to execute
5. Watch parallel nodes execute simultaneously
6. Inspect state at each node

## Performance Notes

### Execution Time

- Sequential approach: ~60-90 seconds
  - 3 summarizers × 20-30 seconds each
- Parallel approach: ~20-30 seconds
  - All 3 summarizers run simultaneously
- **Speedup: ~3x faster**

### API Efficiency

- Redundant approach: 3 API calls
- This implementation: 1 API call
- **Cost savings: 66% reduction**

## Debugging Tips

### View Full State Flow

Uncomment in `main()`:
```python
print("\n🔍 Full message history:")
for i, msg in enumerate(final_state["messages"]):
    msg_type = type(msg).__name__
    content = msg.content if hasattr(msg, 'content') else str(msg)
    print(f"\n[{i}] {msg_type}:")
    print(content[:200] + "..." if len(str(content)) > 200 else content)
```

### LangGraph Studio

- Visual representation shows parallel branches clearly
- Inspect state at each node
- See timing of parallel execution
- Debug tool calls and results

### Common Issues

**"No articles found"**
- News API free tier limitations
- Try different query
- Check internet connection

**"Rate limit exceeded"**
- Free tier: 100 requests/day
- Wait or upgrade plan

**Slow execution**
- Normal for first run (model loading)
- Subsequent runs faster
- Parallel execution helps significantly

## Learning Objectives

After completing this project, you should understand:

1. ✅ How to integrate external APIs with LangGraph
2. ✅ How to implement parallel execution in graphs
3. ✅ How to share state across parallel branches
4. ✅ How to merge results from parallel processing
5. ✅ Why ToolNode is important for tool execution
6. ✅ How to avoid redundant API calls
7. ✅ How to design multi-perspective analysis systems

## Extension Ideas

### Add More Perspectives

```python
# Add fourth summarizer
def summarizer_sources_credibility(state):
    """Analyze source credibility and bias"""
    # Implementation

workflow.add_node("summarizer_sources", summarizer_sources_credibility)
workflow.add_edge("news_tool_node", "summarizer_sources")
workflow.add_edge("summarizer_sources", "merge_summaries")
```

### Add Conditional Branching

```python
def route_by_topic(state):
    """Route to different summarizers based on topic"""
    # If tech news → tech-specific summarizers
    # If politics → political analysis
    # etc.
```

### Add Multiple APIs

```python
@tool
def search_academic_papers(query: str):
    """Search arXiv or Google Scholar"""
    # Implementation

@tool
def search_social_media(query: str):
    """Search Twitter API"""
    # Implementation

# Parallel fetch from multiple sources
workflow.add_node("news_tool", ToolNode([search_news]))
workflow.add_node("papers_tool", ToolNode([search_academic_papers]))
workflow.add_node("social_tool", ToolNode([search_social_media]))
```

### Add Caching

```python
# Cache API results to avoid repeated calls
import hashlib
import json

_cache = {}

@tool
def search_news_cached(query: str):
    cache_key = hashlib.md5(query.encode()).hexdigest()
    if cache_key in _cache:
        return _cache[cache_key]

    result = search_news(query)
    _cache[cache_key] = result
    return result
```

## Files

- `agent.py` - Main workflow implementation
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template
- `README.md` - This file

## Next Steps

1. Run the basic workflow
2. Experiment with different research topics
3. Add print statements to understand timing
4. Visualize in LangGraph Studio
5. Try adding a fourth summarizer
6. Implement caching for repeated queries
7. Add error handling and retries
8. Explore conditional routing patterns

## Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [News API Docs](https://newsapi.org/docs)
- [Parallel Execution in LangGraph](https://langchain-ai.github.io/langgraph/concepts/low_level/#parallelization)
- [ToolNode Reference](https://langchain-ai.github.io/langgraph/reference/prebuilt/#toolnode)
