"""
Streaming Memory-Controlled Conversational Agent
Combines memory management with token-by-token streaming
"""

from typing import TypedDict, Annotated, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
import sys

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")

if api_key:
    print('API Key loaded successfully!')
else:
    print("OPENROUTER_API_KEY not found. Set it in .env file.")
    exit(1)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    streaming=True  # Enable streaming mode
)

# ============================================================================
# STATE: Same as non-streaming version
# ============================================================================

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str
    turn_count: int
    window_count: int

# ============================================================================
# NODE 1: Streaming Chat Node
# ============================================================================

def chat_node_streaming(state: ConversationState):
    """Chat handler with streaming support"""

    # Build context (same as before)
    context = []

    if state["summary"]:
        context.append(SystemMessage(content=f"Previous conversation: {state['summary']}"))

    context.extend(state["messages"][-4:])

    # Stream response token by token
    print("AI: ", end="", flush=True)
    # o/p - AI: 


    full_response = ""
    # state['messages] = [chunk1, chunk2, chunk3, chunk4]  <-- Wrong!

    # response = llm.invoke(context) <-- wait, get all.
    # response = llm.stream(context) <-- get one by one.
    for chunk in llm.stream(context):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_response += chunk.content

    print()  # New line after streaming completes

    # Create AIMessage with full response
    response = AIMessage(content=full_response)

    # Update counters
    return {
        "messages": [response],
        "turn_count": state["turn_count"] + 1,
        "window_count": state["window_count"] + 1
    }

# ============================================================================
# NODE 2: Summarizer (Non-streaming - faster for background task)
# ============================================================================

def summarizer_node(state: ConversationState):
    """Compresses older messages - uses invoke for speed"""

    older_messages = state["messages"][:-4]

    if not older_messages:
        return {"window_count": 0}

    # Check summary size and re-compress if needed
    MAX_SUMMARY_LENGTH = 1000

    existing_summary = state.get("summary", "")

    if len(existing_summary) > MAX_SUMMARY_LENGTH:
        compress_prompt = f"""This summary is too long. Compress to under 500 words:

{existing_summary}

Compressed summary:"""
        compressed = llm.invoke([HumanMessage(content=compress_prompt)])
        existing_summary = compressed.content

    # Build summarization prompt
    prompt = "Summarize this conversation in 2-3 sentences:\n\n"

    if existing_summary:
        prompt += f"Previous summary: {existing_summary}\n\nNew messages:\n"

    for msg in older_messages:
        role = "User" if isinstance(msg, HumanMessage) else "AI"
        prompt += f"{role}: {msg.content[:200]}...\n"  # Limit length

    # Generate summary (non-streaming for speed)
    summary = llm.invoke([HumanMessage(content=prompt)])

    print(f"\n[COMPRESSED] Older messages compressed into summary\n")

    return {
        "messages": state["messages"][-4:],
        "summary": summary.content,
        "window_count": 0
    }

# ============================================================================
# ROUTER: Same as before
# ============================================================================

def should_compress(state: ConversationState) -> Literal["summarizer", "end"]:
    """Check if compression is needed"""
    if state["window_count"] >= 3:
        return "summarizer"
    return "end"

# ============================================================================
# BUILD GRAPH
# ============================================================================

graph = StateGraph(ConversationState)
graph.add_node("chat", chat_node_streaming)  # Uses streaming version
graph.add_node("summarizer", summarizer_node)

graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", should_compress, {"summarizer": "summarizer", "end": END})
graph.add_edge("summarizer", END)

agent = graph.compile()

# ============================================================================
# RUN CONVERSATION
# ============================================================================

if __name__ == "__main__":
    print("\n=== Streaming Memory-Controlled Chatbot ===")
    print("Type 'quit' to exit")
    print("Watch the response appear token by token!\n")

    state = {
        "messages": [],
        "summary": "",
        "turn_count": 0,
        "window_count": 0
    }

    while True:
        user_input = input("You: ")

        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        # Add user message
        state["messages"].append(HumanMessage(content=user_input))

        # Run agent (streaming happens inside chat_node)
        result = agent.invoke(state)

        # Update state
        state = result

        # Show metrics
        print(f"[Turn {state['turn_count']} | Window: {state['window_count']} | Summary: {len(state['summary'])} chars]")
        print()
