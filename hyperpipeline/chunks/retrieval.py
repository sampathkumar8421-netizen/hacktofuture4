import requests
from typing import Any, Dict
from hyperpipeline.schemas import ApplicationSpec

try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'database'))
    from ollama_supabase import SupabaseClient, setup_env
except ImportError:
    SupabaseClient = None
    setup_env = None

class RetrievalChunk:
    """
    Retrieval planner chunk: generates embeddings and pulls relevant RAG vectors from Supabase.
    """
    def __init__(self):
        try:
            db_url = setup_env("new.env")
            self.supabase = SupabaseClient(db_url)
            self.db_connected = True
            print("[OK] RetrievalChunk linked to Supabase Vector DB.")
        except Exception as e:
            self.supabase = None
            self.db_connected = False
            print(f"[Warning] Supabase RAG not available: {e}")

    def create_embedding(self, text: str) -> list[float]:
        """Calls LM Studio's default embedding endpoint."""
        r = requests.post("http://localhost:1234/v1/embeddings", json={
            "input": text,
            "model": "local-model"
        }, timeout=15)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

    def execute(self, spec: ApplicationSpec, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[Chunk] Retrieval: Fetching data for {spec.application_type}")
        
        raw_query = context.get("raw_query", "")
        rag_results = []
        
        if self.db_connected and raw_query:
            try:
                print(f"        -> Generating LM Studio Embedding for: '{raw_query[:30]}...'")
                emb = self.create_embedding(raw_query)
                rag_results = self.supabase.similarity_search("documents", emb, limit=3)
                print(f"        -> Supabase DB Returned {len(rag_results)} vector matches.")
            except Exception as e:
                print(f"        -> RAG Search Failed: {e}")

        # Simulated fallback SQL parsing for standard metrics
        sql_filters = []
        if spec.region_mode == "bbox" and spec.bbox:
            sql_filters.append(f"ST_MakeEnvelope({spec.bbox[0]}, {spec.bbox[2]}, {spec.bbox[1]}, {spec.bbox[3]}, 4326)")
        
        context["retrieval_data"] = {
            "rows_fetched": 1500 + len(rag_results) * 100,
            "floats_involved": [1901111, 2901122],
            "filters_used": sql_filters,
            "rag_context": [res["content"] for res in rag_results]
        }
        return context
