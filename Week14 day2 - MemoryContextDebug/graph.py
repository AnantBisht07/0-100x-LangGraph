"""
==========================================================================
  SUNDAY SESSION: Memory, Context & Debugging in LangGraph
==========================================================================

GOAL:
  Understand how STATE flows through a LangGraph graph.
  Learn to TRACE each node's contribution to the shared state.
  Learn to DEBUG state evolution in LangGraph Studio.

GRAPH TOPOLOGY (no routing, no conditionals):

  START → qna_agent → search_agent → summarizer_agent → END

KEY LESSON:
  Each node reads from shared state and writes to a NEW key.
  No node overwrites another node's output.
  This makes the entire execution TRACEABLE — you can inspect
  the state after any node and see exactly what was added.

WHY THIS MATTERS:
  - If nodes overwrite the same key, you LOSE intermediate data.
    For example, if both QnA and Search wrote to "result", you'd
    never know what QnA produced — it would be gone.
  - By using separate keys (user_question, search_result, final_summary),
    every step is preserved and visible in Studio's state inspector.

HOW TO DEBUG IN LANGRAPH STUDIO:
  1. Open this project in Studio (langgraph dev).
  2. Send a query. Studio shows each node as a step.
  3. Click any node → inspect the STATE at that point.
  4. You'll see keys being ADDED, never removed.
  5. The "messages" list grows with each node — that's your
     full execution trace.
==========================================================================
"""

import os
from typing import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from ddgs import DDGS

load_dotenv()

# =========================================================================
# 1. STATE DEFINITION
# =========================================================================
# IMPORTANT: Each node writes to its OWN key.
#   - qna_agent     → writes "user_question"
#   - search_agent   → writes "search_result"
#   - summarizer     → writes "final_summary"
#
# The "messages" list is our EXECUTION TRACE — every LLM call and tool
# call appends here, giving us a full history for debugging.
# =========================================================================
class TracingState(TypedDict):
    messages: list             # Full message trace (for debugging / Studio)
    user_question: str         # Set by QnA Agent — the clarified question
    search_result: str         # Set by Search Agent — raw search output
    final_summary: str         # Set by Summarizer — the final answer


# =========================================================================
# 2. TOOL — DuckDuckGo web search
# =========================================================================
# This is the ONLY tool in the graph. Only the Search Agent uses it.
# The @tool decorator registers the function schema so LangGraph's
# ToolNode can execute it when the LLM requests a tool call.
# =========================================================================
@tool
def web_search(query: str) -> str:
    """Search the web for factual, up-to-date information about a topic."""
    print(f"  [TOOL CALLED] web_search('{query}')")
    results = DDGS().text(query, max_results=3)
    if not results:
        return f"No results found for: {query}"
    # Return raw text bodies — no summarization here.
    return "\n---\n".join(r["body"] for r in results)


# =========================================================================
# 3. LLM SETUP
# =========================================================================
# We create TWO references:
#   base_llm  — plain LLM, used by QnA and Summarizer (no tools)
#   search_llm — LLM with web_search bound, used by Search Agent
#
# bind_tools() does NOT execute tools. It only tells the LLM that
# tools exist so it can produce tool_call messages.
# =========================================================================
base_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="qwen/qwen3-coder-flash",
    temperature=0,
)

# The search agent needs bind_tools so the LLM can REQUEST a tool call.
# ToolNode then EXECUTES that call.
search_llm = base_llm.bind_tools([web_search])


# =========================================================================
# 4. NODE: QnA Agent
# =========================================================================
# PURPOSE: Take the raw user input and produce a clear, searchable question.
#
# READS:  messages[-1]  (the user's original message)
# WRITES: "user_question" — a NEW state key
#
# This node does NOT touch "search_result" or "final_summary".
# =========================================================================
def qna_agent(state: TracingState):
    print("\n>>> NODE: qna_agent")

    # Read the user's raw input from the message history.
    user_input = state["messages"][-1].content
    print(f"    User said: {user_input}")

    # Ask the LLM to rephrase into a clear, searchable question.
    response = base_llm.invoke([
        HumanMessage(
            content=(
                "You are a question-clarification assistant. "
                "Take the following user input and rephrase it into a single, "
                "clear, factual question suitable for a web search. "
                "Output ONLY the rephrased question, nothing else.\n\n"
                f"User input: {user_input}"
            )
        )
    ])

    clarified_question = response.content
    print(f"    Clarified question: {clarified_question}")

    # WRITE to state: new key "user_question" + append to messages trace.
    # We do NOT overwrite "messages" — LangGraph merges lists automatically.
    return {
        "user_question": clarified_question,
        "messages": [AIMessage(content=f"[QnA Agent] {clarified_question}")],
    }


