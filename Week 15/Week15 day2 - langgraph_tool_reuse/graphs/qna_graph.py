"""
Graph A: Question Answering Bot

PURPOSE:
This graph answers factual questions using document retrieval.

ARCHITECTURE:
    User Question
         ↓
    [Agent Node] ← Decides to use tool
         ↓
    [Document Search ToolNode] ← SHARED/REUSED
         ↓
    [Agent Node] ← Answers using retrieved context
         ↓
    Answer

WHY THIS GRAPH EXISTS:
- Defines the BEHAVIOR for question answering
- Reuses the CAPABILITY (document search) defined elsewhere
- Can be modified independently of other graphs

NOTE:
This graph doesn't define the tool - it IMPORTS it.
Multiple graphs can import and use the same tool.
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# IMPORT THE SHARED TOOL
# This is the key to reusability - we don't redefine it, we import it
from tools import get_document_search_node, create_document_search_tool


# Define the graph state
class QnAState(TypedDict):
    """
    State for the QnA graph.

    WHY TypedDict?
    - Type safety: Catches errors early
    - Clear contract: Other developers know what data flows through
    - IDE support: Better autocomplete and hints
    """
    messages: Annotated[list, add_messages] # appending (updating not replacing).
    # The question we're trying to answer
    question: str


def create_qna_graph():
    """
    Create the Question Answering graph.

    GRAPH FLOW:
    1. User asks a question
    2. Agent decides to search documents
    3. Tool retrieves relevant chunks
    4. Agent synthesizes answer from chunks

    Returns:
        A compiled LangGraph
    """

    # Initialize LLM for the agent
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0,  # Low temperature for factual QnA
    )

    # Bind the tool to the LLM
    # WHY? This allows the LLM to decide when to call the tool
    tool = create_document_search_tool()
    llm_with_tools = llm.bind_tools([tool])

    def agent_node(state: QnAState):
        """
        Agent node: Decides whether to search docs or answer the question.

        WHY THIS NODE?
        - Implements the "thinking" part of the graph
        - Decides when to use tools
        - Synthesizes final answers

        NOTE:
        The agent doesn't implement the search - it CALLS the tool.
        This separation is key to reusability.
        """
        messages = state["messages"]

        # Add system prompt for QnA behavior
        system_message = SystemMessage(content="""You are a helpful question-answering assistant.

Your job:
1. When given a question, use the search_documents tool to find relevant information
2. Answer the question based ONLY on the retrieved documents
3. If the documents don't contain the answer, say so clearly
4. Be concise and factual

Remember: You must search the documents first, then answer based on what you find.""")

        # Call the LLM with tools
        response = llm_with_tools.invoke([system_message] + messages)
        return {"messages": [response]}

    def should_continue(state: QnAState):
        """
        Router function: Decides whether to call tools or end.

        WHY THIS FUNCTION?
        - LangGraph needs to know: "Should we call a tool or are we done?"
        - This is ROUTING LOGIC - it belongs in the GRAPH, not the TOOL

        NOTE
        Tools don't decide when they're called - graphs do.
        This keeps tools simple and reusable.
        """
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM wants to call a tool, route to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, we're done
        return END

    # Build the graph
    workflow = StateGraph(QnAState)

    # Add nodes
    # NOTE: Notice we GET the tool node, not CREATE it
    # This ensures we're using the SAME tool as other graphs
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", get_document_search_node())

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edges
    # Conditional edge: agent → tools OR end
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

    # After tools, always go back to agent
    # WHY? The agent needs to see the tool results and formulate an answer
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


# ARCHITECTURE NOTES:
# 1. This graph defines BEHAVIOR (how to answer questions)
# 2. It IMPORTS the tool (doesn't redefine it)
# 3. The routing logic (should_continue) is HERE, not in the tool
# 4. If we change the tool implementation, this graph still works
# 5. We can create new graphs using the same tool without duplication



"""
Student question -> How does the LLM know when to CALL THE tool?

ANSWER -:

User -> What is python?

LLM -> I need information about that(query).
    -> Generates the tool call.

Graph -> routes to the tool node 

"""
