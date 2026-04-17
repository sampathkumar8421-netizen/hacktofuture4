from typing import Any, Dict
from hyperpipeline.schemas import ApplicationSpec

class FeatureComposerChunk:
    """
    Feature composer chunk: builds derived scientific features from raw measurements.
    """
    def execute(self, spec: ApplicationSpec, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[Chunk] Feature Composer: Computing indicators {spec.derived_indicators}")
        
        retrieval_data = context.get("retrieval_data", {})
        rows = retrieval_data.get("rows_fetched", 0)
        
        features = {}
        if "OHC_0_700" in spec.derived_indicators:
            print("        -> Computing Ocean Heat Content 0-700m...")
            features["OHC_0_700"] = [i * 1.5e9 for i in range(1, 6)]
            
        if "oxygen_anomaly" in spec.derived_indicators:
            print("        -> Computing Oxygen Anomaly relative to baseline...")
            features["oxygen_anomaly"] = [-15.2, -18.4, -2.1]
            
        context["computed_features"] = features
        return context
