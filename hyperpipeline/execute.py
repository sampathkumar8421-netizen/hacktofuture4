import argparse
import json
from hyperpipeline.orchestrator import ParentOrchestrator
from hyperpipeline.chunks import (
    RetrievalChunk,
    FeatureComposerChunk,
    DomainMetricChunk,
    EvidenceReportingChunk
)

CHUNKS_MAP = {
    "retrieval_chunk": RetrievalChunk(),
    "feature_composer_chunk": FeatureComposerChunk(),
    "domain_metric_chunk": DomainMetricChunk(),
    "evidence_and_reporting_chunk": EvidenceReportingChunk()
}

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Argo Agentic Hyperpipeline")
    parser.add_argument("--query", required=True, help="Natural language scientific request")
    args = parser.parse_args()

    print("="*60)
    print(f"USER QUERY: {args.query}")
    print("="*60)

    # 1. Orchestration
    print("\n[Sys] Step 1: Orchestrating Plan...")
    orchestrator = ParentOrchestrator()
    spec, plan = orchestrator.generate_plan(args.query)

    print(f"\n[Spec Generated]: Application Type = {spec.application_type}")
    print(f"[Plan Generated]: Steps = {plan.steps}")

    # 2. Execution Loop
    print("\n[Sys] Step 2: Executing Chunks...")
    context = {}
    for step_name in plan.steps:
        if step_name not in CHUNKS_MAP:
            print(f"Warning: Chunk {step_name} not found. Skipping.")
            continue
            
        chunk = CHUNKS_MAP[step_name]
        context = chunk.execute(spec, context)

    # 3. Final Output
    print("\n[Sys] Step 3: Final Output payload:")
    print("="*60)
    final_report = context.get("final_report", {})
    print(json.dumps(final_report, indent=2))
    print("="*60)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
