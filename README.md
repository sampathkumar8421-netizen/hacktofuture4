# Lily02 — Agentic Ocean Intelligence Workstation (v2.0)

A premium, agentic scientific workstation for advanced oceanographic telemetry analysis. Fuses AutoGluon forensic ML models, local LLM orchestration (LM Studio), and high-speed LangChain integrations into a "Pure Sea" minimalist research environment.

## 🌊 New in v2.0: The "Pure Sea" Evolution

*   **Premium Minimalist UI**: High-fidelity light-mode design system with frosted glass aesthetics.
*   **Search Dock Action Menus**: A dynamic "Plus" (+) toggle system that hides/reveals scientific presets, file uploads, and AutoML controls.
*   **Auto-ML Deep Insights**: Integrated AutoGluon statistical forensics (`Zap` icon) for deep-data pattern recognition on vector retrieval.
*   **Scientific File Agency**: Seamless local file ingestion with decoupled logic cores for complex forensic analysis.
*   **Unified Production Backend**: Frontend and Backend unified on a single high-performance port (8000).

## Project Structure

```
argoland/
├── hyperpipeline/               # Decoupled Reasoning Engine
│   ├── orchestrator.py          # Parent Orchestrator (Reasoning Core)
│   ├── execution_engine.py      # Execution Core (Parallelism + Caching)
│   ├── schemas.py               # Pydantic validation specs
│   └── chunks/                  # Specialized execution nodes
│       ├── retrieval.py         # Supabase Vector search
│       ├── automl_insight.py    # AutoGluon Forensic Engine [NEW]
│       ├── feature_composer.py  # Scientific feature mapping
│       ├── domain_metrics.py    # Argo-specific analytics
│       └── evidence.py          # Final report synthesis
├── lily02_frontend/             # React (Vite) Workstation UI
│   ├── src/
│   │   ├── pages/               # Multi-page dashboard architecture
│   │   │   ├── ChatRoom.jsx     # Unified Command Center
│   │   │   ├── Dashboard.jsx    # Forensic Analysis Hub
│   │   │   └── DataOps.jsx      # Global Network Monitor
│   │   ├── components/          # Reusable UI primitives
│   │   └── index.css            # "Pure Sea" Design Tokens
├── lily02_backend/              # High-performance FastAPI core
│   └── main.py                  # Entry point (Unified Port 8000)
├── automl_agentic/              # AutoGluon Predictive Layer
├── scripts/                     # Operational & Recovery scripts
│   ├── recovery.py              # Unified self-healing mission control [NEW]
│   ├── launch_tunnel.py         # Management of Ngrok public links
│   └── database/                # Supabase & Vector utilties
├── sql/                         # pgvector schemas & search logic
└── README.md
```

## Quick Start (Production Mode)

**1. Environment Setup**
Add your Supabase and Ngrok credentials to `new.env` at project root.

**2. Scientific Initialization**
```bash
pip install -r requirements.txt
cd lily02_frontend && npm install && npm run build
```

**3. Launch Lily02 Workstation**
```bash
# Recommendation: Use the Recovery script for automated healing
python recovery.py
```

The workstation will be available locally on **http://localhost:8000** and publicly via the generated Ngrok link.

## High-Performance Architecture

| Layer | System | Capability |
|---|---|---|
| **Interface** | React v18 | Minimalist "Pure Sea" UX + Lucide Scientific Icons |
| **Logic** | ParentOrchestrator| Multi-step reasoning & dynamic chunk routing |
| **Data** | Supabase/pgvector | Sub-second RAG retrieval over global Argo floats |
| **Forensics** | AutoGluon Tabular | AutoML anomaly detection and statistical pulse |
| **Network** | Ngrok | Integrated public tunneling with vanity URL support |
| **Resilience** | Recovery.py | Automated port clearing and service stabilization |

---
© 2026 Lily02 Scientific Mission Control. Optimized for Oceanographic Forensic Research.
