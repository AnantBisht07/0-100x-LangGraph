"""
WEEK 15 - SUNDAY: External APIs & Parallel Branching Flows

This workflow demonstrates:
1. External API integration (News API) - fetch data ONCE
2. Parallel execution - 3 summarizers run simultaneously
3. Branching flows - different analysis perspectives
4. State sharing - all nodes read from same API results
5. Merging results - consolidate into final research brief

Graph Flow:
START → qna_agent → news_search_tool_node → [parallel: summarizer_1, summarizer_2, summarizer_3] → merge_summaries → END
"""

import os
import requests
from typing import Literal
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

"""
Sequential
Step 1 -> Wait -> Step 2 -> Wait -> Step 3 -> Wait -> Step 4
TT: 50 seconds

Parallel 
Step 1 -
Step 2 -   All happen simultaneously
Step 3 - 
TT: 20 seconds
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise ValueError("NEWS_API_KEY required. Get one from: https://newsapi.org/")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY required")


# ============================================================================
# EXTERNAL API TOOL
# ============================================================================

@tool
def search_news(query: str, max_articles: int = 10) -> str:
    """
    Search for latest news articles using News API.

    This tool will be executed ONCE by ToolNode.
    Results are stored in state and reused by all parallel summarizers.

    WHY @tool?
    - Marks function as LangChain tool (LLM can understand and call it)
    - Auto-generates schema from docstring + type hints

    WHY ToolNode will wrap this?
    - ToolNode executes tools in LangGraph workflows
    - Handles tool calls from agent messages
    - Returns results in proper state format
    - Executed ONCE - results shared via state

    Args:
        query: Search query for news (e.g., "climate change")
        max_articles: Number of articles to fetch (default: 10)

    Returns:
        Formatted string with article data for parallel processing
    """
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": max_articles,
        "apiKey": NEWS_API_KEY,
        "language": "en"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])

        if not articles:
            return f"No articles found for: {query}"

        # Format for parallel summarizers
        # Each summarizer will receive the SAME data but process differently
        formatted_results = []
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            description = article.get("description", "No description")
            content = article.get("content", "No content")
            url_link = article.get("url", "No URL")
            source = article.get("source", {}).get("name", "Unknown")
            published = article.get("publishedAt", "Unknown date")

            formatted_results.append(
                f"[Article {i}]\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Published: {published}\n"
                f"Description: {description}\n"
                f"Content: {content}\n"
                f"URL: {url_link}\n"
            )

        return "\n".join(formatted_results)

    except requests.exceptions.RequestException as e:
        return f"Error fetching news: {str(e)}"


# ============================================================================
# AGENT NODES
# ============================================================================

def qna_agent(state: MessagesState) -> MessagesState:
    """
    QnA Agent: Reformulates user question into research query.

    WHAT IT DOES:
    - Reads user's natural language question
    - Extracts core research topic
    - Outputs clean query for News API

    STATE FLOW:
    - INPUT: User question in state["messages"]
    - OUTPUT: Reformulated query in state["messages"]
    - Next nodes will see this query
    """
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0,
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )

    system_message = SystemMessage(content="""You are a research query expert.

Extract the core research topic from the user's question.
Output ONLY the search query (2-5 words).

Examples:
- "What's new in AI?" → "artificial intelligence"
- "Climate change updates?" → "climate change"
- "Space exploration news?" → "space exploration"
""")

    messages = state["messages"]
    response = llm.invoke([system_message] + messages)

    return {"messages": [response]}


def news_search_agent(state: MessagesState) -> MessagesState:
    """
    News Search Agent: Decides to call the news search tool.

    WHAT IT DOES:
    - Takes reformulated query
    - Generates tool call for search_news
    - ToolNode (next) will execute the actual API call

    STATE FLOW:
    - INPUT: Research query from state["messages"]
    - OUTPUT: Tool call message in state["messages"]
    - ToolNode executes this tool call ONCE
    """
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0,
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )

    llm_with_tools = llm.bind_tools([search_news])

    system_message = SystemMessage(content="""You are a news research assistant.

Use the search_news tool with the query from the previous message.
Request 10 articles for comprehensive analysis.

Always call the tool.""")

    messages = state["messages"]
    response = llm_with_tools.invoke([system_message] + messages)

    return {"messages": [response]}


# ============================================================================
# PARALLEL SUMMARIZER NODES
# ============================================================================
# These three nodes run IN PARALLEL after the ToolNode
# Each reads the SAME news articles from state
# Each analyzes from a DIFFERENT perspective
# Results will be merged by merge_summaries node
# ============================================================================

def summarizer_key_facts(state: MessagesState) -> MessagesState:
    """
    Summarizer 1: Extract key facts and findings.

    PARALLEL EXECUTION:
    - Runs simultaneously with summarizer_trends and summarizer_impact
    - All three summarizers read the SAME articles from state
    - No dependencies between summarizers = true parallelism

    PERSPECTIVE:
    - Focus: What happened? Core facts and events
    - Output: Bullet points of key findings

    STATE FLOW:
    - INPUT: News articles from ToolNode in state["messages"]
    - OUTPUT: Key facts summary in state["messages"]
    """
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.2,
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )

    system_message = SystemMessage(content="""You are a fact-extraction specialist.

