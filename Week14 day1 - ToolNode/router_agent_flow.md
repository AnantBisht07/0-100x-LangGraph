"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      ROUTER AGENT WITH CONDITIONAL EDGES                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

THE VISUAL FLOW:

    [User types a question]
          │
          ▼
    ┌─────────────┐
    │   ROUTER    │  LLM classifies: "search" or "explain"
    │   NODE      │  Returns AIMessage(content="search") or
    │             │  AIMessage(content="explain")
    └─────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │        CONDITIONAL EDGE                      │
    │  route_by_intent() reads the router output  │
    │  and returns a KEY: "search" or "explain"   │
    │                                              │
    │  The path map decides which node runs next: │
    │    "search"  → go to search_caller          │
    │    "explain" → go to explanation             │
    └─────────────────────────────────────────────┘
          │                           │
          ▼                           ▼
    ┌──────────────┐          ┌──────────────┐
    │ SEARCH       │          │ EXPLANATION  │
    │ CALLER       │          │ NODE         │
    │              │          │              │
    │ LLM (with    │          │ LLM (plain)  │
    │ tools) says  │          │ directly     │
    │ "call        │          │ explains the │
    │ search_web   │          │ concept      │
    │ with query=  │          │              │
    │ ..."         │          │ OUTPUT:      │
    │              │          │ AIMessage    │
    │ OUTPUT:      │          │ (the answer) │
    │ AIMessage    │          └──────────────┘
    │ (tool_calls) │                │
    └──────────────┘                ▼
          │                        END
          ▼
    ┌──────────────┐
    │ SEARCH       │
    │ EXECUTOR     │
    │ (ToolNode)   │
    │              │
    │ ACTUALLY     │
    │ runs the     │
    │ search_web   │
    │ function     │
    │              │
    │ OUTPUT:      │
    │ ToolMessage  │
    │ (raw results)│
    └──────────────┘
          │
          ▼
    ┌──────────────────┐
    │ ANSWER WITH      │
    │ SEARCH NODE      │
    │                  │
    │ LLM (plain)     │
    │ reads raw search │
    │ results and     │
    │ writes a clean  │
    │ answer          │
    │                  │
    │ OUTPUT:          │
    │ AIMessage        │
    │ (final answer)  │
    └──────────────────┘
          │
          ▼
         END



"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║           OUTPUT WALKTHROUGH — HOW THE AGENT ACTUALLY RUNS                     ║
╚══════════════════════════════════════════════════════════════════════════════════╝

Let's trace TWO real runs step by step to see exactly what happens inside.

══════════════════════════════════════════════════════════════════════════════════
 RUN 1: "What is 1to10x?"  →  EXPLAIN PATH
