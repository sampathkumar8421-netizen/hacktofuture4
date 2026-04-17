import json
import requests
import os
from typing import Tuple, Dict, Any

from hyperpipeline.schemas import ApplicationSpec, ExecutionPlan


class ParentOrchestrator:
    """
    Hybrid Orchestrator v2.0 (Fast/Slow Path Routing).
    - Fast Path: Simple conversational queries or greetings (uses gpt-4o-mini).
    - Slow Path: Scientific oceanographic analysis (uses Full Hyperpipeline).
    """

    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "local-model", ag_model_path: str = "automl_agentic/models/router_v1"):
        self.base_url = base_url.rstrip("/")
        self.slow_model = model
        self.ag_predictor = None
        self._cached_model_id = None
        
        # Fast Path Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key == "your_key_here":
            self.openai_api_key = None
            
        self.fast_model = os.getenv("FAST_MODEL", "gpt-4o-mini")
        self.fast_base_url = os.getenv("FAST_MODEL_URL", "https://api.openai.com/v1") if self.openai_api_key else self.base_url

        try:
            from autogluon.tabular import TabularPredictor
            import pandas as pd
            self.pd = pd
            self.ag_predictor = TabularPredictor.load(ag_model_path)
            print(f"[OK] Loaded AutoGluon Hybrid Router from {ag_model_path}")
        except Exception:
            print(f"[Warning] AutoGluon model not found at {ag_model_path}. Falling back to Pure LLM routing.")

    def get_attached_model(self) -> str:
        if self._cached_model_id:
            return self._cached_model_id
        try:
            r = requests.get(f"{self.base_url}/models", timeout=3)
            r.raise_for_status()
            data = r.json().get("data", [])
            if data:
                self._cached_model_id = data[0]["id"]
                return self._cached_model_id
        except Exception:
            pass
        return self.slow_model

    def _call_llm(self, system: str, user: str, temperature: float = 0.1, max_tokens: int = 600, use_fast_path: bool = False) -> str:
        """Universal LLM caller supporting both Local (LM Studio) and OpenAI (Fast Path)."""
        url = self.fast_base_url if use_fast_path else self.base_url
        
        # Determine model name: use fast_model ONLY if hitting OpenAI, otherwise resolve local.
        if use_fast_path and self.openai_api_key:
            model = self.fast_model
        else:
            model = self.get_attached_model()

        headers = {"Authorization": f"Bearer {self.openai_api_key}"} if use_fast_path and self.openai_api_key else {}

        r = requests.post(f"{url}/chat/completions", headers=headers, json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def classify_complexity(self, query: str) -> str:
        """Determines if the query is 'SIMPLE' (conversation) or 'COMPLEX' (scientific analysis)."""
        system = "Classify the user query as 'SIMPLE' (greetings, general chat, off-topic) or 'COMPLEX' (Argo data requests, scientific analysis, map/plot/download requests). Output ONLY the word."
        try:
            # Always use fast path for classification
            result = self._call_llm(system, query, temperature=0, max_tokens=10, use_fast_path=True)
            return "COMPLEX" if "COMPLEX" in result.upper() else "SIMPLE"
        except Exception:
            return "COMPLEX" # Default to slow path for reliability

    def generate_plan(self, query: str, chat_history: str = "", uploaded_files: list = None, enable_automl: bool = False) -> Tuple[ApplicationSpec, ExecutionPlan]:
        # Step 1: Route Path
        complexity = self.classify_complexity(query)
        print(f"[Router] Query complexity: {complexity}")

        if complexity == "SIMPLE":
            spec = ApplicationSpec(
                application_type="conversational_response",
                required_variables=[],
                derived_indicators=[],
                output_format="text"
            )
            return spec, ExecutionPlan(steps=[])

        # Step 2: Full Plan Generation (Slow Path)
        ag_app_type = None
        if self.ag_predictor is not None:
            try:
                df_query = self.pd.DataFrame([{"query_text": query}])
                ag_app_type = self.ag_predictor.predict(df_query).iloc[0]
                print(f"[Hybrid Engine] AutoGluon routed: '{ag_app_type}'")
            except Exception:
                pass

        system = """You are an ocean data router. Given a user request, output ONLY a JSON object like:
{"application_type":"ocean_heat_content_timeseries","required_variables":["TEMP","PRES"],"derived_indicators":["OHC_0_700"],"output_format":"table","file_format":null,"steps":["retrieval_chunk","feature_chunk","domain_metric_chunk","reporting_chunk"]}

Rules:
- application_type: pick from [ocean_heat_content_timeseries, bgc_ocean_health_scores, semantic_retrieval_floats_profiles, anomaly_detection_core_temperature_salinity, predictive_ocean_analytics, localized_file_forensics].
- steps: always include retrieval_chunk first and reporting_chunk last.
- If the user mentions 'upload', 'file', or 'my data', include 'advanced_analysis_chunk'.
- If 'ENABLE_AUTOML' is True, include 'automl_insight_chunk' in the steps for deep analysis.
Output ONLY the JSON object."""

        user_msg = f"ENABLE_AUTOML_MODE: {enable_automl}\n" + query
        if chat_history:
            user_msg = f"Context:\n{chat_history}\n\nRequest: {query}\nENABLE_AUTOML_MODE: {enable_automl}"
        
        if uploaded_files:
            user_msg += f"\nAVAILABLE_FILES_FOR_AGENCY: {uploaded_files}"
        
        if ag_app_type:
            user_msg += f'\n(Router hint: application_type should be "{ag_app_type}")'

        try:
            raw = self._call_llm(system, user_msg, temperature=0.1, max_tokens=400, use_fast_path=True)
            
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
                raw = raw.strip()
            
            data = json.loads(raw)
            spec = ApplicationSpec(
                application_type=data.get("application_type", "semantic_retrieval_floats_profiles"),
                required_variables=data.get("required_variables", []),
                derived_indicators=data.get("derived_indicators", []),
                output_format=data.get("output_format", "table"),
                file_format=data.get("file_format")
            )
            plan = ExecutionPlan(steps=data.get("steps", ["retrieval_chunk", "reporting_chunk"]))
            return spec, plan

        except Exception as e:
            print(f"[Orchestrator] LLM planning failed ({e}). Using intelligent fallback.")
            return self._smart_fallback(query, ag_app_type)

    def synthesize_report(self, query: str, final_report: dict) -> str:
        """Converts results to natural language. Simple queries use fast path."""
        # Check if this was a fast-path conversational query
        is_conversational = final_report.get("application") == "conversational_response" or not final_report
        
        system = "You are Lily02, a marine science AI. Summarize results clearly."
        if is_conversational:
            system = "You are Lily02, a friendly ocean intelligence AI. Engage naturally with the user."

        try:
            # Conversational or simple results always use Fast Path
            use_fast = is_conversational or self.classify_complexity(query) == "SIMPLE"
            return self._call_llm(system, f"User: {query}\nData: {json.dumps(final_report)}", temperature=0.3, use_fast_path=use_fast)
        except Exception as e:
            print(f"[Synthesize] Error: {e}")
            return self._format_fallback_report(query, final_report)

    def _format_fallback_report(self, query: str, report: dict) -> str:
        if report.get("application") == "conversational_response":
            return "I am Lily02. How can I help you with Argo ocean data today?"
        lines = [f"## Lily02 Analysis Report\n", f"**Query:** {query}\n", f"**Application:** `{report.get('application', 'unknown')}`\n"]
        data = report.get("data", {})
        if data:
            lines.append("### Results")
            for k, v in data.items(): lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)

    def _smart_fallback(self, query: str, ag_app_type: str = None) -> Tuple[ApplicationSpec, ExecutionPlan]:
        q = query.lower()
        app_type = ag_app_type or "semantic_retrieval_floats_profiles"
        steps = ["retrieval_chunk", "reporting_chunk"]
        if any(w in q for w in ["heat", "ohc", "deoxygenation", "anomal"]):
            steps = ["retrieval_chunk", "feature_chunk", "domain_metric_chunk", "reporting_chunk"]
        
        spec = ApplicationSpec(application_type=app_type, required_variables=[], derived_indicators=[], output_format="table")
        return spec, ExecutionPlan(steps=steps)
