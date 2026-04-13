"""
Graph B: Summarizer Bot

PURPOSE:
This graph creates summaries based on retrieved documents.

ARCHITECTURE:
    User Request (e.g., "Summarize key concepts")
         ↓
    [Agent Node] ← Decides to search documents
         ↓
    [Document Search ToolNode] ← SHARED/REUSED (same as QnA graph!)
         ↓
    [Agent Node] ← Synthesizes summary from chunks
         ↓
    Summary

WHY THIS GRAPH EXISTS:
- Defines DIFFERENT BEHAVIOR (summarization vs QnA)
- Reuses the SAME CAPABILITY (document search)
- Shows how one tool can serve multiple purposes

NOTE:
Compare this to qna_graph.py:
- Different system prompts (behavior)
- Different temperature (creative vs factual)
- SAME tool import (reuse)
This is the power of separation of concerns!
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# IMPORT THE SAME SHARED TOOL
# NOTE: This is the EXACT SAME tool as qna_graph.py uses!
# No code duplication, single source of truth
from tools import get_document_search_node, create_document_search_tool


# Define the graph state
class SummarizerState(TypedDict):
    """
    State for the Summarizer graph.

    NOTE:
    Different graphs can have different state structures.
    The tool doesn't care - it just receives a query and returns results.
    """
    messages: Annotated[list, add_messages]
    # The topic or instruction to summarize
    topic: str


def create_summarizer_graph():
    """
    Create the Summarizer graph.

    GRAPH FLOW:
    1. User provides a summarization request
    2. Agent searches for relevant documents
    3. Tool retrieves relevant chunks
    4. Agent creates a concise summary

    DIFFERENCE FROM QnA:
    - Higher temperature (more creative)
    - Different system prompt (synthesis vs factual)
    - Different behavior, SAME tool

    Returns:
        A compiled LangGraph
    """

    # Initialize LLM for summarization
    # NOTE: Higher temperature for creative synthesis
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.3,  # Slightly higher for better synthesis
    )

    # Bind the SAME tool to this LLM
    # NOTE: The tool doesn't change, but how we use it does
    tool = create_document_search_tool()
    llm_with_tools = llm.bind_tools([tool])

    def agent_node(state: SummarizerState):
        """
        Agent node: Decides whether to search docs or generate summary.

        DIFFERENCE FROM QnA AGENT:
        - Different system prompt
        - Focuses on synthesis and conciseness
        - Same tool usage pattern

        NOTE:
        By changing just the prompt, we get completely different behavior
        using the same underlying tool capability.
        """
        messages = state["messages"]

        # System prompt for SUMMARIZATION behavior
        # COMPARE to qna_graph.py - different behavior, same tool
        system_message = SystemMessage(content="""You are a skilled summarization assistant.

Your job:
1. When given a topic or instruction, use the search_documents tool to find relevant information
2. Read through ALL retrieved chunks carefully
3. Create a concise, well-structured summary that captures key points
4. Organize information logically (use bullet points, sections if helpful)
5. Focus on the most important concepts and insights

Remember: Search first, then synthesize the information into a clear summary.""")

        # Call the LLM with tools (same pattern as QnA)
        response = llm_with_tools.invoke([system_message] + messages)
        return {"messages": [response]}

    def should_continue(state: SummarizerState):
        """
        Router function: Decides whether to call tools or end.

        NOTE:
        This routing logic is IDENTICAL to qna_graph.py.
        In a real system, you might extract this to a shared utility.
        """
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM wants to call a tool, route to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, we're done
        return END

    # Build the graph
    workflow = StateGraph(SummarizerState)

    # Add nodes
    # CRITICAL: This is the SAME get_document_search_node() as QnA graph!
    # We're reusing the exact same ToolNode instance
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", get_document_search_node())

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edges (same structure as QnA graph)
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

    # After tools, return to agent for synthesis
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


# ARCHITECTURE COMPARISON:
#
# QnA Graph vs Summarizer Graph:
# ┌─────────────────┬──────────────────┬─────────────────┐
# │   Component     │    QnA Graph     │ Summarizer Graph│
# ├─────────────────┼──────────────────┼─────────────────┤
# │ Tool Import     │ SAME             │ SAME            │
# │ ToolNode        │ SAME             │ SAME            │
# │ System Prompt   │ Different        │ Different       │
# │ Temperature     │ 0.0 (factual)    │ 0.3 (creative)  │
# │ State Schema    │ QnAState         │ SummarizerState │
# │ Graph Structure │ Similar          │ Similar         │
# └─────────────────┴──────────────────┴─────────────────┘
#
