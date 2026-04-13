"""
Conversational Planner Agent (Multimodal-Ready)

Features:
- Multi-modal input support (Text/Voice/Image)
- Streaming responses
- Async-ready architecture
- Memory management
- Modality normalization layer

Architecture:
Input Router → Modality Processor → Planner → Memory Controller → END
"""

from typing import TypedDict, Annotated, Literal, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages  # reducer function (auto appending messages instead of replacing)
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")

if api_key:
    print('[INIT] API Key loaded successfully!')
else:
    print("[ERROR] OPENROUTER_API_KEY not found. Set it in .env file.")
    exit(1)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    streaming=True  # Enable streaming
)

# ============================================================================
# STATE: Multimodal-Ready State Structure
# ============================================================================

class MultimodalPlannerState(TypedDict):
    """
    Extended state for multimodal conversational planner.

    Core conversation:
    - messages: Full conversation history
    - summary: Compressed older context

    Multimodal support:
    - input_type: Which modality (text/voice/image)
    - raw_input_payload: Original input (text/file path/etc)
    - extracted_text: Normalized text from any modality
    - metadata: Extra info (confidence, language, etc)

    Counters:
    - total_turn_count: Lifetime conversation turns
    """
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str
    total_turn_count: int

    # Multimodal fields
    input_type: Literal["text", "voice", "image"] # voice -> text | image -> text
    raw_input_payload: str
    extracted_text: str
    metadata: Dict[str, Any]

# ============================================================================
# NODE 1: INPUT ROUTER
# ============================================================================

def input_router(state: MultimodalPlannerState) -> Literal["text_processor", "voice_processor", "image_processor"]:
    """
    Routes input based on modality type.

    Architecture principle:
    - Separate routing from processing
    - Each modality has dedicated processor
    - Enables future modality additions

    Returns:
        Node name to route to
    """
    input_type = state["input_type"]

    print(f"[ROUTER] Input type detected: {input_type}")

    if input_type == "text":
        return "text_processor"
    elif input_type == "voice":
        return "voice_processor"
    elif input_type == "image":
        return "image_processor"
    else:
        # Default to text
        print(f"[ROUTER] Unknown type '{input_type}', defaulting to text")
        return "text_processor"

# ============================================================================
# NODE 2: MODALITY PROCESSORS
# ============================================================================

def text_processor(state: MultimodalPlannerState):
    """
    Process text input (direct pass-through).

    Text is already in usable format, so we just extract it.
    """
    print("[TEXT PROCESSOR] Processing text input...")

    return {
        "extracted_text": state["raw_input_payload"],
        "metadata": {
            "processor": "text",
            "processed_at": datetime.now().isoformat()
        }
    }


def voice_processor(state: MultimodalPlannerState):
    """
    Process voice input (mock speech-to-text).

    Future implementation:
    - Use Whisper API for speech-to-text
    - Extract speaker diarization
    - Detect language
    - Calculate confidence scores

    Current: Mock transcription
    """
    print("[VOICE PROCESSOR] Processing voice input...")
    print(f"[VOICE PROCESSOR] Mock: Transcribing '{state['raw_input_payload']}'")

    # Mock transcription
    # In production: Call Whisper API
    transcribed_text = f"[Transcribed from voice]: {state['raw_input_payload']}"

    return {
        "extracted_text": transcribed_text,
        "metadata": {
            "processor": "voice",
            "mock_mode": True,
            "confidence": 0.95,
            "language": "en",
            "processed_at": datetime.now().isoformat()
        }
    }


def image_processor(state: MultimodalPlannerState):
    """
    Process image input (mock image captioning).

    Future implementation:
    - Use GPT-4 Vision for image understanding
    - Use BLIP/CLIP for image captioning
    - Extract objects, text (OCR), scenes
    - Generate detailed descriptions

    Current: Mock captioning
    """
    print("[IMAGE PROCESSOR] Processing image input...")
    print(f"[IMAGE PROCESSOR] Mock: Analyzing '{state['raw_input_payload']}'")

    # Mock image captioning
    # In production: Call GPT-4 Vision or BLIP
    caption = f"[Image description]: {state['raw_input_payload']}"

    return {
        "extracted_text": caption,
        "metadata": {
            "processor": "image",
            "mock_mode": True,
            "image_path": state["raw_input_payload"],
            "detected_objects": ["placeholder"],
            "processed_at": datetime.now().isoformat()
        }
    }

# ============================================================================
# NODE 3: CONVERSATIONAL PLANNER (CORE)
# ============================================================================

## V.V.imp! 

def planner_node(state: MultimodalPlannerState):
    """
    Core planning engine with streaming.

    Responsibilities:
    - Read conversation context (summary + recent messages)
    - Process normalized input (extracted_text)
    - Generate structured planning response
    - Stream output token-by-token

    Planning vs Chatting:
    - Not just answering questions
    - Breaking down tasks into steps
    - Providing structured plans
    - Asking clarifying questions
    """
    print("[PLANNER] Starting planning process...")

    # Build context
    context = []

    # Add summary if exists
    if state["summary"]:
        context.append(SystemMessage(content=f"""Previous conversation summary:
{state['summary']}

Continue helping the user with their planning needs."""))

    # Add recent messages (last 4)
    recent_messages = state["messages"][-4:] if len(state["messages"]) > 4 else state["messages"]
    context.extend(recent_messages)

    # Add current input (normalized from any modality)
    current_input = state["extracted_text"]

    # Add planning system prompt
    planning_prompt = f"""You are a conversational planning assistant.

Your role:
- Help users break down complex tasks into actionable steps
- Ask clarifying questions when needed
- Provide structured, organized plans
- Consider constraints and requirements
- Be concise but thorough

User input (may be from text, voice, or image):
{current_input}

Provide a helpful planning response:"""

    context.append(HumanMessage(content=planning_prompt))

    # Stream response
    print("Planner: ", end="", flush=True)

    full_response = ""
    for chunk in llm.stream(context):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_response += chunk.content

    print()  # Newline after streaming

    # Create response message
    response = AIMessage(content=full_response)

    return {
        "messages": [response],
        "total_turn_count": state["total_turn_count"] + 1
    }