# =========================================================================
# 5. NODE: Search Agent (ToolNode-based)
# =========================================================================
# This is a TWO-STEP process:
#   Step A: search_agent_call  — LLM decides what to search (produces tool_call)
#   Step B: search_tool_execute — ToolNode executes the tool call
#   Step C: search_agent_collect — reads tool output, stores in "search_result"
#
# WHY three sub-steps?
#   ToolNode expects the last message to be an AIMessage with tool_calls.
#   After ToolNode runs, the last message is a ToolMessage with the result.
#   We need a final step to copy that result into our "search_result" key
#   so the Summarizer can read it by key (not by digging through messages).
# =========================================================================

# Step A: Ask the LLM to call web_search
def search_agent_call(state: TracingState):
    print("\n>>> NODE: search_agent_call")

    # READ from state: use the clarified question (context reuse!)
    question = state["user_question"]
    print(f"    Searching for: {question}")

    # The LLM (with tools bound) will produce a tool_call message.
    response = search_llm.invoke([
        HumanMessage(
            content=f"Search the web for: {question}"
        )
    ])

    return {"messages": [response]}


# Step B: ToolNode executes the tool call automatically.
search_tool_execute = ToolNode([web_search])


# Step C: Collect tool output into the "search_result" state key.
def search_agent_collect(state: TracingState):
    print("\n>>> NODE: search_agent_collect")

    # The last message is a ToolMessage containing raw search output.
    raw_result = state["messages"][-1].content
    print(f"    Raw search result (first 200 chars): {raw_result[:200]}...")

    # WRITE to state: new key "search_result".
    # We do NOT summarize — that's the Summarizer's job.
    return {
        "search_result": raw_result,
        "messages": [AIMessage(content=f"[Search Agent] Stored raw search results.")],
    }


# =========================================================================
# 6. NODE: Summarizer Agent
# =========================================================================
# PURPOSE: Read the stored search result and produce a final summary.
#
# READS:  "user_question"  — to know what was asked
#         "search_result"  — to know what was found
# WRITES: "final_summary"  — the final answer
#
# KEY LESSON — CONTEXT REUSE:
#   The Summarizer does NOT call any tool. It does NOT search again.
#   It reads data that was already placed in state by previous nodes.
#   This demonstrates how state acts as shared MEMORY between agents.
#
# WHAT IF state was overwritten?
#   If search_agent had written to "user_question" instead of
#   "search_result", the original question would be LOST.
#   The Summarizer would have no idea what the user originally asked.
#   → This is why each node writes to its OWN key.
# =========================================================================
def summarizer_agent(state: TracingState):
    print("\n>>> NODE: summarizer_agent")

    # READ from state — both keys written by previous nodes.
    question = state["user_question"]
    search_data = state["search_result"]

    print(f"    Question: {question}")
    print(f"    Search data length: {len(search_data)} chars")

    response = base_llm.invoke([
        HumanMessage(
            content=(
                "You are a summarization assistant. "
                "Based on the search results below, write a clear and concise "
                "answer to the user's question.\n\n"
                f"QUESTION: {question}\n\n"
                f"SEARCH RESULTS:\n{search_data}\n\n"
                "Provide a well-structured summary. Do not search again."
            )
        )
    ])

    final = response.content
    print(f"    Summary (first 200 chars): {final[:200]}...")

    return {
        "final_summary": final,
        "messages": [AIMessage(content=f"[Summarizer] {final}")],
    }


