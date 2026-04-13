"""
Minimal 3-Agent Sequential Graph with LangGraph
================================================
Educational example for Week 13: First Agent Graph

Graph Flow:
    START → Interpreter → Summarizer → Formatter → END
"""

import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# LLM SETUP (OpenRouter)
# =============================================================================

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="openai/gpt-4o-mini"
)


# =============================================================================
# STATE DEFINITION
# =============================================================================

class GraphState(TypedDict):
    """Shared state passed between agents."""

    user_question: str      # Input from user
    intent: str             # From Interpreter
    topic: str              # From Interpreter
    summary: str            # From Summarizer
    final_output: str       # From Formatter


# =============================================================================
# AGENT 1: INTERPRETER
# =============================================================================

def interpreter_agent(state: GraphState) -> dict:
    """Extracts intent and topic from user input."""
    print("[Agent 1: Interpreter] Running...")

    return {
        "intent": "explain",
        "topic": state["user_question"]
    }


# =============================================================================
# AGENT 2: SUMMARIZER
# =============================================================================

def summarizer_agent(state: GraphState) -> dict:
    """Creates a brief explanation based on the topic."""
    print("[Agent 2: Summarizer] Running...")

    response = llm.invoke([
        HumanMessage(content=f"Explain this in 2-3 sentences: {state['topic']}")
    ])

    return {"summary": response.content}


# =============================================================================
# AGENT 3: FORMATTER
# =============================================================================

def formatter_agent(state: GraphState) -> dict:
    """Formats the summary for final output."""
    print("[Agent 3: Formatter] Running...")

    response = llm.invoke([
        HumanMessage(content=f"Format this nicely:\n\nTopic: {state['topic']}\n\n{state['summary']}")
    ])

    return {"final_output": response.content}


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def build_graph() -> StateGraph:
    """Builds the 3-agent sequential graph."""

    graph = StateGraph(GraphState)

    # Add agents as nodes
    graph.add_node("interpreter", interpreter_agent)
    graph.add_node("summarizer", summarizer_agent)
    graph.add_node("formatter", formatter_agent)

    # Define sequential flow
    graph.add_edge(START, "interpreter")
    graph.add_edge("interpreter", "summarizer")
    graph.add_edge("summarizer", "formatter")
    graph.add_edge("formatter", END)

    return graph


# START -> interpreter(some context) -> summarizer(some context) -> formatter(some context) -> END

# =============================================================================
# COMPILED GRAPH (for LangGraph Studio)
# =============================================================================

graph = build_graph().compile()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    user_input = input("You: ")

    result = graph.invoke({"user_question": user_input})

    print("\nAnswer:")
    print(result["final_output"])
