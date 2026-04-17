import sys
import json
import requests
from hyperpipeline.orchestrator import ParentOrchestrator

try:
    from ollama_supabase import SupabaseClient, setup_env
except ImportError:
    pass

def test_integration():
    print("=== Lead Systems Architect: Executing Integration Protocol ===")
    query = "Evaluate the kilosample parameters for temperature threshold anomalies across the central Pacific sector."
    print(f"Query: {query}")
    
    # 1. Establish RAG connection bypassing Translators
    try:
        db_url = setup_env("new.env")
        sb = SupabaseClient(db_url)
        print("Connected to Supabase.")
        
        # Using LM Studio instance locally for embeddings
        r = requests.post("http://localhost:1234/v1/embeddings", json={
            "input": query,
            "model": "local-model"
        }, timeout=10)
        r.raise_for_status()
        query_emb = r.json()["data"][0]["embedding"]
        
        rag_data = sb.similarity_search("kilosample", query_emb, limit=3)
        context_text = json.dumps(rag_data)
        print(f"Retrieved {len(rag_data)} telemetry records from kilosample.")
        
    except Exception as e:
        print(f"[Warning] RAG Live Connection Failed ({e}). Injecting specific dummy payload for test synthesis.")
        context_text = '''[
          {"id": 481, "content": "Lat: 20.5, Lon: -150.1, Depth: 50m, Temp: 31.2C", "metadata": {"source": "kilosample", "qc_flag": 4}},
          {"id": 482, "content": "Lat: 20.8, Lon: -150.9, Depth: 20m, Temp: 26.5C", "metadata": {"source": "kilosample", "qc_flag": 1}}
        ]'''

    # 2. Invoke Orchestrator (Primary: Gemini 3.1 Pro High)
    orc = ParentOrchestrator(base_url="http://localhost:1234/v1", model="gemini-3.1-pro-high")
    
    print("\nSynthesizing JSON Output Payload...\n")
    output = orc.synthesize_rag_json(query, context_text)
    
    print("--- FULL SYNTHESIS OUTPUT ---\n")
    print(output)
    print("\n------------------------------")

if __name__ == "__main__":
    test_integration()