Analyze the news articles and extract:
- Key facts and events
- Important statistics and data
- Main developments and announcements

Format as bullet points.
Be concise and factual.
Start with: "KEY FACTS:\n"
""")

    messages = state["messages"]
    response = llm.invoke([system_message] + messages)

    return {"messages": [response]}


def summarizer_trends_themes(state: MessagesState) -> MessagesState:
    """
    Summarizer 2: Identify trends and themes.

    PARALLEL EXECUTION:
    - Runs simultaneously with summarizer_key_facts and summarizer_impact
    - Reads same articles, different analysis angle

    PERSPECTIVE:
    - Focus: What patterns emerge? Recurring themes?
    - Output: Trends and common themes across articles

    STATE FLOW:
    - INPUT: News articles from ToolNode in state["messages"]
    - OUTPUT: Trends analysis in state["messages"]
    """
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.3,
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )

    system_message = SystemMessage(content="""You are a trend analysis specialist.

Analyze the news articles and identify:
- Recurring themes across multiple sources
- Emerging patterns and trends
- Common narratives and perspectives

Format as bullet points.
Look for connections between articles.
Start with: "TRENDS & THEMES:\n"
""")

    messages = state["messages"]
    response = llm.invoke([system_message] + messages)

    return {"messages": [response]}


def summarizer_implications_impact(state: MessagesState) -> MessagesState:
    """
    Summarizer 3: Analyze implications and impact.

    PARALLEL EXECUTION:
    - Runs simultaneously with summarizer_key_facts and summarizer_trends
    - Same input data, different analytical lens

    PERSPECTIVE:
    - Focus: So what? Why does this matter?
    - Output: Implications, consequences, future impact

    STATE FLOW:
    - INPUT: News articles from ToolNode in state["messages"]
    - OUTPUT: Impact analysis in state["messages"]
    """
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.4,
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )

    system_message = SystemMessage(content="""You are an impact analysis specialist.

Analyze the news articles and assess:
- Implications of the reported events
- Potential consequences and effects
- Future impact and what to watch for

Format as bullet points.
Think about broader significance.
Start with: "IMPLICATIONS & IMPACT:\n"
""")

    messages = state["messages"]
    response = llm.invoke([system_message] + messages)

    return {"messages": [response]}


# ============================================================================
# MERGE NODE
# ============================================================================

def merge_summaries(state: MessagesState) -> MessagesState:
    """
    Merge Node: Consolidates all parallel summaries into final research brief.

    WHAT IT DOES:
    - Waits for ALL three summarizers to complete
    - Reads their outputs from state["messages"]
    - Combines into cohesive research brief
    - Produces final answer for user

    STATE FLOW:
    - INPUT: Three summaries from parallel nodes in state["messages"]
    - OUTPUT: Final consolidated research brief in state["messages"]

    WHY THIS NODE?
    - Parallel execution needs a merge point
    - Ensures all perspectives are integrated
    - Creates coherent final output
    """
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.3,
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )

    system_message = SystemMessage(content="""You are a research brief synthesizer.

You will see three different analyses of the same news articles:
1. Key Facts
2. Trends & Themes
3. Implications & Impact

Your job:
- Combine all three perspectives into ONE cohesive research brief
- Structure it clearly with sections
- Remove redundancies
- Create a comprehensive yet concise overview

Format:
# Research Brief: [Topic]

## Overview
[1-2 sentence summary]

## Key Findings
[Synthesized from all three analyses]

## Emerging Trends
[Pattern analysis]

## Implications
[Future impact and significance]

## Conclusion
[Takeaway message]

