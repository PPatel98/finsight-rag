"""
app.py
------
The Streamlit web interface for the RAG Financial Document Q&A system.

Run this to start the app:
    streamlit run app.py

Streamlit opens your browser automatically at http://localhost:8501
"""

import streamlit as st
from io import BytesIO
from query import ingest_document, answer_question, delete_collection

# ── Page configuration ─────────────────────────────────────────────────────────
# Must be the first Streamlit command in the file

st.set_page_config(
    page_title="Financial Document Q&A",
    page_icon="📊",
    layout="centered"
)

# ── Session State Setup ────────────────────────────────────────────────────────
# Streamlit re-runs the entire script from top to bottom every time
# the user does anything. Session state lets us remember things between
# those re-runs — like which document is loaded or what was asked before.

if "collection_id" not in st.session_state:
    st.session_state.collection_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_filename" not in st.session_state:
    st.session_state.current_filename = None

# ── Header ─────────────────────────────────────────────────────────────────────

st.title("📊 Financial Document Q&A")
st.markdown(
    "Upload any SEC filing, annual report, or financial PDF and ask "
    "questions about it in plain English."
)
st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
# The sidebar is a panel on the left side of the screen.
# We put the file uploader here so it stays visible while chatting.

with st.sidebar:
    st.header("📁 Upload Document")

    uploaded_file = st.file_uploader(
        label="Choose a PDF file",
        type=["pdf"],
        help="Upload any financial PDF — 10-K, annual report, earnings release, etc."
    )

    # Show which document is currently loaded
    if st.session_state.current_filename:
        st.success(f"✅ Loaded:\n{st.session_state.current_filename}")

    # Clear button — resets everything so user can start fresh
    if st.session_state.collection_id:
        if st.button("🗑️ Clear & upload new document"):
            delete_collection(st.session_state.collection_id)
            st.session_state.collection_id = None
            st.session_state.chat_history = []
            st.session_state.current_filename = None
            st.rerun()

    st.divider()

    st.markdown("**How it works:**")
    st.markdown(
        "1. Upload a financial PDF\n"
        "2. Wait ~30 seconds to process\n"
        "3. Ask any question about it\n"
        "4. Get answers from the document"
    )

    st.divider()

    st.markdown("**Example questions:**")
    st.markdown(
        "- What was total revenue last year?\n"
        "- What are the biggest risk factors?\n"
        "- How does the company describe its AI strategy?\n"
        "- What drove revenue growth this year?\n"
        "- How much cash does the company have?"
    )

# ── Handle File Upload ─────────────────────────────────────────────────────────
# This block runs whenever a file is uploaded.
# We check if it's a NEW file to avoid reprocessing on every re-run.

if uploaded_file is not None:
    is_new_file = uploaded_file.name != st.session_state.current_filename

    if is_new_file:
        # Clean up the old document if one was loaded
        if st.session_state.collection_id:
            delete_collection(st.session_state.collection_id)
            st.session_state.chat_history = []

        # Show a spinner while processing
        with st.spinner(f"Processing '{uploaded_file.name}'... please wait"):
            # Read uploaded file into memory as bytes
            file_bytes = BytesIO(uploaded_file.read())

            # Run the ingestion pipeline from query.py
            collection_id = ingest_document(file_bytes, uploaded_file.name)

            # Save results to session state
            st.session_state.collection_id = collection_id
            st.session_state.current_filename = uploaded_file.name

        st.success(f"✅ Ready! Ask your first question below.")

# ── Chat Interface ─────────────────────────────────────────────────────────────
# Only shows once a document has been loaded

if st.session_state.collection_id:

    st.subheader("💬 Ask a question about the document")

    # Display previous messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input box — pinned to bottom of screen like a real chat app
    # Returns the user's text when they hit Enter, None otherwise
    user_question = st.chat_input("Type your question here...")

    if user_question:
        # Show the user's question immediately
        with st.chat_message("user"):
            st.markdown(user_question)

        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question
        })

        # Get and display Claude's answer
        with st.chat_message("assistant"):
            with st.spinner("Searching document and generating answer..."):
                answer = answer_question(
                    question=user_question,
                    collection_id=st.session_state.collection_id
                )
            st.markdown(answer)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer
        })

# ── Empty state ────────────────────────────────────────────────────────────────
# What to show before any document is loaded

else:
    st.info("👈 Upload a PDF using the sidebar on the left to get started.")
