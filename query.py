"""
query.py
--------
The core RAG logic for the Financial Document Q&A system.

Uses:
- pypdf        : extracts text from uploaded PDFs
- chromadb     : stores chunks and searches by meaning (handles embeddings internally)
- anthropic    : sends relevant chunks + question to Claude for an answer

Two main functions that app.py will call:
1. ingest_document() - called when user uploads a PDF
2. answer_question() - called when user asks a question
"""

import uuid
import anthropic
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from io import BytesIO

# ── Configuration ──────────────────────────────────────────────────────────────

# Where ChromaDB saves its data on your Mac
CHROMA_PATH = "./chroma_db"

# How many characters per chunk (roughly half a page of text)
CHUNK_SIZE = 1000

# How many characters to overlap between chunks so sentences
# don't get cut off at chunk boundaries
CHUNK_OVERLAP = 200

# How many chunks to retrieve when answering a question.
# We grab the 5 most relevant chunks and send them all to Claude.
TOP_K_RESULTS = 5

# ── Initialize clients once ────────────────────────────────────────────────────
# These are created once when the file loads, then reused for every
# function call — more efficient than reconnecting every time.

print("Initializing clients...")

# Anthropic client for question answering
# Automatically reads ANTHROPIC_API_KEY from your environment
anthropic_client = anthropic.Anthropic()

# ChromaDB's built-in embedding function
# This uses a lightweight model that runs locally — no API key needed
# It handles converting text to numbers entirely on its own
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Connect to ChromaDB — creates the chroma_db folder if it doesn't exist
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

print("Ready.")


# ── Step 1: Extract text from PDF ─────────────────────────────────────────────

def extract_text(file_bytes: BytesIO) -> str:
    """
    Reads a PDF from memory and returns all its text as one big string.

    'file_bytes' is the raw bytes of the uploaded PDF.
    pypdf reads each page and we join them all together with a newline.
    """
    reader = PdfReader(file_bytes)
    pages_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text:  # skip blank pages
            pages_text.append(text)

    full_text = "\n".join(pages_text)
    return full_text


# ── Step 2: Split text into chunks ────────────────────────────────────────────

def split_into_chunks(text: str) -> list[str]:
    """
    Splits a long string of text into smaller overlapping chunks.

    Example with CHUNK_SIZE=10, CHUNK_OVERLAP=2:
    Text:   "Hello World Example"
    Chunk1: "Hello Worl"
    Chunk2: "rld Exampl"  <- starts 2 chars back from where chunk1 ended
    Chunk3: "ple"

    The overlap ensures no sentence gets completely cut in half.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        if chunk.strip():  # skip chunks that are only whitespace
            chunks.append(chunk)

        # Move forward by chunk_size minus the overlap
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ── Step 3: Ingest document into ChromaDB ─────────────────────────────────────

def ingest_document(file_bytes: BytesIO, filename: str) -> str:
    """
    Called by app.py when a user uploads a PDF.

    Takes the file, processes it, stores everything in ChromaDB,
    and returns a unique collection_id.

    What is collection_id?
    - Think of it like a folder name inside ChromaDB
    - Each uploaded document gets its own unique folder
    - app.py saves this ID so it knows which folder to search later
    - We use uuid to generate a random unique ID like 'doc_a3f7b291c0e2'
    """
    print(f"\nIngesting: {filename}")

    # Extract all text from the PDF
    text = extract_text(file_bytes)
    print(f"Extracted {len(text):,} characters from {filename}")

    # Split into chunks
    chunks = split_into_chunks(text)
    print(f"Created {len(chunks)} chunks")

    # Generate a unique ID for this document's collection
    # uuid4() creates a random string — guaranteed to be unique every time
    collection_id = f"doc_{uuid.uuid4().hex[:12]}"

    # Delete the collection if it somehow already exists (shouldn't happen,
    # but this prevents duplicate data if something goes wrong)
    try:
        chroma_client.delete_collection(collection_id)
    except Exception:
        pass

    # Create a new collection with our embedding function
    # ChromaDB will automatically convert our text chunks to numbers
    # using the embedding_fn we defined above — we don't have to do it manually
    collection = chroma_client.create_collection(
        name=collection_id,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Add all chunks to the collection
    # ChromaDB handles the embedding conversion automatically here
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    print(f"Stored {len(chunks)} chunks in collection: {collection_id}")
    return collection_id


# ── Step 4: Answer a question ─────────────────────────────────────────────────

def answer_question(question: str, collection_id: str) -> str:
    """
    Called by app.py when a user types a question.

    1. Gets the right ChromaDB collection for the current document
    2. Searches for the 5 most relevant chunks (ChromaDB handles embedding the
       question automatically using the same embedding_fn)
    3. Builds a prompt with those chunks as context
    4. Sends it to Claude and returns the answer
    """

    # Get the collection we stored this document in
    collection = chroma_client.get_collection(
        name=collection_id,
        embedding_function=embedding_fn
    )

    # Search for the most relevant chunks
    # ChromaDB automatically converts the question to an embedding
    # using embedding_fn, then finds the closest matching chunks
    results = collection.query(
        query_texts=[question],
        n_results=TOP_K_RESULTS
    )

    # Pull out the actual text from the results
    # results["documents"] is a list of lists — [0] gets the inner list
    retrieved_chunks = results["documents"][0]

    # Join all chunks into one block of context text
    # The "---" separator helps Claude see where one chunk ends and another begins
    context = "\n\n---\n\n".join(retrieved_chunks)

    # Build the prompt we'll send to Claude.
    # Key instruction: "use ONLY the excerpts below"
    # This prevents Claude from making things up from its training data
    # and keeps all answers grounded in the actual document.
    prompt = f"""You are a financial analyst assistant helping users understand SEC filings and annual reports.

Use ONLY the document excerpts below to answer the question. If the answer is not found in the excerpts, say clearly that the information is not available in the provided document — do not guess or use outside knowledge.

DOCUMENT EXCERPTS:
{context}

USER QUESTION:
{question}

ANSWER:"""

    # Send to Claude and get the response
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


# ── Cleanup helper ─────────────────────────────────────────────────────────────

def delete_collection(collection_id: str) -> None:
    """
    Deletes a ChromaDB collection when the user uploads a new document
    or clears the session. Keeps disk usage clean.
    """
    try:
        chroma_client.delete_collection(collection_id)
        print(f"Deleted collection: {collection_id}")
    except Exception:
        pass
