import requests

class IndicTranslator:
    """
    A pre-processing module for the Hyperpipeline.
    Uses LM Studio to detect if a request is in an Indian language (like Hindi, Bengali, Telugu, etc.) 
    and securely translates the exact domain constraints into English so the downstream Argo engine 
    can format the JSON spec deterministically without losing nuances.
    """
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "local-model"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._cached_model_id = None

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
        return self.model

    def _is_server_running(self) -> bool:
        return self.get_attached_model() is not None

    def translate_if_needed(self, query: str) -> str:
        if not self._is_server_running():
            print("Warning: LM Studio server not running. Bypassing Indic Translator.")
            return query
            
        system_prompt = """You are a highly precise scientific translator for the AI4Bharat IndicNLP integration.
If the following oceanographic query is in an Indian Language (e.g., Hindi, Bengali, Tamil, Telugu), translate it to English. 
Keep all scientific metrics, coordinates, regions, timestamps, and variables extremely accurate.
If the query is ALREADY in English, simply return the exact same English query.

Output ONLY the translated (or identical) English text. Do NOT add markdown, explanations, or quotes.
"""
        
        try:
            model = self.get_attached_model()
            r = requests.post(f"{self.base_url}/chat/completions", json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.1,
                "stream": False
            }, timeout=30)
            r.raise_for_status()
            
            translated_text = r.json()["choices"][0]["message"]["content"].strip()
            return translated_text
        except Exception as e:
            print(f"Error during Indic translation: {e}. Bypassing translation.")
            return query