# =========================================================================
# 7. BUILD THE GRAPH
# =========================================================================
# Topology: START → qna → search_call → search_execute → search_collect → summarizer → END
#
# This is a STRICTLY SEQUENTIAL graph. No conditionals, no routing.
# Every run follows the exact same path — making it easy to trace.
#
# IN LANGRAPH STUDIO:
#   - Each node appears as a box in the graph view.
#   - Click a box after execution to see the state snapshot at that point.
#   - The "messages" list grows at each step — that's your trace.
#   - The named keys (user_question, search_result, final_summary) appear
#     one by one as nodes execute — you can see state EVOLVING.
# =========================================================================
graph = StateGraph(TracingState)

# Register all nodes
graph.add_node("qna_agent", qna_agent)
graph.add_node("search_agent_call", search_agent_call)
graph.add_node("search_tool_execute", search_tool_execute)
graph.add_node("search_agent_collect", search_agent_collect)
graph.add_node("summarizer_agent", summarizer_agent)

# Wire them sequentially — no conditions, no branching
graph.add_edge(START, "qna_agent")
graph.add_edge("qna_agent", "search_agent_call")
graph.add_edge("search_agent_call", "search_tool_execute")
graph.add_edge("search_tool_execute", "search_agent_collect")
graph.add_edge("search_agent_collect", "summarizer_agent")
graph.add_edge("summarizer_agent", END)

# Compile the graph into a runnable agent
agent = graph.compile()


# =========================================================================
# 8. RUN LOCALLY
# =========================================================================
# This __main__ block lets you test from the terminal:
#   python graph.py
#
# It prints the full final state so you can inspect every key.
# In Studio, you get the same info in the UI — but this is useful
# for quick local debugging.
# =========================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Memory, Context & Debugging — LangGraph Demo")
    print("=" * 60)

    user_input = input("\nYou: ")

    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_question": "",
        "search_result": "",
        "final_summary": "",
    }

    # =========================================================================
    # TRACING METHOD: stream() instead of invoke()
    # =========================================================================
    # invoke() runs the entire graph and returns the FINAL state only.
    # stream() yields the state AFTER EACH NODE — this is how you trace.
    #
    # Each chunk looks like:
    #   { "node_name": { "key": "value_written_by_that_node" } }
    #
    # This lets you see EXACTLY what each node added to state.
    # In LangGraph Studio, this is shown visually — but here we print it.
    # =========================================================================
    print("\n" + "=" * 60)
    print("  STEP-BY-STEP STATE TRACE (using stream())")
    print("=" * 60)

    final_state = None  # we'll capture the last state

    for step in agent.stream(initial_state):
        # step is a dict like {"qna_agent": {"user_question": "...", "messages": [...]}}
        node_name = list(step.keys())[0]
        node_output = step[node_name]

        print(f"\n--- After node: {node_name} ---")
        print(f"    Keys written: {list(node_output.keys())}")

        # Show what this node wrote (excluding full message objects for readability)
        for key, value in node_output.items():
            if key == "messages":
                # Show message types only — full content is too noisy
                msg_types = [type(m).__name__ for m in value]
                print(f"    messages: appended {msg_types}")
            else:
                preview = str(value)[:150]
                print(f"    {key}: {preview}")

        final_state = node_output  # keep updating

    # =========================================================================
    # FINAL STATE INSPECTION
    # =========================================================================
    # After streaming, we run invoke() once more to get the complete state.
    # (stream() yields per-node diffs, not the accumulated state.)
    # =========================================================================
    print("\n" + "=" * 60)
    print("  FULL FINAL STATE (using invoke())")
    print("=" * 60)

    result = agent.invoke(initial_state)

    print(f"\n[user_question]   {result['user_question']}")
    print(f"\n[search_result]   {result['search_result'][:300]}...")
    print(f"\n[final_summary]   {result['final_summary']}")

    print(f"\n[messages count]  {len(result['messages'])} messages in trace")

    print("\n--- Message Trace ---")
    for i, msg in enumerate(result["messages"]):
        role = type(msg).__name__
        content = msg.content[:120] if msg.content else "(tool_call)"
        print(f"  [{i}] {role}: {content}")

    print("\n" + "=" * 60)
    print("  ANSWER:")
    print("=" * 60)
    print(result["final_summary"])
