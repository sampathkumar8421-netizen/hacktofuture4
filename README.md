# Lily02 — Agentic Ocean Intelligence Workstation (v2.0)

A premium, agentic scientific workstation for advanced oceanographic telemetry analysis. Fuses AutoGluon forensic ML models, local LLM orchestration (LM Studio), and high-speed LangChain integrations into a "Pure Sea" minimalist research environment.

## 🌊 New in v2.0: The "Pure Sea" Evolution

*   **Lily02 CLI (Open Source)**: Cross-platform terminal interface for scientific intelligence (Windows, Linux, iOS via iSH).
*   **GPT-OSS-120B Integration**: Premier local model support for complex scientific reasoning and forensic analysis.
*   **Local Installation Portal**: Integrated setup hub for deploying the hyperpipeline on private architecture.
*   **Search Dock Action Menus**: A dynamic "Plus" (+) toggle system for scientific presets and AutoML controls.
*   **Auto-ML Deep Insights**: Integrated AutoGluon statistical forensics (`Zap` icon) for deep-data pattern recognition.

## Project Structure

```
argoland/
├── hyperpipeline/               # Decoupled Reasoning Engine (OSS Core)
├── lily02_cli/                  # Terminal Command Interface [NEW]
├── lily02_frontend/             # React (Vite) Workstation UI
│   ├── src/pages/
│   │   └── LocalInstallation.jsx # Deployment Hub [NEW]
├── lily02_backend/              # Unified FastAPI API (Port 8000)
├── scripts/                     # Operational & Recovery scripts
├── pyproject.toml               # Python Packaging Spec [NEW]
└── README.md
```

## 🚀 Local Installation (CLI)

Lily02 is now available as a pip-installable agentic package for Windows, Linux, and iOS.

**1. Install the CLI Package**
```bash
pip install .
```

**2. Configure the reasoning core**
Set your model in `new.env`:
```bash
LOCAL_AGENT_MODEL="gpt-oss-120b"
```

**3. Run the CLI**
```bash
# General query
lily02 ask "Analyze heat trends in the North Atlantic"

# Enable deep Auto-ML forensics
lily02 ask "Scan for BGC anomalies" --automl
```

## 🖥️ Workstation Quick Start

**1. Initialize Environment**
```bash
pip install -r requirements.txt
cd lily02_frontend && npm install && npm run build
```

**2. Launch Unified Services**
```bash
python recovery.py
```
Access the workstation UI locally at `http://localhost:8000`.

## High-Performance Architecture

| Layer | System | Capability |
|---|---|---|
| **Interface** | React v18 / CLI | "Pure Sea" UX + Premium Terminal Diagnostics |
| **Logic** | ParentOrchestrator| Multi-step reasoning with gpt-oss-120b |
| **Data** | Supabase/pgvector | Sub-second RAG retrieval |
| **Forensics** | AutoGluon Tabular | Real-time statistical anomaly detection |
| **Resilience** | Recovery.py | Automated port clearing and service stabilization |

---
© 2026 Lily02 Scientific Mission Control. Open Source Agentic Research.
