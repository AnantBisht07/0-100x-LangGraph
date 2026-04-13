"""
tools.py — Agent tools, each decorated with @traceable.

Every tool call appears as its own SPAN in LangSmith.
This means you can see exactly which tool was called,
what input it received, and what it returned — all in one trace.

In a real production system these would call:
  - search_tool    → a search API (Serper, Tavily, Google)
  - calculator_tool → a math evaluation service
  - weather_tool   → a weather API
"""

from langsmith import traceable


@traceable(name="Search Tool", run_type="tool")
def search_tool(query: str) -> str:
    """
    Simulate a web search.

    Returns structured fake results so the demo works without an API key.
    In production: replace with Serper / Tavily / SerpAPI call.

    Args:
        query: The search query string.

    Returns:
        Simulated search results as a formatted string.
    """
    # Simulated knowledge base for demo purposes
    knowledge = {
        "langsmith":   "LangSmith is an observability platform by LangChain. "
                       "It records every run, trace, and span of your AI system.",
        "mcp":         "Model Context Protocol (MCP) is a structured approach to "
                       "context injection — deciding what data enters the LLM "
                       "and what stays out.",
        "langchain":   "LangChain is a framework for building LLM-powered "
                       "applications. It includes chains, agents, and tools.",
        "openai":      "OpenAI provides GPT models via API. gpt-4o-mini is a "
                       "fast, cost-efficient model suitable for most tasks.",
        "python":      "Python is a high-level programming language widely used "
                       "in AI, data science, and web development.",
        "agent":       "An AI agent is a system that perceives its environment, "
                       "reasons about it, and takes actions to achieve a goal.",
    }

    query_lower = query.lower()
    for keyword, result in knowledge.items():
        if keyword in query_lower:
            return f"Search results for '{query}':\n{result}"

    return (
        f"Search results for '{query}':\n"
        "No specific results found. Try rephrasing your query."
    )


@traceable(name="Calculator Tool", run_type="tool")
def calculator_tool(expression: str) -> str:
    """
    Evaluate a safe mathematical expression.

    Args:
        expression: A math expression string e.g. '2 + 2' or '10 * 5'.

    Returns:
        The result as a string, or an error message.
    """
    # Only allow safe characters to prevent code injection
    allowed = set("0123456789+-*/()., ")
    if not all(c in allowed for c in expression):
        return f"Error: unsafe characters in expression '{expression}'"

    try:
        result = eval(expression)  # noqa: S307 — safe: filtered above
        return f"Result of '{expression}' = {result}"
    except Exception as e:
        return f"Calculator error: {e}"


@traceable(name="Tool Router", run_type="chain")
def dispatch_tool(tool_name: str, query: str) -> str:
    """
    Route a tool call to the correct function.

    Args:
        tool_name: 'search' or 'calculator'.
        query:     The input for the tool.

    Returns:
        Tool output string.
    """
    if tool_name == "search":
        return search_tool(query)
    elif tool_name == "calculator":
        return calculator_tool(query)
    else:
        return f"Unknown tool: '{tool_name}'"
