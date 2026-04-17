## Argo → Supabase Postgres (pgvector + PostGIS)

This repo now includes a **Supabase-ready importer** for your dataset at `C:\Users\ASUS\argo_complete_database_final`.

### Prereqs

- **Python 3.10+**
- **Ollama** running locally (only if you use `--embed`)
  - Install an embedding model (768-dim recommended):

```bash
ollama pull nomic-embed-text
```

### 1) Install deps

From `c:\Users\ASUS\Downloads\argoland`:

```bash
python -m pip install -r requirements.txt
```

### 2) Set Supabase connection env

You already have `new.env` with `DIRECT_URL` / `DATABASE_URL`.

### 3) Create schema + RPCs in Supabase

```bash
python argo_import_supabase.py --env-file new.env --data-dir "C:\Users\ASUS\argo_complete_database_final" --setup-only
```

This executes:
- `sql/argo_schema.sql` (tables + pgvector + PostGIS + indexes)
- `sql/argo_search.sql` (semantic search RPCs)
- loads `metadata/argo_features_catalog.json` into `public.feature_catalogs`

### 4) Import CSVs

```bash
python argo_import_supabase.py --env-file new.env --data-dir "C:\Users\ASUS\argo_complete_database_final"
```

#### Smoke test (recommended first)

```bash
python argo_import_supabase.py --env-file new.env --data-dir "C:\Users\ASUS\argo_complete_database_final" --no-setup --only-float 6904066 --batch-size 2000
```

### 5) Generate embeddings (semantic search)

```bash
python argo_import_supabase.py --env-file new.env --data-dir "C:\Users\ASUS\argo_complete_database_final" --embed
```

### Example queries (SQL)

#### Time-series style: daily average temperature for one float

```sql
select
  date_trunc('day', m.measurement_time) as day,
  avg(m.temperature) as avg_temp_c
from public.measurements m
join public.profiles p on p.id = m.profile_id
where p.wmo_id = 6904066
group by 1
order by 1;
```

#### Spatial: profiles within 200km of a point

```sql
select p.wmo_id, p.cycle_number, p.profile_time, p.latitude, p.longitude
from public.profiles p
where st_dwithin(
  p.location,
  st_setsrid(st_makepoint(38.536, -53.120), 4326)::geography,
  200000
)
order by p.profile_time desc
limit 50;
```

#### Semantic search (after `--embed`): match floats by meaning

In Supabase SQL editor you can call the RPC if you supply a query embedding.
Typically you generate embeddings client-side (Ollama) and pass the vector in.

RPCs created:
- `public.match_floats(query_embedding vector(768), match_count int)`
- `public.match_profiles(query_embedding vector(768), match_count int, filter_wmo_id int)`

