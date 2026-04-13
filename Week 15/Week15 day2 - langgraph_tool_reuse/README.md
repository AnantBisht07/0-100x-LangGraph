# LangGraph Tool Reuse Demo

## Purpose
This project demonstrates **TOOL REUSE** across multiple LangGraph workflows.
Build tools ONCE, use them in MANY graphs.

## Architecture

```
┌─────────────────────────────────────┐
│   Shared Tool Layer (Capabilities)  │
│   - Document Search ToolNode        │
└─────────────────────────────────────┘
           ↑              ↑
           │              │
     ┌─────┴───┐     ┌────┴─────┐
     │ Graph A │     │ Graph B  │
     │ QnA Bot │     │Summarizer│
     └─────────┘     └──────────┘
```

## Key Concepts

1. **ToolNode = Capability**: The document search tool is a capability that can be used by any graph
2. **Graph = Behavior**: Each graph defines HOW to use the tool (QnA vs Summary)
3. **Reusability**: Write once, import everywhere
4. **Separation of Concerns**: Tools don't know about routing, graphs don't duplicate tool logic.

## Project Structure

```
langgraph_tool_reuse/
├── tools/
│   ├── __init__.py
│   └── document_search.py      # Reusable document search ToolNode
├── graphs/
│   ├── __init__.py
│   ├── qna_graph.py            # Graph A: Question Answering
│   └── summarizer_graph.py     # Graph B: Summarization
├── data/
│   └── sample_docs/            # Place your .txt or .pdf files here
├── main.py                     # Run either graph
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your_openrouter_api_key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
```

3. Add documents to `data/sample_docs/`

## Usage

### Run QnA Bot (Graph A)
```bash
python main.py qna "What is machine learning?"
```

### Run Summarizer Bot (Graph B)
```bash
python main.py summarize "Summarize the key concepts"
```

##

- **Why separate tools from graphs?** Reusability, testability, maintainability
- **Why ToolNode?** LangGraph's way of wrapping LangChain tools
- **Why no routing in tools?** Tools are capabilities, graphs define behavior
- **Why this matters?** In production, you'll have dozens of tools and many graphs
