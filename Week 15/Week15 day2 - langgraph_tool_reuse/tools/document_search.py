"""
Reusable Document Search Tool

WHY THIS FILE EXISTS:
- Defines the document search capability ONCE
- Can be imported and reused by multiple graphs
- No routing logic - just pure search functionality
- This is the "capability layer" of our architecture

NOTE : 
In production, you'll have many tools like this (web search, database query, API calls).
Each tool should be self-contained and reusable.
"""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode


# Global vector store - initialized once, reused by all graphs
_vector_store = None


def _initialize_vector_store(docs_path: str = "data/sample_docs"):
    """
    Initialize the vector store with documents.

    WHY GLOBAL STATE HERE?
    - Vector stores are expensive to create (embeddings cost time/money)
    - We initialize ONCE and reuse across all graphs
    - In production, you might use a persistent vector DB instead

    NOTE:
    This is NOT part of the tool itself - it's setup/infrastructure.
    The tool below just USES the vector store.
    """
    global _vector_store

    if _vector_store is not None:
        return _vector_store

    print(f"🔧 Initializing vector store from {docs_path}...")

    # Check if documents exist
    docs_dir = Path(docs_path)
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        # Create a sample document
        sample_file = docs_dir / "sample.txt"
        sample_file.write_text("""
Machine Learning Overview

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.

Key Concepts:
1. Supervised Learning: Learning from labeled data to make predictions
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Neural Networks: Computing systems inspired by biological neural networks
4. Deep Learning: ML based on artificial neural networks with multiple layers

Applications:
- Image recognition and computer vision
- Natural language processing
- Recommendation systems
- Predictive analytics
- Autonomous vehicles

Machine learning algorithms build a model based on sample data, known as training data, to make predictions or decisions without being explicitly programmed to do so.
        """)
        print(f"📝 Created sample document at {sample_file}")

    # Load documents from directory
    # NOTE: LangChain provides many loaders (PDF, CSV, JSON, etc.)
    loader = DirectoryLoader(
        docs_path,
        glob="**/*.txt",
        loader_cls=TextLoader,
        show_progress=True
    )
    documents = loader.load()

    if not documents:
        raise ValueError(f"No documents found in {docs_path}. Add .txt files to continue.")

    print(f"📚 Loaded {len(documents)} documents")

    # Split documents into chunks
    # WHY? LLMs have context limits, and smaller chunks = better retrieval
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    splits = text_splitter.split_documents(documents)
    print(f"✂️  Split into {len(splits)} chunks")

    # Create embeddings and vector store
    # NOTE: Embeddings convert text to vectors for semantic search
    embeddings = OpenAIEmbeddings()
    _vector_store = FAISS.from_documents(splits, embeddings)
    print(f"✅ Vector store initialized with {len(splits)} chunks\n")

    return _vector_store


@tool
def search_documents(query: str, k: int = 3) -> str:
    """
    Search through documents and return relevant chunks.

    WHY @tool DECORATOR?
    - Marks this as a LangChain tool
    - LangChain tools can be called by LLMs
    - ToolNode wraps these tools for use in LangGraph

    Args:
        query: The search query or question
        k: Number of relevant chunks to return (default: 3)

    Returns:
        A formatted string with relevant document chunks

    NOTE:
    This function has NO idea which graph is calling it.
    It's just a pure capability: "search and return results"
    """
    # Ensure vector store is initialized
    vector_store = _initialize_vector_store()

    # Perform similarity search
    # NOTE: This uses cosine similarity on embeddings
    results = vector_store.similarity_search(query, k=k)

    if not results:
        return "No relevant documents found."

    # Format results for the LLM
    formatted_results = []
    for i, doc in enumerate(results, 1):
        formatted_results.append(f"[Chunk {i}]\n{doc.page_content}\n")

    return "\n".join(formatted_results)


def create_document_search_tool():
    """
    Factory function to get the document search tool.

    WHY A FACTORY?
    - Encapsulation: Hides implementation details
    - Flexibility: Easy to swap implementations later
    - Clarity: Clear intent in code

    Returns:
        The search_documents tool function
    """
    # Initialize vector store when tool is created
    _initialize_vector_store()
    return search_documents


def get_document_search_node():
    """
    Create a ToolNode wrapping the document search tool.

    WHY THIS FUNCTION?
    - ToolNode is LangGraph's way of using LangChain tools in graphs
    - By defining this ONCE, we ensure both graphs use the SAME tool
    - No code duplication = single source of truth

    NOTE:
    This ToolNode can be imported by ANY graph.
    It's the bridge between LangChain (@tool) and LangGraph (ToolNode).

    Returns:
        A ToolNode containing the document search tool
    """
    tool = create_document_search_tool()
    return ToolNode([tool])


# ARCHITECTURE NOTES:
# 1. This file defines a CAPABILITY (document search)
# 2. It does NOT define HOW to use it (that's the graph's job)
# 3. It does NOT contain routing logic (which tool to call when)
# 4. It CAN be imported and reused by multiple graphs
# 5. Changes here affect ALL graphs using it (single source of truth)
