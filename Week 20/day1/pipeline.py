"""
pipeline.py — Multi-step agent pipeline with full LangSmith observability.

Every function is decorated with @traceable.
This means LangSmith records each step as a SPAN inside the parent TRACE.

The trace tree you will see in LangSmith dashboard:
    ┌─ Agent Pipeline  [run_type: chain]
    │   ├─ Router           [run_type: chain]  → decides: search or chat
    │   ├─ Tool Executor    [run_type: tool]   → calls search/calculator
    │   ├─ Context Builder  [run_type: chain]  → MCP structured context
    │   └─ LLM Call         [run_type: llm]    → GPT response

Each span shows:
    - input
    - output
    - latency
    - token usage (for LLM spans)

    
"""

import config
from context_manager import ContextManager
from tools import dispatch_tool
from langsmith import traceable
from openai import OpenAI

# OpenRouter is OpenAI-compatible — same SDK, different base_url + key
_client = OpenAI(
    api_key  = config.OPENROUTER_API_KEY,
    base_url = config.OPENROUTER_BASE_URL,
    default_headers = {
        "HTTP-Referer": config.OPENROUTER_SITE_URL,
        "X-Title":      config.OPENROUTER_APP_NAME,
    },
)
_ctx_manager = ContextManager()

# Keywords that trigger the search tool
_SEARCH_TRIGGERS = [
    "search", "find", "look up", "what is", "who is",
    "explain", "tell me about", "how does", "define",
]

# Keywords that trigger the calculator tool
_CALC_TRIGGERS = [
    "calculate", "compute", "what is", "how much is",
    "+", "-", "*", "/", "percent", "%",
]


# ── Step 1: Router ────────────────────────────────────────────────────────────

@traceable(name="Router", run_type="chain")
def route_query(query: str) -> dict:
    """
    Classify the user query to decide the execution path.

    Returns:
        {
            "type":  "search" | "calculator" | "chat",
            "query": <original query>
        }
    """
    q = query.lower()

    # Check calculator first (more specific)
    if any(t in q for t in _CALC_TRIGGERS) and any(c in q for c in "0123456789"):
        return {"type": "calculator", "query": query}

    # Then check search
    if any(t in q for t in _SEARCH_TRIGGERS):
        return {"type": "search", "query": query}

    # Default: direct LLM chat
    return {"type": "chat", "query": query}


# ── Step 2: Tool Executor ─────────────────────────────────────────────────────

@traceable(name="Tool Executor", run_type="tool")
def execute_tool(tool_type: str, query: str) -> str | None:
    """
    Run the appropriate tool if the router requested one.

    Returns None for 'chat' type (no tool needed).
    """
    if tool_type == "chat":
        return None
    return dispatch_tool(tool_type, query)


# ── Step 3: Context Builder (MCP) ─────────────────────────────────────────────

@traceable(name="Context Builder (MCP)", run_type="chain")
def build_context_step(
    user_id:     str,
    messages:    list[dict],
    query:       str,
    tool_result: str | None,
) -> dict:
    """
    MCP layer — build the structured context for the LLM.

    Returns a dict with the context string and token estimate for logging.
    """
    context = _ctx_manager.build_context(user_id, messages, query, tool_result)
    tokens  = _ctx_manager.get_token_estimate(context)
    return {
        "context":        context,
        "token_estimate": tokens,
    }


# ── Step 4: LLM Call ──────────────────────────────────────────────────────────

@traceable(name="LLM Call", run_type="llm")
def call_llm(context: str) -> str:
    """
    Send structured MCP context to the LLM and return response.

    The context is passed as a SYSTEM message — this is important.
    It means the LLM receives a fully structured briefing, not raw history.
    """
    response = _client.chat.completions.create(
        model       = config.LLM_MODEL,
        messages    = [{"role": "system", "content": context}],
        temperature = 0.7,
        max_tokens  = 500,
    )
    return response.choices[0].message.content.strip()


# ── Master Pipeline ───────────────────────────────────────────────────────────

@traceable(name="Agent Pipeline", run_type="chain")
def run_pipeline(
    user_id:  str,
    messages: list[dict],
    query:    str,
) -> dict:
    """
    Full agent pipeline — the entry point for every user turn.

    Flow:
        User Input → Router → Tool (optional) → MCP Context → LLM → Response

    Args:
        user_id:  Unique user identifier (used to load profile + memory).
        messages: Full conversation history so far.
        query:    Current user message.

    Returns:
        {
            "response":       <LLM response string>,
            "route":          <"search" | "calculator" | "chat">,
            "tool_result":    <tool output or None>,
            "token_estimate": <rough token count of the context>
        }
    """
    # Step 1 — Route
    route = route_query(query)

    # Step 2 — Tool (if needed)
    tool_result = execute_tool(route["type"], query)

    # Step 3 — MCP Context Building
    ctx_data = build_context_step(user_id, messages, query, tool_result)

    # Step 4 — LLM
    response = call_llm(ctx_data["context"])

    return {
        "response":       response,
        "route":          route["type"],
        "tool_result":    tool_result,
        "token_estimate": ctx_data["token_estimate"],
    }
