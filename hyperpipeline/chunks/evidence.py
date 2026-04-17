from typing import Any, Dict
from hyperpipeline.schemas import ApplicationSpec

class EvidenceReportingChunk:
    """
    Evidence & reporting chunk: assembles all pipeline artifacts into a rich final report.
    """
    def execute(self, spec: ApplicationSpec, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[Chunk] Evidence & Reporting: Compiling final {spec.output_format}")

        app_results = context.get("app_results", {})
        retrieval_data = context.get("retrieval_data", {})
        computed_features = context.get("computed_features", {})
        rag_context = retrieval_data.get("rag_context", [])

        # Build a rich data payload instead of empty dict
        data_payload = {}
        
        # Include computed features directly in data
        if computed_features:
            data_payload["computed_metrics"] = computed_features
        
        # Include domain results
        if app_results:
            data_payload["domain_analysis"] = app_results
        
        # Include RAG context snippets
        if rag_context:
            data_payload["rag_evidence"] = rag_context[:3]

        # Include AutoML insights
        if "automl_summary" in context:
            data_payload["automl_mode_output"] = context["automl_summary"]
        if "ml_analysis_report" in context:
            data_payload["ml_forensic_report"] = context["ml_analysis_report"]

        report = {
            "application": spec.application_type,
            "format_used": spec.output_format,
            "data": data_payload,
            "provenance": {
                "floats_used": retrieval_data.get("floats_involved", []),
                "rows_processed": retrieval_data.get("rows_fetched", 0),
                "qc_policy_applied": spec.qc_policy,
                "variables": spec.required_variables,
                "derived_indicators": spec.derived_indicators,
                "automl_enabled": "automl_summary" in context
            }
        }

        if computed_features:
            report["provenance"]["intermediate_features"] = list(computed_features.keys())

        context["final_report"] = report
        return context
