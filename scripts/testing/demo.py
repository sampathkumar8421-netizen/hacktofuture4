"""
Example: Ollama + Supabase Integration Demo

This script demonstrates the full workflow of connecting Ollama with Supabase:
1. Setup the database with vector extension
2. Generate embeddings with Ollama
3. Store in Supabase
4. Search using similarity
5. Chat with RAG (Retrieval-Augmented Generation)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ollama_supabase import OllamaClient, SupabaseClient, setup_env


def demo():
    """Run a complete demo of Ollama + Supabase integration."""

    # Load environment
    load_dotenv("new.env", override=True)
    db_url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")

    if not db_url:
        print("Error: DIRECT_URL not found in new.env")
        sys.exit(1)

    print("=" * 60)
    print("Ollama + Supabase PostgreSQL Integration Demo")
    print("=" * 60)

    # Initialize clients
    print("\n1. Initializing Ollama client...")
    ollama = OllamaClient()

    print("\n2. Initializing Supabase client...")
    supabase = SupabaseClient(db_url)

    # Setup vector extension
    print("\n3. Setting up pgvector extension...")
    try:
        supabase.setup_vector_extension()
    except Exception as e:
        print(f"   (Extension may already exist: {e})")

    # Create embeddings table
    print("\n4. Creating documents table...")
    try:
        supabase.create_embeddings_table("documents", dimension=768)
    except Exception as e:
        print(f"   (Table may already exist: {e})")

    # Sample documents
    documents = [
        {
            "content": "Ollama is an open-source project that makes it easy to run large language models locally on your machine.",
            "metadata": {"topic": "ai", "category": "tools"}
        },
        {
            "content": "Supabase is an open-source Firebase alternative that provides PostgreSQL database, authentication, and real-time subscriptions.",
            "metadata": {"topic": "database", "category": "backend"}
        },
        {
            "content": "PostgreSQL is a powerful, open-source object-relational database system with over 35 years of active development.",
            "metadata": {"topic": "database", "category": "sql"}
        },
        {
            "content": "Vector embeddings are numerical representations of text that capture semantic meaning and enable similarity search.",
            "metadata": {"topic": "ml", "category": "embeddings"}
        },
        {
            "content": "Retrieval-Augmented Generation (RAG) combines information retrieval with text generation to produce more accurate responses.",
            "metadata": {"topic": "ai", "category": "rag"}
        }
    ]

    # Generate and store embeddings
    print(f"\n5. Generating embeddings for {len(documents)} documents...")
    for i, doc in enumerate(documents, 1):
        print(f"   Processing document {i}/{len(documents)}...", end=" ")
        embedding = ollama.generate_embeddings(doc["content"])
        doc_id = supabase.insert_document(
            "documents",
            content=doc["content"],
            embedding=embedding,
            metadata=doc["metadata"]
        )
        print(f"stored with ID: {doc_id}")

    # Demonstrate similarity search
    print("\n6. Testing similarity search...")
    query = "What is RAG and how does it work?"
    print(f"   Query: '{query}'")

    query_embedding = ollama.generate_embeddings(query)
    results = supabase.similarity_search("documents", query_embedding, limit=3)

    print(f"\n   Top 3 similar documents:")
    for r in results:
        print(f"   - Similarity: {r['similarity']:.4f} | {r['content'][:60]}...")

    # Demonstrate RAG chat
    print("\n7. Testing RAG chat...")
    question = "Tell me about databases"
    print(f"   Question: '{question}'")

    # Get context
    query_embedding = ollama.generate_embeddings(question)
    context_docs = supabase.similarity_search("documents", query_embedding, limit=2)
    context = "\n".join([d["content"] for d in context_docs])

    # Generate response
    prompt = f"""Answer the following question based ONLY on the provided context.
If the context doesn't contain the answer, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""

    print("   Generating response with Ollama...")
    answer = ollama.generate(prompt)
    print(f"\n   Answer: {answer}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try: python ollama_supabase.py search 'your query'")
    print("  - Try: python ollama_supabase.py chat 'your question'")
    print("  - Try: python ollama_supabase.py list")


if __name__ == "__main__":
    demo()
