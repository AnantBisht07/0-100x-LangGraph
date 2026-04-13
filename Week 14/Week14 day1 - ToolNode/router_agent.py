"""
Router Agent — Conditional Routing with LangGraph
==================================================

Graph structure:  (Router | Conditional logic)

    START
      │
      ▼
  ┌──────────┐
  │  ROUTER  │  ← LLM classifies intent: "search" or "explain" # what is the current temp of india?
  └──────────┘
      │
      ├── intent == "search"   ( #router suggests the path )
      │       │
      │       ▼
      │   ┌──────────────────┐
      │   │ SEARCH TOOL NODE │  ← ToolNode runs the actual search
      │   └──────────────────┘
      │       │
      │       ▼
      │   ┌──────────────────────┐
      │   │ ANSWER WITH SEARCH   │  ← LLM reads results, writes answer
      │   └──────────────────────┘
      │       │
      │       ▼
      │      END
      │
      └── intent == "explain"
              │
              ▼
          ┌─────────────┐
          │ EXPLANATION  │  ← LLM explains the concept directly
          └─────────────┘
              │
              ▼
             END
"""

import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from ddgs import DDGS

load_dotenv()

# =============================================================================
# 1. LLM SETUP
# =============================================================================
# We create TWO versions of the LLM:
#   - base_llm: Plain LLM, no tool awareness. Used for routing, explaining,
#               and summarizing search results.
#   - tool_llm: LLM with the search tool bound. Used ONLY in the search path
#               so it can REQUEST a tool call that ToolNode will execute.

base_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="qwen/qwen3-coder-flash",
    temperature=0
)


# =============================================================================
# 2. TOOL DEFINITION
# =============================================================================
# The @tool decorator converts this function into a LangChain Tool object.
# It reads the function name, docstring, and type hints to build a schema
# that the LLM can understand and request.

@tool
def search_web(query: str) -> str:
    """Search the web for real-time factual information about a topic."""
    print(f"  [Tool Executing] search_web(query='{query}')")
    results = DDGS().text(query, max_results=3)
    if not results:
        return f"No search results found for: {query}"
    return "\n".join(r["body"] for r in results)


# Bind the tool to a separate LLM instance.
# This LLM will REQUEST tool calls; ToolNode will EXECUTE them.
tool_llm = base_llm.bind_tools([search_web])


# =============================================================================
# 3. NODE DEFINITIONS
# =============================================================================
# Each node is a function that:
#   - Receives the shared state (MessagesState with a "messages" list)
#   - Does its work
#   - Returns {"messages": [new_message]} to APPEND to the state


def router_node(state: MessagesState):
    """
    ROUTER NODE — The Decision Maker

    This node does NOT answer the question. It only CLASSIFIES the intent.
    The LLM reads the user's message and returns ONE word: "search" or "explain".

    WHY a separate router?
        Routing logic is decoupled from execution. The router just labels;
        the conditional edge reads that label and picks the correct path.
        This makes the graph modular — you can add new intents without
        rewriting node logic.
    """
    user_message = state["messages"][-1].content

    # We give the LLM a strict classification prompt.
    # No tool binding here — we just want a single-word text response.
    classification = base_llm.invoke([
        HumanMessage(content=(
            "You are an intent classifier. Your ONLY job is to classify the "
            "user's query into exactly one category.\n\n"
            "Categories:\n"
            '- "search" → The user wants real-time, factual, or current information '
            "(e.g., who founded X, latest news, what happened in Y).\n"
            '- "explain" → The user wants a conceptual explanation, definition, '
            "or understanding of a topic (e.g., what is recursion, how does gravity work).\n\n"
            "Rules:\n"
            "- Respond with ONLY the single word: search OR explain\n"
            "- Do NOT add any other text, punctuation, or explanation.\n\n"
            f"User query: {user_message}"
        ))
    ])

    print(f"  [Router] Intent classified as: '{classification.content.strip()}'")

    # Store the classification as an AIMessage in the state.
    # The conditional edge will read this to decide the path.
    return {"messages": [classification]}


