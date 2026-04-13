# Quick Start Guide

## 1. Installation

```bash
# Navigate to project directory
cd langgraph_tool_reuse

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# Get your key from: https://openrouter.ai/keys
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxxx
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

## 3. Run the Examples

### Question Answering (Graph A)
```bash
python main.py qna "What is machine learning?"
python main.py qna "What are the applications of AI in healthcare?"
python main.py qna "What is natural language processing?"
```

### Summarization (Graph B)
```bash
python main.py summarize "Summarize the key concepts about AI"
python main.py summarize "Give me an overview of machine learning"
python main.py summarize "Summarize the ethical considerations of AI"
```

## 4. Add Your Own Documents

Place `.txt` files in the `data/sample_docs/` directory:

```bash
# Example
echo "Your content here" > data/sample_docs/my_document.txt
```

Then run the graphs again - they'll automatically use your new documents!

## 5. Understanding the Output

When you run a command, you'll see:

1. **Vector store initialization** (first run only):
   ```
   🔧 Initializing vector store from data/sample_docs...
   📚 Loaded X documents
   ✂️  Split into X chunks
   ✅ Vector store initialized
   ```

2. **Graph execution**:
   ```
   🤖 Starting QnA Bot (Graph  A)
   ❓Question: What is machine learning?
   💡 Answer: [The answer based on retrieved documents]
   ```

## 6. Key Files to Explore

explore files in this order:

1. **[tools/document_search.py](tools/document_search.py)** - The reusable tool
2. **[graphs/qna_graph.py](graphs/qna_graph.py)** - Graph A implementation
3. **[graphs/summarizer_graph.py](graphs/summarizer_graph.py)** - Graph B implementation
4. **[main.py](main.py)** - Entry point and usage examples

## 7. Troubleshooting

### "No documents found" error
- Check that `.txt` files exist in `data/sample_docs/`
- The code will create a sample document automatically if none exist

### API key errors
- Verify your `.env` file exists and contains valid credentials
- Check that you've activated your virtual environment

### Import errors
- Ensure you've installed all dependencies: `pip install -r requirements.txt`
- Check that you're in the correct directory

## 8. Next Steps

Try modifying the code:

1. **Change the system prompts** in the graph files to alter behavior
2. **Adjust the temperature** to see how it affects outputs
3. **Add a third graph** that reuses the same tool
4. **Modify the chunk size** in `document_search.py` to see retrieval changes

## 

1. **Tool Reuse**: Both graphs import the SAME tool - no duplication
2. **Separation of Concerns**: Tools define capabilities, graphs define behavior
3. **Scalability**: Adding new graphs doesn't require changing the tool
4. **Maintainability**: Bug fixes in the tool benefit all graphs
