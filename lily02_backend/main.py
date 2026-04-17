"""
Lily02 FastAPI Backend (Decoupled Architecture)
================================================
Layer 1: Translation (IndicTranslator)
Layer 2: Reasoning (ParentOrchestrator - ONLY produces a plan)
Layer 3: Execution (ExecutionEngine - ONLY runs chunks deterministically)
Layer 4: Synthesis (Orchestrator - converts results to natural language)
"""

import sys
import os
import json
import shutil
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hyperpipeline.orchestrator import ParentOrchestrator
from hyperpipeline.indic_translator import IndicTranslator
from hyperpipeline.execution_engine import ExecutionEngine
from hyperpipeline.chunks import (
    RetrievalChunk, FeatureComposerChunk, DomainMetricChunk, EvidenceReportingChunk,
    AdvancedAnalysisChunk, AutoMLInsightChunk
)

# ---------------------------------------------------------------
# Application Bootstrap
# ---------------------------------------------------------------
app = FastAPI(
    title="Lily02 Agentic AI Engine",
    description="Decoupled Reasoning + Async Execution Architecture",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 1 & 2: Reasoning components (produce plans, never execute)
orchestrator = ParentOrchestrator(base_url="http://localhost:1234/v1")
translator = IndicTranslator(base_url="http://localhost:1234/v1")

# Layer 3: Execution engine (executes plans, never reasons)
CHUNKS_MAP = {
    "retrieval_chunk": RetrievalChunk(),
    "feature_chunk": FeatureComposerChunk(),
    "feature_composer_chunk": FeatureComposerChunk(),
    "domain_metric_chunk": DomainMetricChunk(),
    "reporting_chunk": EvidenceReportingChunk(),
    "evidence_and_reporting_chunk": EvidenceReportingChunk(),
    "advanced_analysis_chunk": AdvancedAnalysisChunk(),
    "automl_insight_chunk": AutoMLInsightChunk()
}
engine = ExecutionEngine(chunks_map=CHUNKS_MAP)

# ---------------------------------------------------------------
# File Agency Config
# ---------------------------------------------------------------
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    chat_history: str = ""
    enable_automl: bool = False


# ---------------------------------------------------------------
# Core Pipeline Endpoints
# ---------------------------------------------------------------
@app.post("/api/orchestrate")
async def execute_hyperpipeline(request: QueryRequest):
    """
    Decoupled pipeline logic execution with Agency Support.
    """
    try:
        # Hot-scan for uploaded files to provide context to the agent
        recent_uploads = []
        if os.path.exists(UPLOAD_DIR):
            files = sorted(
                [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))],
                key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)),
                reverse=True
            )
            recent_uploads = files[:3] # Pass 3 most recent files

        translated_query = translator.translate_if_needed(request.query)
        
        # Reason with awareness of uploaded files and AutoML preference
        spec, plan = orchestrator.generate_plan(
            translated_query, 
            chat_history=request.chat_history,
            uploaded_files=recent_uploads,
            enable_automl=request.enable_automl
        )
        
        # Execute with full context
        context = await engine.execute_plan(
            spec, plan, 
            translated_query,
            uploaded_files=[os.path.join(UPLOAD_DIR, f) for f in recent_uploads]
        )
        final_report = context.get("final_report", {})
        exec_stats = engine.get_execution_stats()
        natural_response = orchestrator.synthesize_report(request.query, final_report)

        raw_data = None
        if hasattr(spec, 'file_format') and spec.file_format:
            if spec.file_format == "json":
                raw_data = json.dumps(final_report, indent=2)
            elif spec.file_format == "csv":
                import pandas as pd
                try:
                    df = pd.DataFrame(context.get("retrieval_data", {"data": ["empty"]}))
                except Exception:
                    df = pd.DataFrame([context.get("retrieval_data", {})])
                raw_data = df.to_csv(index=False)
            elif spec.file_format == "markdown":
                raw_data = natural_response

        return {
            "status": "success",
            "lily_response": natural_response,
            "application_type": spec.application_type,
            "plan_steps": plan.steps,
            "file_format": getattr(spec, 'file_format', None),
            "raw_file_payload": raw_data,
            "execution_stats": exec_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Receives user files for local agency analysis."""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "status": "success",
            "filename": file.filename,
            "path": file_path,
            "message": f"File {file.filename} uploaded and ready for analysis."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "engine": "Lily02 v2.0 (Decoupled Architecture - Persona Evolution)",
        "execution_stats": engine.get_execution_stats(),
        "uploads_active": len(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else 0
    }

# ---------------------------------------------------------------
# Static File Hosting (React Frontend)
# ---------------------------------------------------------------
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lily02_frontend', 'dist'))

if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(request: Request, full_path: str):
        if "api/" in full_path:
            raise HTTPException(status_code=404)
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    print(f"[Warning] Frontend dist directory not found at {DIST_DIR}. Serving API only.")
