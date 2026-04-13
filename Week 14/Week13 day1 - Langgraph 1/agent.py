# All the imports
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os

load_dotenv()

if os.environ.get("OPENAI_API_KEY"):
    print('Key successfully loaded!')
else:
    print("OPENAI_API_KEY not found. Set it in .env file.")

# defining the state of our agent
class AgentState(TypedDict):
    user_message: HumanMessage

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    base_url="https://openrouter.ai/api/v1"
)

# purpose of this node is to pass the user's message to the LLM
def first_node(state: AgentState) -> AgentState:
    response = llm.invoke(state["user_message"])
    print(f"\nAI: {response.content}")
    return state

# BUILDING our graph
graph = StateGraph(AgentState)
graph.add_node("node1", first_node)
graph.add_edge(START, "node1")
graph.add_edge("node1", END)
agent = graph.compile()

if __name__ == "__main__":
    user_input = input("You: ")
    agent.invoke({"user_message": [HumanMessage(content=user_input)]})