# ============================================================================
# NODE 4: MEMORY CONTROLLER
# ============================================================================

def should_compress(state: MultimodalPlannerState) -> Literal["compress", "end"]:
    """
    Decide if memory compression is needed.

    Trigger: Every 5 turns
    """
    turn_count = state["total_turn_count"]

    # Compress every 5 turns
    if turn_count > 0 and turn_count % 5 == 0:
        print(f"[MEMORY] Compression triggered at turn {turn_count}")
        return "compress"

    return "end"


def memory_compressor(state: MultimodalPlannerState):
    """
    Compress older messages into summary.

    Same logic as streaming agent:
    - Keep recent messages
    - Summarize older messages
    - Merge with existing summary
    """
    print("[MEMORY] Compressing conversation history...")

    messages = state["messages"]

    # Keep last 4 messages
    older_messages = messages[:-4] if len(messages) > 4 else []

    if not older_messages:
        print("[MEMORY] No older messages to compress")
        return {}

    # Build summarization prompt
    existing_summary = state.get("summary", "")

    prompt = "Summarize this planning conversation in 3-4 sentences:\n\n"

    if existing_summary:
        prompt += f"Previous summary: {existing_summary}\n\nNew messages:\n"

    for msg in older_messages:
        role = "User" if isinstance(msg, HumanMessage) else "Planner"
        content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
        prompt += f"{role}: {content}\n"

    # Generate summary (non-streaming for speed)
    summary_response = llm.invoke([HumanMessage(content=prompt)])

    print(f"[MEMORY] Summary updated ({len(summary_response.content)} chars)")

    return {
        "messages": messages[-4:],  # Keep only recent
        "summary": summary_response.content
    }

# ============================================================================
# BUILD GRAPH
# ============================================================================

def create_planner_graph():
    """
    Construct the multimodal planner graph.

    Flow:
    START → Input Router → Modality Processor → Planner → Memory Check → [Compressor] → END
    """
    graph = StateGraph(MultimodalPlannerState)

    # Add modality processors
    graph.add_node("text_processor", text_processor)
    graph.add_node("voice_processor", voice_processor)
    graph.add_node("image_processor", image_processor)

    # Add core nodes
    graph.add_node("planner", planner_node)
    graph.add_node("compress", memory_compressor)

    # Set entry point with router
    graph.add_conditional_edges(
        START,
        input_router,
        {
            "text_processor": "text_processor",
            "voice_processor": "voice_processor",
            "image_processor": "image_processor"
        }
    )

    # All processors go to planner
    graph.add_edge("text_processor", "planner")
    graph.add_edge("voice_processor", "planner")
    graph.add_edge("image_processor", "planner")

    # Planner checks memory
    graph.add_conditional_edges(
        "planner",
        should_compress,
        {
            "compress": "compress",
            "end": END
        }
    )

    # After compression, end
    graph.add_edge("compress", END)

    return graph.compile()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Demo the conversational planner.

    Shows:
    - Text input processing
    - Mock voice input
    - Mock image input
    - Memory compression
    - Streaming responses
    """
    print("\n" + "="*80)
    print("CONVERSATIONAL PLANNER AGENT (Multimodal-Ready)")
    print("="*80)
    print("\nCommands:")
    print("  text: <message>   - Text input")
    print("  voice: <message>  - Mock voice input")
    print("  image: <desc>     - Mock image input")
    print("  quit              - Exit")
    print("="*80 + "\n")

    agent = create_planner_graph()

    # Initialize state
    state = {
        "messages": [],
        "summary": "",
        "total_turn_count": 0,
        "input_type": "text",
        "raw_input_payload": "",
        "extracted_text": "",
        "metadata": {}
    }

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == 'quit':
            print("\n[EXIT] Goodbye!\n")
            break

        if not user_input:
            continue

        # Parse input type
        if user_input.startswith("text:"):
            input_type = "text"
            payload = user_input[5:].strip()
        elif user_input.startswith("voice:"):
            input_type = "voice"
            payload = user_input[6:].strip()
        elif user_input.startswith("image:"):
            input_type = "image"
            payload = user_input[6:].strip()
        else:
            # Default to text
            input_type = "text"
            payload = user_input

        # Update state with new input
        state["input_type"] = input_type
        state["raw_input_payload"] = payload

        # Run agent
        result = agent.invoke(state)

        # Update state
        state = result

        # Show metrics
        print(f"\n[Turn {state['total_turn_count']} | Summary: {len(state.get('summary', ''))} chars | Type: {input_type}]")


if __name__ == "__main__":
    main()