Be professional and thorough.""")

    messages = state["messages"]
    response = llm.invoke([system_message] + messages)

    return {"messages": [response]}


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_research_workflow():
    """
    Create the research workflow with parallel execution.

    GRAPH STRUCTURE:

    START
      ↓
    qna_agent (reformulate query)
      ↓
    news_search_agent (decide to call tool)
      ↓
    news_tool_node (execute News API - ONCE)
      ↓
    ┌─────────────────────────────────────────┐
    │ PARALLEL BRANCHING (3 simultaneous)     │
    │                                         │
    │  summarizer_key_facts                   │
    │  summarizer_trends_themes               │
    │  summarizer_implications_impact         │
    └─────────────────────────────────────────┘
      ↓
    merge_summaries (consolidate results)
      ↓
    END

    WHY THIS STRUCTURE?

    1. SEQUENTIAL SETUP:
       - qna_agent: Extract clean query
       - news_search_agent: Generate tool call
       - news_tool_node: Execute API call ONCE

    2. PARALLEL PROCESSING:
       - Three summarizers run simultaneously
       - No dependencies between them
       - All read same data from state
       - Each provides different perspective

    3. MERGE POINT:
       - merge_summaries waits for all three
       - Combines perspectives
       - Produces final output

    STATE MANAGEMENT:
    - MessagesState accumulates all messages
    - Tool results stored once, read by all summarizers
    - No redundant API calls
    - Full context available for merging

    WHY TOOLNODE?
    - Separates tool execution from agent decision
    - Executed exactly once (not per summarizer)
    - Results automatically added to state
    - All downstream nodes access same results

    PARALLEL EXECUTION MECHANICS:
    - When multiple nodes have edges from the same source
    - And no dependencies between them
    - LangGraph executes them in parallel
    - Continues when ALL complete (barrier synchronization)
    """
    # Create state graph
    workflow = StateGraph(MessagesState)

    # Add sequential nodes
    workflow.add_node("qna_agent", qna_agent)
    workflow.add_node("news_search_agent", news_search_agent)

    # Add ToolNode - wraps search_news tool
    # Executes ONCE, results shared via state
    workflow.add_node("news_tool_node", ToolNode([search_news]))

    # Add parallel summarizer nodes
    # These will run SIMULTANEOUSLY
    workflow.add_node("summarizer_key_facts", summarizer_key_facts)
    workflow.add_node("summarizer_trends_themes", summarizer_trends_themes)
    workflow.add_node("summarizer_implications_impact", summarizer_implications_impact)

    # Add merge node
    workflow.add_node("merge_summaries", merge_summaries)

    # Define sequential flow (setup)
    workflow.add_edge(START, "qna_agent")
    workflow.add_edge("qna_agent", "news_search_agent")
    workflow.add_edge("news_search_agent", "news_tool_node")

    # BRANCHING: From tool node to THREE parallel summarizers
    # These edges create the parallel execution
    # All three nodes will start simultaneously after news_tool_node completes
    workflow.add_edge("news_tool_node", "summarizer_key_facts")
    workflow.add_edge("news_tool_node", "summarizer_trends_themes")
    workflow.add_edge("news_tool_node", "summarizer_implications_impact")

    # MERGE: All three summarizers converge to merge node
    # merge_summaries will wait until ALL three complete
    workflow.add_edge("summarizer_key_facts", "merge_summaries")
    workflow.add_edge("summarizer_trends_themes", "merge_summaries")
    workflow.add_edge("summarizer_implications_impact", "merge_summaries")

    # Final edge to END
    workflow.add_edge("merge_summaries", END)

    # Compile the graph
    # Validates structure and creates executable workflow
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point.

    DEBUGGABILITY:
    - Clear print statements show progress
    - Each stage is visible
    - State flow can be traced
    - Compatible with LangGraph Studio for visual debugging
    """
    print("=" * 80)
    print("WEEK 15 - SUNDAY: External APIs & Parallel Branching Flows")
    print("=" * 80)
    print()

    # Create workflow
    graph = create_research_workflow()

    # Get user input
    user_question = input("What topic would you like to research? ")
    print()

    # Prepare initial state
    initial_state = {
        "messages": [HumanMessage(content=user_question)]
    }

    print("🚀 Starting research workflow...")
    print()
    print("📋 Workflow stages:")
    print("  1. Reformulating query")
    print("  2. Fetching news from API (once)")
    print("  3. Parallel analysis (3 perspectives)")
    print("  4. Merging results")
    print()
    print("⏳ Processing... (this may take 20-30 seconds)")
    print()

    # Execute graph
    # The graph will:
    # 1. Run qna_agent
    # 2. Run news_search_agent
    # 3. Run news_tool_node (API call)
    # 4. Run three summarizers IN PARALLEL
    # 5. Run merge_summaries
    final_state = graph.invoke(initial_state)

    # Extract final research brief
    final_message = final_state["messages"][-1]

    print("=" * 80)
    print("📊 FINAL RESEARCH BRIEF")
    print("=" * 80)
    print()
    print(final_message.content)
    print()
    print("=" * 80)
    print()
    print("✅ Research complete!")
    print()

    # DEBUGGING TIP:
    # To see ALL messages (full state flow), uncomment:
    # print("\n🔍 Full message history:")
    # for i, msg in enumerate(final_state["messages"]):
    #     msg_type = type(msg).__name__
    #     content = msg.content if hasattr(msg, 'content') else str(msg)
    #     print(f"\n[{i}] {msg_type}:")
    #     print(content[:200] + "..." if len(str(content)) > 200 else content)


if __name__ == "__main__":
    main()
