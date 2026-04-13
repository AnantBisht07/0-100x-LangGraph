# Two Agent System: QnA → Summarizer

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from dotenv import load_dotenv
import os

load_dotenv()

if os.environ.get("OPENAI_API_KEY"):
    print('Key successfully loaded!')
else:
    print("OPENAI_API_KEY not found. Set it in .env file.")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    base_url="https://openrouter.ai/api/v1"
)

# Node 1: QnA Agent - answers the user's question
def qna_agent(state: MessagesState):
    system_msg = SystemMessage(content="You are a helpful QnA assistant. Answer the user's question in detail.")
    messages = [system_msg] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Node 2: Summarizer Agent - summarizes the QnA response
def summarizer_agent(state: MessagesState):
    system_msg = SystemMessage(content="You are a summarizer. Take the previous AI response and summarize it in 2-3 short bullet points.")
    messages = [system_msg] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Build the graph: QnA → Summarizer
graph = StateGraph(MessagesState)
graph.add_node("qna_agent", qna_agent)
graph.add_node("summarizer_agent", summarizer_agent)

graph.add_edge(START, "qna_agent")
graph.add_edge("qna_agent", "summarizer_agent")
graph.add_edge("summarizer_agent", END)

agent = graph.compile()

if __name__ == "__main__":
    user_input = input("You: ")
    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
    print("\n--- Final Output ---")
    print(f"AI: {result['messages'][-1].content}")
