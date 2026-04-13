"""
Main Entry Point - LangGraph Tool Reuse Demo

PURPOSE:
Demonstrates running different graphs that share the same tools.

USAGE:
    python main.py qna "What is machine learning?"
    python main.py summarize "Summarize the key concepts"

NOTE:
Notice how we import BOTH graphs, and both work seamlessly.
They're using the SAME document search tool under the hood.
"""

import sys
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Import both graphs
from graphs import create_qna_graph, create_summarizer_graph


def print_separator():
    """Helper to make output readable."""
    print("\n" + "=" * 80 + "\n")


def run_qna_graph(question: str):
    """
    Run the Question Answering graph.

    Args:
        question: The question to answer
    """
    print("🤖 Starting QnA Bot (Graph A)")
    print_separator()

    # Create the graph
    # NOTE: Graph creation is cheap, it's just defining the workflow
    graph = create_qna_graph()

    # Prepare the input
    #  We pass messages in LangChain format
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "question": question
    }

    print(f"❓ Question: {question}\n")

    # Run the graph
    # The graph handles tool calls automatically
    result = graph.invoke(initial_state)

    # Extract and display the answer
    final_message = result["messages"][-1]
    print("💡 Answer:")
    print(final_message.content)
    print_separator()


def run_summarizer_graph(topic: str):
    """
    Run the Summarizer graph.

    Args:
        topic: The topic or instruction to summarize
    """
    print("📝 Starting Summarizer Bot (Graph B)")
    print_separator()

    # Create the graph
    # This uses the SAME tool as QnA, different behavior
    graph = create_summarizer_graph()

    # Prepare the input
    initial_state = {
        "messages": [HumanMessage(content=topic)],
        "topic": topic
    }

    print(f"📋 Request: {topic}\n")

    # Run the graph
    result = graph.invoke(initial_state)

    # Extract and display the summary
    final_message = result["messages"][-1]
    print("📄 Summary:")
    print(final_message.content)
    print_separator()


def print_usage():
    """Print usage instructions."""
    print("""
LangGraph Tool Reuse Demo
=========================

This demo shows how to build reusable tools and use them across multiple graphs.

USAGE:
    python main.py qna "<question>"
        Runs the QnA bot (Graph A) to answer factual questions

    python main.py summarize "<topic/instruction>"
        Runs the Summarizer bot (Graph B) to create summaries

EXAMPLES:
    python main.py qna "What is machine learning?"
    python main.py qna "What are the applications of ML?"
    python main.py summarize "Summarize the key concepts"
    python main.py summarize "Give me an overview of the main topics"

ENVIRONMENT:
    Set these environment variables:
    - OPENAI_API_KEY: Your OpenRouter API key
    - OPENAI_BASE_URL: https://openrouter.ai/api/v1
    """)


def main():
    """Main entry point."""

    # Load environment variables
    load_dotenv()

    # Verify environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("Please set your OpenRouter API key:")
        print("  export OPENAI_API_KEY='your_api_key'")
        print("  export OPENAI_BASE_URL='https://openrouter.ai/api/v1'")
        sys.exit(1)

    # Parse command line arguments
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    user_input = sys.argv[2]

    # Route to the appropriate graph
    if command == "qna":
        run_qna_graph(user_input)
    elif command in ["summarize", "summary"]:
        run_summarizer_graph(user_input)
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()