══════════════════════════════════════════════════════════════════════════════════

  You type:  what is 1to10x?

  STEP 1 — agent.invoke() starts the graph
  ──────────────────────────────────────────
    Initial state:
      messages = [HumanMessage("what is 1to10x?")]

    The graph starts at START, which has an edge to "router".
    So router_node runs first.


  STEP 2 — router_node runs
  ──────────────────────────
    WHAT HAPPENS:
      - Reads state["messages"][-1].content → "what is 1to10x?"
      - Sends this prompt to base_llm (plain LLM, no tools):
          "You are an intent classifier... User query: what is 1to10x?"
      - The LLM sees "what is..." → this is asking for an explanation.
      - LLM responds: AIMessage(content="explain")

    CONSOLE OUTPUT:
      [Router] Intent classified as: 'explain'

    STATE AFTER:
      messages = [
        HumanMessage("what is 1to10x?"),
        AIMessage("explain")               ← router added this
      ]


  STEP 3 — Conditional edge fires
  ─────────────────────────────────
    WHAT HAPPENS:
      - router_node finished → LangGraph checks: what's the next edge?
      - It finds: add_conditional_edges("router", route_by_intent, {...})
      - So it calls: route_by_intent(state)

    INSIDE route_by_intent:
      - Reads state["messages"][-1].content → "explain"
      - .strip().lower() → "explain"
      - "search" in "explain"? → NO
      - Returns "explain"

    LANGGRAPH LOOKS UP PATH MAP:
      {"search": "search_caller", "explain": "explanation"}
      Key "explain" → next node is "explanation"

    So the graph goes to explanation_node. The entire search path is SKIPPED.
    search_caller, search_executor, answer_with_search — NONE of them run.


  STEP 4 — explanation_node runs
  ───────────────────────────────
    WHAT HAPPENS:
      - Reads state["messages"][0].content → "what is 1to10x?"
        (Uses [0] to get the ORIGINAL user question, not the router's "explain")
      - Sends to base_llm:
          "You are a helpful teacher. Explain the following concept...
           Question: what is 1to10x?"
      - LLM responds with the explanation (even though it doesn't really
        know what 1to10x is, it tries its best — this is LLM hallucination,
        not a code problem)

    STATE AFTER:
      messages = [
        HumanMessage("what is 1to10x?"),
        AIMessage("explain"),
        AIMessage("**1to10x** is a simple multiplication...")  ← explanation
      ]


  STEP 5 — END
  ─────────────
    explanation_node has an edge to END → graph stops.

    result = agent.invoke(...) returns the final state.
    result["messages"][-1].content → the explanation text.
    This is what gets printed as "Answer:".


  FULL CONSOLE OUTPUT:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  You: what is 1to10x?                                               │
  │                                                                      │
  │    [Router] Intent classified as: 'explain'                          │
  │                                                                      │
  │  Answer:                                                             │
  │  **1to10x** is a simple multiplication concept where you multiply   │
  │  a number by a factor between 1 and 10...                           │
  └──────────────────────────────────────────────────────────────────────┘

  NODES THAT RAN:      router_node → explanation_node → END (2 nodes)
  NODES THAT SKIPPED:  search_caller, search_executor, answer_with_search
  TOTAL MESSAGES:      3 (Human + "explain" + explanation)


══════════════════════════════════════════════════════════════════════════════════
 RUN 2: "Who founded OpenAI?"  →  SEARCH PATH
══════════════════════════════════════════════════════════════════════════════════

  You type:  Who founded OpenAI?

  STEP 1 — agent.invoke() starts the graph
  ──────────────────────────────────────────
    Initial state:
      messages = [HumanMessage("Who founded OpenAI?")]

    START → router_node runs.


  STEP 2 — router_node runs
  ──────────────────────────
    WHAT HAPPENS:
      - Reads "Who founded OpenAI?"
      - Sends classification prompt to base_llm.
      - LLM sees "Who founded..." → factual question about a real company.
      - LLM responds: AIMessage(content="search")

    CONSOLE OUTPUT:
      [Router] Intent classified as: 'search'

    STATE AFTER:
      messages = [
        HumanMessage("Who founded OpenAI?"),
        AIMessage("search")                    ← router added this
      ]


  STEP 3 — Conditional edge fires
  ─────────────────────────────────
    WHAT HAPPENS:
      - LangGraph calls route_by_intent(state)
      - Reads state["messages"][-1].content → "search"
      - "search" in "search"? → YES
      - Returns "search"

    PATH MAP LOOKUP:
      "search" → "search_caller"

    So the graph goes to search_tool_node_caller.
    The explanation_node is SKIPPED entirely.


  STEP 4 — search_tool_node_caller runs
  ──────────────────────────────────────
    WHAT HAPPENS:
      - Reads state["messages"][0].content → "Who founded OpenAI?"
      - Sends to tool_llm (LLM with search_web bound):
          "Search for factual information about: Who founded OpenAI?"
      - tool_llm sees it has a search tool available.
      - Instead of answering, it REQUESTS a tool call:
          AIMessage(
            content="",
            tool_calls=[{
              "name": "search_web",
              "args": {"query": "Who founded OpenAI?"}
            }]
          )

    KEY POINT: No search has happened yet!
    The LLM only WROTE A REQUEST. Like filling out an order form.

    STATE AFTER:
      messages = [
        HumanMessage("Who founded OpenAI?"),
        AIMessage("search"),
        AIMessage(tool_calls=[{search_web, "Who founded OpenAI?"}])  ← REQUEST
      ]


  STEP 5 — search_executor (ToolNode) runs
  ──────────────────────────────────────────
    WHAT HAPPENS:
      - Reads state["messages"][-1] → the AIMessage with tool_calls.
      - Sees: {name: "search_web", args: {query: "Who founded OpenAI?"}}
      - Finds search_web in its tool list.
      - ACTUALLY CALLS: search_web("Who founded OpenAI?")
      - Inside search_web:
          → DDGS().text("Who founded OpenAI?", max_results=3) runs
          → DuckDuckGo returns 3 real web results
          → Joins the "body" text of each result with newlines
          → Returns the joined string
      - ToolNode wraps the result in a ToolMessage.

    CONSOLE OUTPUT:
      [Tool Executing] search_web(query='Who founded OpenAI?')

    THIS IS WHERE THE REAL DATA COMES FROM!
    The actual internet search happens HERE, not in any other node.

    STATE AFTER:
      messages = [
        HumanMessage("Who founded OpenAI?"),
        AIMessage("search"),
        AIMessage(tool_calls=[...]),
        ToolMessage("OpenAI was founded in December 2015 as a non-profit │
                     organization by Sam Altman, Elon Musk, Ilya...")     ← REAL DATA
      ]


  STEP 6 — answer_with_search_node runs
  ──────────────────────────────────────
    WHAT HAPPENS:
      - Reads state["messages"][-1].content → the raw search snippets
        from DuckDuckGo (messy, multiple paragraphs).
      - Sends to base_llm (plain LLM, NO tools):
          "Using the search results below, write a clear and concise
           answer... Search results: OpenAI was founded in December 2015..."
      - LLM reads the raw snippets and writes a polished answer.
      - Returns AIMessage with the clean summary.

    WHY base_llm here?
      We already HAVE the search results. If we used tool_llm, the LLM
      might try to search AGAIN instead of just summarizing. base_llm
      has no tools, so it can only generate text.

    STATE AFTER:
      messages = [
        HumanMessage("Who founded OpenAI?"),
        AIMessage("search"),
        AIMessage(tool_calls=[...]),
        ToolMessage("OpenAI was founded in December 2015..."),
        AIMessage("OpenAI was founded in December 2015 as a non-profit   │
                   organization by Sam Altman, Elon Musk, Ilya           │
                   Sutskever, Greg Brockman...")                ← FINAL ANSWER
      ]


  STEP 7 — END
  ─────────────
    answer_with_search_node has an edge to END → graph stops.

    result["messages"][-1].content → the polished answer.
    This is what gets printed.


  FULL CONSOLE OUTPUT:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  You: Who founded OpenAI?                                            │
  │                                                                      │
  │    [Router] Intent classified as: 'search'                           │
  │    [Tool Executing] search_web(query='Who founded OpenAI?')          │
  │                                                                      │
  │  Answer:                                                             │
  │  OpenAI was founded in December 2015 as a non-profit organization   │
  │  by Sam Altman, Elon Musk, Ilya Sutskever, Greg Brockman, and      │
  │  Trevor Blackwell...                                                │
  └──────────────────────────────────────────────────────────────────────┘

  NODES THAT RAN:      router → search_caller → search_executor
                       → answer_with_search → END (4 nodes)
  NODES THAT SKIPPED:  explanation
  TOTAL MESSAGES:      5 (Human + "search" + tool_calls + ToolMessage + answer)


══════════════════════════════════════════════════════════════════════════════════
 SIDE-BY-SIDE COMPARISON
══════════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────┬────────────────────────────────────────────────┐
  │                      │  "What is 1to10x?"    │  "Who founded OpenAI?"│
  ├──────────────────────┼───────────────────────┼───────────────────────┤
  │ Router output        │  "explain"            │  "search"             │
  │ route_by_intent()    │  returns "explain"    │  returns "search"     │
  │ Path taken           │  EXPLAIN path         │  SEARCH path          │
  │ Nodes executed       │  router → explanation │  router → caller →   │
  │                      │                       │  executor → answer   │
  │ Nodes skipped        │  caller, executor,    │  explanation          │
  │                      │  answer_with_search   │                       │
  │ Tool called?         │  NO                   │  YES (DuckDuckGo)     │
  │ Internet used?       │  NO                   │  YES                  │
  │ Messages in state    │  3                    │  5                    │
  │ LLM calls made       │  2 (router + explain) │  3 (router + caller  │
  │                      │                       │     + answer)         │
  │ Source of answer     │  LLM's training data  │  Live web results    │
  └──────────────────────┴───────────────────────┴───────────────────────┘

  KEY TAKEAWAY:
    The SAME code (agent.invoke) takes COMPLETELY different paths
    depending on the user's question. That's the power of conditional
    routing — one graph, multiple behaviors.

══════════════════════════════════════════════════════════════════════════════════
 WHY THE CONSOLE PRINTS LOOK DIFFERENT
══════════════════════════════════════════════════════════════════════════════════

  EXPLAIN PATH — You see:
    [Router] Intent classified as: 'explain'
    Answer: ...

    Only ONE print statement fires (from router_node).
    The search tool never runs, so [Tool Executing] never appears.

  SEARCH PATH — You see:
    [Router] Intent classified as: 'search'
    [Tool Executing] search_web(query='...')
    Answer: ...

    TWO print statements fire:
    1. [Router] from router_node's print()
    2. [Tool Executing] from search_web's print()

    The second print PROVES the tool actually ran and hit DuckDuckGo.
    If you only see [Router] but not [Tool Executing], it means the
    conditional edge sent you to the explain path instead.

══════════════════════════════════════════════════════════════════════════════════
"""
