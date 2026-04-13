# Example Output

This document shows what you'll see when running the demo.

## First Run: Initializing Vector Store

```bash
$ python main.py qna "What is machine learning?"
```

### Output:
```
🔧 Initializing vector store from data/sample_docs...
Scanning directory: 100%|██████████| 1/1 [00:00<00:00, 45.12it/s]
📚 Loaded 1 documents
✂️  Split into 12 chunks
✅ Vector store initialized with 12 chunks

🤖 Starting QnA Bot (Graph A)
================================================================================

❓ Question: What is machine learning?

💡 Answer:
Machine learning is a subset of artificial intelligence that enables systems to
learn and improve from experience without being explicitly programmed. According
to the documents, it focuses on developing computer programs that can access data
and use it to learn for themselves.

Key aspects include:
- Supervised Learning: Learning from labeled data to make predictions
- Unsupervised Learning: Finding patterns in unlabeled data
- Neural Networks: Computing systems inspired by biological neural networks
- Deep Learning: ML based on artificial neural networks with multiple layers

Machine learning algorithms build models based on sample data (training data) to
make predictions or decisions without being explicitly programmed to do so.

================================================================================
```

## Second Run: Using Cached Vector Store

```bash
$ python main.py summarize "Summarize AI applications"
```

### Output:
```
📝 Starting Summarizer Bot (Graph B)
================================================================================

📋 Request: Summarize AI applications

📄 Summary:
AI has diverse applications across multiple industries:

**Healthcare**
- Disease diagnosis and prediction
- Drug discovery and development
- Personalized treatment planning
- Medical imaging analysis

**Finance**
- Fraud detection systems
- Algorithmic trading
- Credit scoring
- Risk assessment

**Transportation**
- Autonomous vehicles
- Traffic prediction and optimization
- Route optimization
- Predictive maintenance

**Entertainment**
- Recommendation systems (Netflix, Spotify)
- Content generation
- Game AI
- Personalized advertising

These applications demonstrate how AI is transforming various sectors by
automating complex tasks, providing personalized experiences, and enabling
data-driven decision making.

================================================================================
```

## Comparing Both Outputs

### QnA Bot (Graph A)
- **Style**: Direct, factual answer
- **Structure**: Bullet points with definitions
- **Tone**: Precise and technical
- **Temperature**: 0 (no creativity)
- **Goal**: Answer the specific question accurately

### Summarizer Bot (Graph B)
- **Style**: Organized summary with sections
- **Structure**: Categories with multiple points
- **Tone**: Overview-oriented
- **Temperature**: 0.3 (slight creativity)
- **Goal**: Synthesize key information

### What's the Same?
Both used the **EXACT SAME** `search_documents` tool to retrieve information from the vector store!

## Additional Examples

### QnA: Specific Question
```bash
$ python main.py qna "What is natural language processing?"
```

```
💡 Answer:
Natural Language Processing (NLP) is a branch of AI that helps computers
understand, interpret, and manipulate human language. It bridges the gap
between human communication and computer understanding.

Key applications include:
- Chatbots and virtual assistants
- Sentiment analysis
- Machine translation
- Text summarization
- Named entity recognition
```

### Summarizer: Broad Topic
```bash
$ python main.py summarize "Give me an overview of AI ethics"
```

```
📄 Summary:
**Ethical Considerations in AI**

As AI becomes more prevalent, several important ethical questions arise:

- **Privacy**: Concerns with data collection and usage
- **Bias**: Potential for algorithmic bias affecting decisions
- **Employment**: Job displacement due to automation
- **Accountability**: Determining responsibility for AI decisions
- **Transparency**: Need for explainability in AI systems

These considerations are crucial for ensuring AI development aligns with
human values and societal needs.
```

### Error Handling: No Relevant Documents
```bash
$ python main.py qna "What is quantum computing?"
```

```
💡 Answer:
I don't have information about quantum computing in the available documents.
The documents focus on AI, machine learning, and related topics. To answer
questions about quantum computing, I would need documents that cover that topic.
```

## Behind the Scenes: What's Happening

### First Tool Call (QnA)
```
[Agent] I need to search for "machine learning"
  ↓
[ToolNode] Calling search_documents("machine learning", k=3)
  ↓
[FAISS] Performing similarity search...
  ↓
[ToolNode] Returns 3 most relevant chunks:
  - Chunk 1: "Machine learning is a subset of AI..."
  - Chunk 2: "Key ML concepts include..."
  - Chunk 3: "Machine learning algorithms build..."
  ↓
[Agent] Receives chunks, synthesizes answer
```

### Second Tool Call (Summarizer)
```
[Agent] I need to search for "AI applications"
  ↓
[ToolNode] Calling search_documents("AI applications", k=3)
           ⭐ SAME FUNCTION AS QnA USED ⭐
  ↓
[FAISS] Performing similarity search...
  ↓
[ToolNode] Returns 3 most relevant chunks:
  - Chunk 1: "Healthcare: Disease diagnosis..."
  - Chunk 2: "Finance: Fraud detection..."
  - Chunk 3: "Transportation: Autonomous vehicles..."
  ↓
[Agent] Receives chunks, synthesizes SUMMARY (different behavior!)
```

## Performance Notes

### Vector Store Initialization
- **First run**: 2-3 seconds (loading, chunking, embedding)
- **Subsequent runs**: Instant (already in memory)
- **Production**: Would use persistent DB (Pinecone, Weaviate)

### Query Execution
- **Average time**: 3-5 seconds
  - 1-2s: LLM decides to use tool
  - 0.5s: Vector search (FAISS is fast!)
  - 1-2s: LLM synthesizes response
- **Cost**: ~$0.01 per query (depends on model and token usage)

### Memory Usage
- **Vector store**: ~50MB for 100 documents
- **Graph execution**: Minimal (stateless)


### Moment 1: Vector Store Initialization
```
🔧 Initializing vector store from data/sample_docs...
📚 Loaded 1 documents
✂️  Split into 12 chunks
✅ Vector store initialized with 12 chunks
```


### Moment 2: Same Tool, Different Outputs
Compare the QnA output (precise, factual) with the Summarizer output (organized, synthesized). Both used the SAME retrieval tool!


### Moment 3: Tool Transparency
The user never sees "calling search_documents tool" - it's handled internally by the graph. This is the beauty of LangGraph's agent pattern.

TOOLS are called automatically when needed. The graph orchestrates everything.

## Next Steps

Try these commands to see more:

```bash
# Factual questions
python main.py qna "What is supervised learning?"
python main.py qna "What are the branches of AI?"

# Summaries
python main.py summarize "Summarize the future of AI"
python main.py summarize "Overview of computer vision"

# Compare answers
python main.py qna "What is computer vision?"
python main.py summarize "Summarize computer vision"
```

Notice how the SAME information is presented differently based on the graph's behavior!
