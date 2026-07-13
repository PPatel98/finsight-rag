# 🔍 FinSight RAG — Financial Document Intelligence

> **Module 1 of [FinSight AI](#finsight-ai-platform)** — a personal financial intelligence platform built for real investment research.

Upload any SEC filing, annual report, or financial PDF and ask plain-English questions about it. Get answers grounded directly in the document — no hallucination, no guessing.

---

## 💡 Why I Built This

As someone learning to invest, I found financial documents overwhelming — 10-Ks run 80+ pages of dense legal and financial language. I wanted a way to ask plain-English questions and get answers backed by the actual document, not generic AI responses from training data.

This project solves that. It also demonstrates a production-ready RAG (Retrieval-Augmented Generation) architecture — the same pattern used by financial services companies like Wells Fargo, Bank of America, and Truist to build document intelligence systems at scale.

---

## 🎯 What It Does

- Upload **any financial PDF** — 10-K, annual report, earnings release, S-1
- Ask **plain-English questions** about the document
- Get **accurate, document-grounded answers** from Claude (Anthropic)
- **Multi-turn conversation** — ask follow-up questions in context
- **Session isolation** — each uploaded document gets its own vector collection
- **Persistent storage** — ChromaDB saves chunks to disk between sessions

---

## 🏗️ Architecture

```
User uploads PDF
      ↓
pypdf extracts text from every page
      ↓
Text split into 1,000-character overlapping chunks
(200-character overlap prevents context loss at boundaries)
      ↓
ChromaDB converts chunks to embeddings using built-in embedding function
and stores them in a persistent local vector database
      ↓
User asks a question
      ↓
ChromaDB converts question to embedding using same function
and retrieves top 5 most semantically similar chunks
      ↓
Retrieved chunks + question sent to Claude (claude-sonnet-4-6)
with prompt that restricts answers to document content only
      ↓
Claude's answer displayed in Streamlit chat interface
```

### Key architectural decisions

**Session isolation via UUID collections**
Each uploaded document gets a unique ChromaDB collection (`doc_a3f7b291c0e2`), preventing data mixing across sessions and enabling clean document switching.

**Overlapping chunking strategy**
Chunks overlap by 200 characters to prevent information loss at boundaries — a common failure point in naive chunking implementations.

**Grounded prompting**
The system prompt explicitly restricts Claude to only use retrieved document excerpts, preventing hallucination from training data. If the answer isn't in the document, Claude says so.

**Provider-agnostic design**
The embedding layer (ChromaDB) and LLM layer (Anthropic) are separated and independently swappable. Switching to AWS Bedrock or Azure OpenAI requires changing one line of configuration — important for enterprise deployment where the LLM provider is often dictated by security policy.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Anthropic Claude (claude-sonnet-4-6) |
| **Vector Database** | ChromaDB (persistent, local) |
| **Embeddings** | ChromaDB DefaultEmbeddingFunction |
| **PDF Processing** | pypdf |
| **Frontend** | Streamlit |
| **Language** | Python 3.12 |

---

## 📋 Example Questions

Once you upload a 10-K or annual report, try asking:

- *"What was total revenue last fiscal year?"*
- *"What are the biggest risk factors mentioned?"*
- *"How does the company describe its AI strategy?"*
- *"What drove revenue growth this year?"*
- *"How much cash does the company have on hand?"*
- *"What segments does the business operate in?"*
- *"Did the company mention any ongoing legal proceedings?"*

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12
- An Anthropic API key ([get one here](https://console.anthropic.com))

### Installation

**1. Clone the repo**
```bash
git clone https://github.com/PPatel98/finsight-rag.git
cd finsight-rag
```

**2. Create and activate a virtual environment**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set your Anthropic API key**
```bash
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zprofile
source ~/.zprofile
```

**5. Run the app**
```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

### Usage
1. Upload any financial PDF using the sidebar
2. Wait ~30 seconds for the document to process
3. Ask questions in the chat box
4. Upload a new document anytime to switch context

---

## 📁 Project Structure

```
finsight-rag/
├── app.py              # Streamlit UI and session state management
├── query.py            # Core RAG logic — ingestion and question answering
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🧠 How RAG Works (Plain English)

**The problem with asking an LLM about a document directly:**
You'd have to send the entire document every time you ask a question. A single 10-K can be 150,000+ tokens — expensive, slow, and hits context window limits.

**What RAG does instead:**
1. Break the document into small chunks and store them in a vector database
2. When a question comes in, find only the most relevant chunks (typically 5)
3. Send just those chunks to the LLM as context
4. The LLM answers based only on what was retrieved

**Why this is better:**
- Only ~700 tokens sent per question instead of 150,000+
- No context window limits — works on documents of any size
- Answers are grounded in the actual document — not the LLM's training data
- The database persists — no need to re-upload documents between sessions

---

## 🔗 FinSight AI Platform

This project is **Module 1** of FinSight AI — a suite of AI tools for personal investment research.

| Module | Repo | Description | Status |
|---|---|---|---|
| 1 — Document Intelligence | [finsight-rag](https://github.com/PPatel98/finsight-rag) | Ask questions about any financial PDF | ✅ Complete |
| 2 — Research Agent | finsight-agent | Autonomous multi-source company research | 🔨 In Progress |
| 3 — Eval Framework | finsight-evals | Measure and validate AI answer quality | 📋 Planned |
| 4 — Risk Pipeline | finsight-risk | ML-based financial risk scoring | 📋 Planned |
| 5 — Dashboard | finsight-dashboard | Unified investment research hub | 📋 Planned |

---

## 👤 Author

**Parth Patel** — Software Engineer transitioning into AI/ML Engineering

- LinkedIn: [linkedin.com/in/parth-p75](https://linkedin.com/in/parth-p75)
- GitHub: [github.com/PPatel98](https://github.com/PPatel98)
