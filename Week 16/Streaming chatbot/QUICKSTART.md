# Quick Start - Streaming Memory-Controlled Chatbot

## 1. Setup

### Prerequisites
```bash
# Required packages
pip install langgraph langchain-openai langchain-core python-dotenv
```

### API Key Configuration
```bash
# Create .env file in this directory
echo OPENROUTER_API_KEY=your-key-here > .env
```

Or copy from parent directory:
```bash
copy "..\\.env" ".env"
```

## 2. Run

```bash
cd "c:\EADP\Week 16\Streaming Chatbot"
python streaming_memory_agent.py
```

## 3. Try It

```
=== Streaming Memory-Controlled Chatbot ===
Type 'quit' to exit
Watch the response appear token by token!

You: tell me about tokyo
AI: Tokyo is Japan's bustling capital, known for...
    ↑ Watch this appear word by word!

[Turn 1 | Window: 1 | Summary: 0 chars]

You: quit
Goodbye!
```

## 4. Experiment

### Test 1: Short Response (Streaming Less Visible)
```
You: hi
AI: Hello!  ← Fast, barely see streaming
```

### Test 2: Long Response (Streaming Very Visible)
```
You: explain the history of japan in detail
AI: Japan has a rich and complex history spanning thousands of years...
    ↑ Streaming very visible for long responses!
```

### Test 3: Compression Cycle
```
You: plan trip to tokyo
AI: [streams response]
[Turn 1 | Window: 1 | Summary: 0 chars]

You: what about kyoto
AI: [streams response]
[Turn 2 | Window: 2 | Summary: 0 chars]

You: and osaka
AI: [streams response]
[Turn 3 | Window: 3 | Summary: 0 chars]

[COMPRESSED] Older messages compressed into summary

You: best food in nara
AI: [streams response - knows about tokyo/kyoto via summary]
[Turn 4 | Window: 1 | Summary: 245 chars]
```

## 5. Compare with Non-Streaming

### Run Original (Non-Streaming)
```bash
cd ".."
python simple_memory_agent.py
```

### Run Streaming
```bash
cd "Streaming Chatbot"
python streaming_memory_agent.py
```

### Notice:
- Same memory management ✓
- Same compression logic ✓
- Different display experience ✓

## 6. File Structure

```
Streaming Chatbot/
├── streaming_memory_agent.py   ← Main code
├── README.md                    ← Overview
├── ARCHITECTURE.md              ← Technical details
├── COMPARISON.md                ← vs Non-streaming
├── QUICKSTART.md                ← This file
└── .env                         ← API key (create this)
```

## 7. Key Files to Read

1. **README.md** - Start here
2. **streaming_memory_agent.py** - Read the code
3. **ARCHITECTURE.md** - Understand how it works
4. **COMPARISON.md** - See differences from original

## 8. Common Issues

### Issue: No streaming visible
**Cause**: Response too short
**Solution**: Ask longer questions

### Issue: Output buffered (appears in chunks)
**Cause**: Terminal buffering
**Solution**: Check `flush=True` is present

### Issue: "OPENROUTER_API_KEY not found"
**Cause**: Missing .env file
**Solution**: Create .env with your API key

## 9. Learning Path

### Step 1: Run and Observe
- Run the streaming chatbot
- Watch tokens appear
- Notice immediate feedback

### Step 2: Compare
- Run non-streaming version
- Compare user experience
- Notice same total time

### Step 3: Read Code
- Open streaming_memory_agent.py
- Find the streaming loop (line ~60)
- Understand accumulation pattern

### Step 4: Understand Architecture
- Read ARCHITECTURE.md
- Understand: Same architecture, different display
- See layered design

### Step 5: Experiment
- Try modifying streaming format
- Add custom token processing
- Change display patterns

## 10. Next Steps

### Modify Streaming Display
```python
# Current:
print(chunk.content, end="", flush=True)

# Try adding color:
print(f"\033[32m{chunk.content}\033[0m", end="", flush=True)

# Try adding pauses:
import time
print(chunk.content, end="", flush=True)
time.sleep(0.01)  # Slow down streaming
```

### Add Streaming to Other Nodes
```python
# Try streaming in summarizer too
def summarizer_node(state):
    # ...
    for chunk in llm.stream([HumanMessage(content=prompt)]):
        # Process chunks
```

### Measure Performance
```python
import time

start = time.time()
result = agent.invoke(state)
elapsed = time.time() - start

print(f"Total time: {elapsed:.2f}s")
```

## 11. Understanding Output

### Normal Turn
```
You: your question
AI: streaming response appears here...
[Turn X | Window: Y | Summary: Z chars]
```

### Compression Turn
```
You: your question
AI: streaming response appears here...
[Turn X | Window: Y | Summary: Z chars]

[COMPRESSED] Older messages compressed into summary
```

### Metrics Explained
- **Turn**: Total conversation turns (never resets)
- **Window**: Turns since last compression (resets to 0)
- **Summary**: Size of compressed context in characters

## 12. Tips

✅ **Do:**
- Ask long questions to see streaming clearly
- Watch for compression after 3 turns
- Compare with non-streaming version
- Experiment with code modifications

❌ **Don't:**
- Expect instant full responses (still takes time)
- Confuse streaming with faster processing
- Forget to use `flush=True`
- Modify state structure without understanding

## 13. Help

### Documentation
- README.md - Overview and concepts
- ARCHITECTURE.md - Technical deep dive
- COMPARISON.md - Side-by-side with original

### Code Comments
The code has inline comments explaining:
- Why streaming is used
- How accumulation works
- Where flush is important

### Parent Directory
Compare with:
```
../simple_memory_agent.py - Non-streaming version
../STUDENT_GUIDE.md - Memory management concepts
```

## 14. Success Checklist

- [ ] Installed dependencies
- [ ] Created .env with API key
- [ ] Ran streaming chatbot successfully
- [ ] Saw tokens appear word by word
- [ ] Tested compression (3+ questions)
- [ ] Compared with non-streaming version
- [ ] Read ARCHITECTURE.md
- [ ] Understood: Streaming = display change, not architecture change

## Ready to Learn!

Start with **README.md**, then run the code and watch it stream! 🚀

---

**Remember**: Streaming changes the user experience, not how the agent thinks!
