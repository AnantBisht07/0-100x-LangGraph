import os
from typing import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode # execution of tool calls.

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from ddgs import DDGS # duck duck go search

load_dotenv()

# -----------------------------
# 1. State
# -----------------------------
class AgentState(TypedDict):
    messages: list

# -----------------------------
# 2. Tool
# -----------------------------
@tool # LLM Can now able to see this part. It is adding some labels + wrapper. So this function is very very special, treat this differently.
def search_tool(query: str) -> str:
    """Search for factual information about a query."""
    print(f"[Tool Called] query: {query}")
    results = DDGS().text(query, max_results=3) # who is the founder of OpenAI. 
    if not results:
        return f"No search results found for: {query}"
    return "\n".join(r["body"] for r in results)
    # DuckDuck Go response -
# --------------------------------------------------------------------------
#      {                                                             │
# │         "title": "Tesla (company) - Wikipedia",                    │
# │         "href": "https://en.wikipedia.org/wiki/Tesla,_Inc.",       │
# │         "body": "Tesla, Inc. was founded in July 2003 by..."      │
# │       }, 
# --------------------------------------------------------------------------


# -----------------------------
# 3. LLM
# -----------------------------
base_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="qwen/qwen3-coder-flash",
    temperature=0
)
# llm = base_llm.bind_tools([search_tool])
"""
Bind tools, does not execute any tool.
it only tells the LLM that tools exist.
working of bind_tools() - 
1). taking the list of tools(search tool, etc).
2). extracting each tools's schema(name, desc, param).
3). creates new LLM wrapper, that attach these schemas to every api request sent to the model.
"""

# -----------------------------
# 4. Decision node (CALLS TOOL)
# -----------------------------
def decision_node(state: AgentState):
    user_query = state["messages"][-1].content

    response = llm.invoke([
        HumanMessage(
            content=f"Search for factual information about: {user_query}"
        )
    ])

    return {"messages": [response]}

"""
 state  The shared state dict              
 state["messages"]        → The list of all messages           
 state["messages"][-1]    → The LAST message in the list  
"""

# -----------------------------
# 5. Tool node
# Creates a instance of tool node, giving it access to our search_tool function.
# -----------------------------
tool_node = ToolNode([search_tool])

# -----------------------------
# 6. Answer node
# -----------------------------
def answer_node(state: AgentState):
    search_result = state["messages"][-1].content

    final_response = base_llm.invoke([
        HumanMessage(
            content=f"Use the following search result to answer clearly:\n{search_result}"
        )
    ])

    return {"messages": [final_response]}

# -----------------------------
# 7. Graph
# -----------------------------
graph = StateGraph(AgentState)

graph.add_node("decision", decision_node)
graph.add_node("search", tool_node)
graph.add_node("answer", answer_node)

graph.add_edge(START, "decision")
graph.add_edge("decision", "search")
graph.add_edge("search", "answer")
graph.add_edge("answer", END)

agent = graph.compile()

# -----------------------------
# 8. Run
# -----------------------------
if __name__ == "__main__":
    user_input = input("You: ")

    result = agent.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    print("\nAnswer:")
    print(result["messages"][-1].content)
