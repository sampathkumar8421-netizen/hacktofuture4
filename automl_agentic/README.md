## AutoGluon Agentic Router (Argo/OneArgo)

This folder builds a **first-pass ML router** that maps a user’s natural-language request to:
- an `application_type` (from your Argo/OneArgo catalog)
- a **parameter bundle** (region/time/depth/QC/etc.) for downstream deterministic tools

This is intentionally **decision-support only** (it does not run NWP/ocean assimilation models).

### Why AutoGluon here?
AutoGluon is used to train a supervised classifier on labeled examples of requests.
In production, the “parent agent” can use this router output to pick which tools/chunks to run.

### Files
- `requirements-automl.txt`: extra dependencies (AutoGluon + data tooling)
- `export_supabase_public.py`: export selected tables from Supabase Postgres to local Parquet/CSV
- `generate_training_data.py`: create synthetic labeled requests with parameter combinations
- `train_router.py`: train a router model
- `predict_router.py`: load model and predict on new user text

### Quick start

From repo root (`c:\Users\ASUS\Downloads\argoland`):

```bash
python -m pip install -r automl_agentic/requirements-automl.txt
```

Generate training data:

```bash
python automl_agentic/generate_training_data.py --out automl_agentic/data/train.csv --n 4000
```

Train:

```bash
python automl_agentic/train_router.py --train automl_agentic/data/train.csv --out-dir automl_agentic/models/router_v1
```

Predict:

```bash
python automl_agentic/predict_router.py --model-dir automl_agentic/models/router_v1 --text "Find floats near 10N 55E in 2023 with low oxygen and pH anomaly"
```

### Supabase export (optional)
Exports a safe subset of `public.*` tables for analysis/feature building.

```bash
python automl_agentic/export_supabase_public.py --env-file new.env --out-dir automl_agentic/exports --limit 200000
```