def search_tool_node_caller(state: MessagesState):
    """
    SEARCH CALLER — Asks the LLM to generate a tool call request.

    WHY is this separate from ToolNode?
        ToolNode can only EXECUTE tool calls — it can't create them.
        Someone needs to ASK the LLM "please call the search tool."
        This node does that. It sends the user's question to the
        tool-aware LLM, which responds with a tool_calls request.
        The next node (ToolNode) will execute that request.
    """
    # The user's original question is the FIRST message in state.
    user_message = state["messages"][0].content

    # Use tool_llm (with search_web bound) so the LLM can REQUEST a tool call.
    response = tool_llm.invoke([
        HumanMessage(content=f"Search for factual information about: {user_message}")
    ])

    return {"messages": [response]}


# ToolNode — The Worker that ACTUALLY executes the search_web function.
# It reads tool_calls from the last AIMessage and runs the matching function.
search_executor = ToolNode([search_web])


def answer_with_search_node(state: MessagesState):
    """
    ANSWER NODE — Summarizes search results into a clean answer.

    WHY use base_llm (not tool_llm)?
        We already have the search results. We don't want the LLM to
        request ANOTHER tool call — we want a plain text answer.
    """
    # The last message is the ToolMessage containing raw search snippets.
    search_results = state["messages"][-1].content

    response = base_llm.invoke([
        HumanMessage(content=(
            "Using the search results below, write a clear and concise answer "
            "to the user's question.\n\n"
            f"Search results:\n{search_results}"
        ))
    ])

    return {"messages": [response]}


def explanation_node(state: MessagesState):
    """
    EXPLANATION NODE — Directly explains a concept using the LLM's knowledge.

    WHY no tools here?
        Conceptual questions like "What is recursion?" don't need web search.
        The LLM's training data already contains this knowledge.
        Using base_llm (no tools) ensures a direct text answer.
    """
    user_message = state["messages"][0].content

    response = base_llm.invoke([
        HumanMessage(content=(
            "You are a helpful teacher. Explain the following concept clearly "
            "and concisely, suitable for a beginner.\n\n"
            f"Question: {user_message}"
        ))
    ])

    return {"messages": [response]}


# =============================================================================
# 4. ROUTING FUNCTION — Reads the router's output and picks a path
# =============================================================================
# This function is used by add_conditional_edges.
# It receives the CURRENT state and returns a string key ("search" or "explain")
# that maps to the next node.

def route_by_intent(state: MessagesState) -> str:
    """
    WHY a separate function instead of if-else inside a node?
        LangGraph's add_conditional_edges requires a function that returns
        a routing KEY. This keeps routing logic declarative and visible
        in the graph structure — not hidden inside node code.
    """
    # The last message is the router's AIMessage containing "search" or "explain".
    router_output = state["messages"][-1].content.strip().lower()

    # Guard against unexpected LLM output.
    if "search" in router_output:
        return "search"
    else:
        return "explain"


# =============================================================================
# 5. BUILD THE GRAPH
# =============================================================================
# The graph is like an assembly line blueprint.
# We add stations (nodes) and tracks (edges) between them.

graph = StateGraph(MessagesState)

# --- Add all nodes ---
graph.add_node("router", router_node)
graph.add_node("search_caller", search_tool_node_caller)
graph.add_node("search_executor", search_executor)
graph.add_node("answer_with_search", answer_with_search_node)
graph.add_node("explanation", explanation_node)

# --- Entry point ---
graph.add_edge(START, "router")

# --- Conditional edge: router → search path OR explain path ---
# add_conditional_edges takes:
#   1. Source node name: "router"
#   2. Routing function: route_by_intent (returns "search" or "explain")
#   3. Path map: maps routing keys to node names
#
# WHY conditional edges instead of if-else in code?
#   - The graph structure becomes VISIBLE and debuggable.
#   - LangGraph Studio can visualize the branching paths.
#   - Adding a third intent later is just one more entry in the map.
graph.add_conditional_edges(
    "router",
    route_by_intent,
    {
        "search": "search_caller",     # Factual → search path
        "explain": "explanation",       # Conceptual → explain path
    }
)

# --- Search path: caller → executor → answer → END ---
graph.add_edge("search_caller", "search_executor")
graph.add_edge("search_executor", "answer_with_search")
graph.add_edge("answer_with_search", END)

# --- Explain path: explanation → END ---
graph.add_edge("explanation", END)

# --- Compile the graph into a runnable agent ---
agent = graph.compile()


# =============================================================================
# 6. RUN
# =============================================================================

if __name__ == "__main__":
    user_input = input("You: ")
    print()

    result = agent.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    print(f"\nAnswer:\n{result['messages'][-1].content}")

