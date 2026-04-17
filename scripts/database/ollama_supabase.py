"""
Ollama + Supabase PostgreSQL Integration

This module provides integration between your local Ollama instance and Supabase PostgreSQL.
Supports embeddings, chat completions, and vector similarity search using pgvector.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import numpy as np
import psycopg
import requests
from dotenv import load_dotenv


class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._check_connection()

    def _check_connection(self) -> None:
        """Verify Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            if not models:
                print("Warning: No models found in Ollama. Run: ollama pull nomic-embed-text")
            else:
                print(f"Connected to Ollama. Available models: {[m['name'] for m in models]}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Cannot connect to Ollama at localhost:11434.\n"
                "Please ensure Ollama is running. Start it with: ollama serve"
            )

    def generate_embeddings(self, text: str, model: str = "nomic-embed-text") -> list[float]:
        """Generate embeddings for text using Ollama."""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def chat(self, messages: list[dict], model: str = "llama3.1", stream: bool = False) -> str:
        """Send chat completion request to Ollama."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": model, "messages": messages, "stream": stream},
            timeout=120
        )
        response.raise_for_status()
        if stream:
            return response
        return response.json()["message"]["content"]

    def generate(self, prompt: str, model: str = "llama3.1") -> str:
        """Generate text completion using Ollama."""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"]


class SupabaseClient:
    """Client for Supabase PostgreSQL with vector support."""

    def __init__(self, database_url: str):
        self.database_url = self._sanitize_database_url(database_url)

    @staticmethod
    def _sanitize_database_url(url: str) -> str:
        """Remove pgbouncer query param that psycopg doesn't support."""
        try:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                userinfo, hostpart = rest.split("@", 1)
                if ":" in userinfo:
                    user, pwd = userinfo.rsplit(":", 1)
                    if len(pwd) >= 2 and pwd.startswith("[") and pwd.endswith("]"):
                        pwd = pwd[1:-1]
                        url = f"{scheme}://{user}:{pwd}@{hostpart}"
        except ValueError:
            pass

        parts = urlsplit(url)
        if not parts.query:
            return url
        kept = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True)
                if k.lower() != "pgbouncer"]
        new_query = urlencode(kept, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    def execute(self, query: str, params: tuple = ()) -> list[tuple]:
        """Execute a SQL query and return results."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                try:
                    return cur.fetchall()
                except psycopg.ProgrammingError:
                    return []

    def setup_vector_extension(self) -> None:
        """Enable pgvector extension in Supabase."""
        self.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("pgvector extension enabled")

    def create_embeddings_table(self, table_name: str = "documents", dimension: int = 768) -> None:
        """Create a table for storing documents with vector embeddings."""
        # Drop existing table if needed
        self.execute(f"DROP TABLE IF EXISTS {table_name};")

        # Create table with vector support
        self.execute(f"""
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{{}}',
                embedding VECTOR({dimension}),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create index for similarity search
        self.execute(f"""
            CREATE INDEX ON {table_name}
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        print(f"Table '{table_name}' created with vector support (dimension: {dimension})")

    def insert_document(self, table_name: str, content: str, embedding: list[float],
                        metadata: dict | None = None) -> int:
        """Insert a document with its embedding."""
        metadata = metadata or {}
        embedding_str = f"[{','.join(map(str, embedding))}]"

        result = self.execute("""
            INSERT INTO documents (content, metadata, embedding)
            VALUES (%s, %s, %s::vector)
            RETURNING id;
        """, (content, json.dumps(metadata), embedding_str))

        return result[0][0] if result else -1

    def similarity_search(self, table_name: str, query_embedding: list[float],
                          limit: int = 5) -> list[dict]:
        """Find most similar documents using cosine similarity."""
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        rows = self.execute(f"""
            SELECT id, content, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM {table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (embedding_str, embedding_str, limit))

        return [
            {
                "id": row[0],
                "content": row[1],
                "metadata": row[2],
                "similarity": float(row[3])
            }
            for row in rows
        ]


def setup_env(env_file: str | None = None) -> str:
    """Load environment and return database URL."""
    if env_file:
        env_path = Path(env_file)
        if env_path.exists() and env_path.stat().st_size > 0:
            load_dotenv(env_path, override=True)

    database_url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DIRECT_URL/DATABASE_URL not set. Provide via env or --env-file")
    return database_url


def cmd_setup(db_url: str) -> None:
    """Setup vector extension and tables."""
    print("Setting up Supabase for vector storage...")
    supabase = SupabaseClient(db_url)
    supabase.setup_vector_extension()
    supabase.create_embeddings_table("documents", dimension=768)
    print("Setup complete!")


def cmd_embed(db_url: str, ollama: OllamaClient, text: str) -> None:
    """Generate embeddings for text and store in Supabase."""
    print(f"Generating embedding for: {text[:50]}...")

    embedding = ollama.generate_embeddings(text)
    print(f"Generated embedding with {len(embedding)} dimensions")

    supabase = SupabaseClient(db_url)
    doc_id = supabase.insert_document(
        "documents",
        content=text,
        embedding=embedding,
        metadata={"source": "cli", "model": "nomic-embed-text"}
    )
    print(f"Stored in Supabase with ID: {doc_id}")


def cmd_search(db_url: str, ollama: OllamaClient, query: str) -> None:
    """Search for similar documents."""
    print(f"Searching for: {query}")

    # Generate embedding for query
    query_embedding = ollama.generate_embeddings(query)

    # Search in Supabase
    supabase = SupabaseClient(db_url)
    results = supabase.similarity_search("documents", query_embedding, limit=5)

    print(f"\nFound {len(results)} similar documents:\n")
    for r in results:
        print(f"ID: {r['id']} | Similarity: {r['similarity']:.4f}")
        print(f"Content: {r['content'][:200]}...")
        print("-" * 50)


def cmd_chat(db_url: str, ollama: OllamaClient, question: str) -> None:
    """RAG-style chat: retrieve context from Supabase, then answer with Ollama."""
    print(f"Question: {question}")

    # Get relevant context from Supabase
    query_embedding = ollama.generate_embeddings(question)
    supabase = SupabaseClient(db_url)
    results = supabase.similarity_search("documents", query_embedding, limit=3)

    # Build context
    context = "\n\n".join([r["content"] for r in results])
    print(f"\nRetrieved {len(results)} relevant documents as context.")

    # Generate answer with Ollama
    prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:"""

    print("\nGenerating answer...")
    answer = ollama.generate(prompt)
    print(f"\nAnswer: {answer}")


def cmd_list(db_url: str) -> None:
    """List all stored documents."""
    supabase = SupabaseClient(db_url)
    rows = supabase.execute("""
        SELECT id, content, created_at FROM documents ORDER BY created_at DESC LIMIT 20;
    """)

    print(f"Found {len(rows)} documents:\n")
    for row in rows:
        print(f"ID: {row[0]} | Created: {row[2]}")
        print(f"Content: {row[1][:100]}...")
        print("-" * 50)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ollama + Supabase PostgreSQL Integration"
    )
    parser.add_argument("--env-file", default="new.env",
                        help="Path to env file (default: new.env)")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                        help="Ollama base URL")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    subparsers.add_parser("setup", help="Setup pgvector extension and tables")

    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Embed and store text")
    embed_parser.add_argument("text", help="Text to embed")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for similar documents")
    search_parser.add_argument("query", help="Search query")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="RAG-style chat with documents")
    chat_parser.add_argument("question", help="Question to ask")

    # List command
    subparsers.add_parser("list", help="List stored documents")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Setup environment
        db_url = setup_env(args.env_file)

        if args.command == "setup":
            cmd_setup(db_url)
            return 0

        # Initialize Ollama client for other commands
        ollama = OllamaClient(args.ollama_url)

        if args.command == "embed":
            cmd_embed(db_url, ollama, args.text)
        elif args.command == "search":
            cmd_search(db_url, ollama, args.query)
        elif args.command == "chat":
            cmd_chat(db_url, ollama, args.question)
        elif args.command == "list":
            cmd_list(db_url)

    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
