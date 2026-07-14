# FinSight RAG: Financial Document Q&A

Module 1 of FinSight AI, a personal financial intelligence platform I built to support my own investment research.

This tool lets you upload any SEC filing or financial PDF and ask plain-English questions about it. Answers are grounded directly in the document using a RAG (Retrieval-Augmented Generation) pipeline backed by ChromaDB and Anthropic's Claude.

---

## What it does

- Accepts any financial PDF: 10-K, annual report, earnings release, S-1
- Splits the document into chunks, embeds them, and stores them in a local vector database
- On each question, retrieves the most semantically relevant chunks and passes them to Claude as context
- Returns answers sourced strictly from the document, not Claude's training data
- Maintains conversation history within a session
- Each uploaded document gets its own isolated ChromaDB collection, so switching documents is clean

---

## Architecture

```
PDF upload
    |
    v
pypdf extracts full text
    |
    v
Text split into 1,000-character chunks with 200-character overlap
    |
    v
ChromaDB converts chunks to embeddings and stores them on disk
    |
    v
User submits a question
    |
    v
ChromaDB retrieves top 5 most semantically similar chunks
    |
    v
Chunks and question sent to Claude with a prompt that restricts
the answer to the retrieved content only
    |
    v
Answer displayed in Streamlit chat interface
```

**Session isolation:** Each document upload generates a UUID-based ChromaDB collection name. This prevents data from different documents mixing and allows clean document switching mid-session.

**Chunking overlap:** The 200-character overlap between chunks prevents information from being lost at chunk boundaries, which is a common failure point in naive chunking approaches.

**Grounded prompting:** The system prompt explicitly tells Claude to use only the retrieved excerpts. If the answer is not in the document, Claude says so rather than pulling from training data.

**Provider-agnostic design:** The embedding layer and LLM layer are decoupled. Switching from Anthropic to AWS Bedrock or Azure OpenAI requires changing one line of configuration, which matters in enterprise environments where the LLM provider is often set by security policy.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude (claude-sonnet-4-6) |
| Vector database | ChromaDB (persistent, local) |
| Embeddings | ChromaDB DefaultEmbeddingFunction |
| PDF processing | pypdf |
| Frontend | Streamlit |
| Language | Python 3.12 |

---

## Setup

**Requirements:** Python 3.12 and an Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

```bash
# Clone the repo
git clone https://github.com/PPatel98/finsight-rag.git
cd finsight-rag

# Create and activate a virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zprofile
source ~/.zprofile

# Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload any financial PDF from the sidebar and start asking questions.

---

## Example questions

These work well against any company's 10-K or annual report:

- What was total revenue last fiscal year?
- What are the biggest risk factors the company identifies?
- How does the company describe its AI or technology strategy?
- What drove revenue growth or decline this year?
- How much cash and equivalents does the company hold?
- What business segments does the company operate in?
- Are there any ongoing legal proceedings mentioned?

---

## Project structure

```
finsight-rag/
    app.py              Streamlit UI and session state management
    query.py            Core RAG logic: ingestion and question answering
    requirements.txt    Python dependencies
    README.md           This file
```

---

## Part of FinSight AI

This is Module 1 of a larger platform I am building for personal investment research. Each module is a standalone project that builds on the same architectural patterns.

| Module | Repo | Description | Status |
|---|---|---|---|
| 1 - Document Intelligence | [finsight-rag](https://github.com/PPatel98/finsight-rag) | Ask questions about any financial PDF | Complete |
| 2 - Research Agent | finsight-agent | Autonomous multi-source company research | In progress |

---

## Author

Parth Patel, Software Engineer

- LinkedIn: [linkedin.com/in/parth-p75](https://linkedin.com/in/parth-p75)
- GitHub: [github.com/PPatel98](https://github.com/PPatel98)
