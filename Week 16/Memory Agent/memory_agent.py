"""
Memory-Controlled Conversational Agent
Demonstrates automatic context compression in conversations
"""
# example - Annotated[list, 'this is a special type of list']
# example - Literal['yes', 'no']

from typing import TypedDict, Annotated, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os

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
    base_url="https://openrouter.ai/api/v1"
)

# ============================================================================
# STATE: Tracks conversation with compression
# ============================================================================

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Full conversation
    summary: str                                          # Compressed older context
    turn_count: int                                       # Total turns
    window_count: int                                     # Turns since last compression

# ============================================================================
# NODE 1: Chat - Handles conversation
# ============================================================================

def chat_node(state: ConversationState):
    """Main chat handler - uses summary + recent messages"""

    # Build context for LLM
    context = []

    # Add summary if it exists
    if state["summary"]:
        context.append(SystemMessage(content=f"Previous conversation: {state['summary']}"))

    # Add recent messages (last 4 messages)
    context.extend(state["messages"][-4:])

    # Get response
    response = llm.invoke(context)

    # Update counters
    return {
        "messages": [response],
        "turn_count": state["turn_count"] + 1,
        "window_count": state["window_count"] + 1
    }

# ============================================================================
# NODE 2: Summarizer - Compresses old messages
# ============================================================================

def summarizer_node(state: ConversationState):
    """Compresses older messages into summary"""

    # Get older messages (exclude last 4)
    older_messages = state["messages"][:-4]

    if not older_messages:
        return {"window_count": 0}

    # Build summarization prompt
    prompt = "Summarize this conversation in 2-3 sentences:\n\n"

    if state["summary"]:
        prompt += f"Previous summary: {state['summary']}\n\nNew messages:\n"

    for msg in older_messages:
        role = "User" if isinstance(msg, HumanMessage) else "AI"
        prompt += f"{role}: {msg.content}\n"

    # Generate summary
    summary = llm.invoke([HumanMessage(content=prompt)])

    print(f"\n[COMPRESSED] Older messages compressed into summary")

    # Keep only recent 4 messages, update summary, reset window counter
    return {
        "messages": state["messages"][-4:],
        "summary": summary.content,
        "window_count": 0
    }

# ============================================================================
# ROUTER: Decides when to compress
# ============================================================================

def should_compress(state: ConversationState) -> Literal["summarizer", "end"]:
    """Check if compression is needed (after 3 turns)"""
    if state["window_count"] >= 3:
        return "summarizer"
    return "end"

# ============================================================================
# BUILD GRAPH
# ============================================================================

graph = StateGraph(ConversationState)
graph.add_node("chat", chat_node)
graph.add_node("summarizer", summarizer_node)

graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", should_compress, {"summarizer": "summarizer", "end": END})
graph.add_edge("summarizer", END)

agent = graph.compile()

# ============================================================================
# RUN CONVERSATION
# ============================================================================

if __name__ == "__main__":
    print("\n=== Memory-Controlled Chatbot ===")
    print("Type 'quit' to exit\n")

    # Initialize state
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

        # Add user message to state
        state["messages"].append(HumanMessage(content=user_input))

        # Run agent
        result = agent.invoke(state)

        # Update state with result
        state = result

        # Print AI response
        ai_response = state["messages"][-1].content
        print(f"AI: {ai_response}")

        # Show metrics
        print(f"[Turn {state['turn_count']} | Window: {state['window_count']} | Summary: {len(state['summary'])} chars]")
        print()
