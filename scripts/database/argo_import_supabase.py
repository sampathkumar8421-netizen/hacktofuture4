import argparse
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg
import requests
from dotenv import load_dotenv


def _sanitize_database_url(url: str) -> str:
    """
    Supabase pooler URLs often include query params like `pgbouncer=true`.
    Psycopg/libpq rejects unknown URI query parameters, so strip ones we don't need.
    """
    try:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            userinfo, hostpart = rest.split("@", 1)
            if ":" in userinfo:
                user, pwd = userinfo.rsplit(":", 1)
                if len(pwd) >= 2 and pwd.startswith("[") and pwd.endswith("]"):
                    pwd = pwd[1:-1]
                    url = f"{scheme}://{user}:{pwd}@{hostpart}"
    except ValueError:
        pass

    parts = urlsplit(url)
    if not parts.query:
        return url
    kept = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k.lower() != "pgbouncer"]
    new_query = urlencode(kept, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _chunks(it: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(it), size):
        yield it[i : i + size]


def _to_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_text(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return None
    return s


def _run_sql_file(conn: psycopg.Connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    model: str
    timeout_s: float


def _vector_literal(v: list[float]) -> str:
    # pgvector text input format: '[1,2,3]'
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"


def ollama_embed(text: str, cfg: OllamaConfig) -> list[float]:
    # Ollama API: POST /api/embeddings { model, prompt }
    resp = requests.post(
        f"{cfg.base_url.rstrip('/')}/api/embeddings",
        json={"model": cfg.model, "prompt": text},
        timeout=cfg.timeout_s,
    )
    resp.raise_for_status()
    data = resp.json()
    emb = data.get("embedding")
    if not isinstance(emb, list) or not emb:
        raise RuntimeError(f"Unexpected Ollama response: {data}")
    return emb


def upsert_feature_catalogs(conn: psycopg.Connection, data_dir: Path) -> None:
    catalog_path = data_dir / "metadata" / "argo_features_catalog.json"
    if not catalog_path.exists():
        return

    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    rows: list[tuple] = []
    for key, item in raw.items():
        category = item.get("category") or key
        sensor = item.get("sensor")
        variables = item.get("variables") or []
        units = item.get("units") or {}
        math_deps = item.get("math_deps") or item.get("mathematical_deps") or []
        plots = item.get("plots") or item.get("graphical_reps") or []
        description = item.get("description")

        for var in variables:
            rows.append(
                (
                    category,
                    var,
                    description,
                    units.get(var),
                    None,
                    sensor,
                    json.dumps(math_deps),
                    json.dumps(plots),
                )
            )

    if not rows:
        return

    sql = """
        insert into public.feature_catalogs (
          category, feature_name, description, units, data_type, sensor_type, mathematical_deps, graphical_reps
        ) values (
          %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb
        )
        on conflict (category, feature_name) do update set
          description = excluded.description,
          units = excluded.units,
          data_type = excluded.data_type,
          sensor_type = excluded.sensor_type,
          mathematical_deps = excluded.mathematical_deps,
          graphical_reps = excluded.graphical_reps
    """

    with conn.cursor() as cur:
        for batch in _chunks(rows, 1000):
            cur.executemany(sql, batch)


def upsert_float(conn: psycopg.Connection, wmo_id: int, platform_type: Optional[str]) -> None:
    sql = """
      insert into public.floats (wmo_id, platform_type)
      values (%s, %s)
      on conflict (wmo_id) do update set
        platform_type = coalesce(excluded.platform_type, public.floats.platform_type)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (wmo_id, platform_type))


def get_or_create_profile_id(
    conn: psycopg.Connection,
    *,
    wmo_id: int,
    cycle_number: int,
    profile_time: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    direction: Optional[str],
    data_mode: Optional[str],
    position_qc: Optional[str],
    time_qc: Optional[str],
    metadata: dict[str, Any],
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            select id
            from public.profiles
            where wmo_id = %s and cycle_number = %s and profile_time is not distinct from %s
            limit 1
            """,
            (wmo_id, cycle_number, profile_time),
        )
        row = cur.fetchone()
        if row:
            return int(row[0])

        cur.execute(
            """
            insert into public.profiles (
              wmo_id, cycle_number, profile_direction, data_mode,
              profile_time, latitude, longitude,
              position_qc, time_qc, metadata
            ) values (
              %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s::jsonb
            )
            returning id
            """,
            (
                wmo_id,
                cycle_number,
                direction,
                data_mode,
                profile_time,
                latitude,
                longitude,
                position_qc,
                time_qc,
                json.dumps(metadata),
            ),
        )
        new_row = cur.fetchone()
        if not new_row:
            raise RuntimeError("Failed to insert profile")
        return int(new_row[0])


def insert_measurements_batch(conn: psycopg.Connection, rows: list[tuple]) -> None:
    sql = """
      insert into public.measurements (
        profile_id, wmo_id, cycle_number,
        measurement_time, latitude, longitude,
        pressure, pressure_qc,
        temperature, temperature_qc,
        salinity, salinity_qc,
        conductivity, conductivity_qc,
        dissolved_oxygen, dissolved_oxygen_qc, temp_doxy, molar_doxy,
        chlorophyll, chlorophyll_qc,
        nitrate, nitrate_qc,
        ph, ph_qc,
        bbp470, bbp532, bbp700, bbp700_2,
        cdom, cdom_qc,
        downwelling_par,
        down_irradiance380, down_irradiance412, down_irradiance443, down_irradiance490, down_irradiance555,
        metadata
      ) values (
        %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s, %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s, %s, %s,
        %s, %s,
        %s,
        %s, %s, %s, %s, %s,
        %s::jsonb
      )
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)


def import_float_csv(
    conn: psycopg.Connection,
    csv_path: Path,
    batch_size: int = 5000,
    progress_every: int = 50_000,
) -> tuple[int, int, int]:
    """
    Import one per-float CSV (many rows across cycle/pressure levels).
    Returns (wmo_id, num_profiles, num_measurements).
    """
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError(f"Missing header: {csv_path}")

        profiles_seen: dict[tuple[int, int, Optional[str]], int] = {}
        measurements_batch: list[tuple] = []
        num_measurements = 0
        rows_seen = 0

        wmo_id_any: Optional[int] = None

        for row in reader:
            rows_seen += 1
            wmo_id = _to_int(row.get("PLATFORM_NUMBER"))
            cycle_number = _to_int(row.get("CYCLE_NUMBER"))
            profile_time = _to_text(row.get("TIME"))
            if wmo_id is None or cycle_number is None:
                continue

            wmo_id_any = wmo_id_any or wmo_id
            upsert_float(conn, wmo_id=wmo_id, platform_type=_to_text(row.get("PLATFORM_TYPE")))

            profile_key = (wmo_id, cycle_number, profile_time)
            profile_id = profiles_seen.get(profile_key)
            if profile_id is None:
                prof_meta = {
                    "source_csv": str(csv_path),
                }
                profile_id = get_or_create_profile_id(
                    conn,
                    wmo_id=wmo_id,
                    cycle_number=cycle_number,
                    profile_time=profile_time,
                    latitude=_to_float(row.get("LATITUDE")),
                    longitude=_to_float(row.get("LONGITUDE")),
                    direction=_to_text(row.get("DIRECTION")),
                    data_mode=_to_text(row.get("DATA_MODE")),
                    position_qc=_to_text(row.get("POSITION_QC")),
                    time_qc=_to_text(row.get("TIME_QC")),
                    metadata=prof_meta,
                )
                profiles_seen[profile_key] = profile_id

            meta = {}
            for k in (
                "PRES_ERROR",
                "TEMP_ERROR",
                "PSAL_ERROR",
                "N_POINTS",
                "DOXY2",
                "DOXY3",
                "CHLA_FLUORESCENCE",
                "UP_RADIANCE412",
                "UP_RADIANCE443",
                "UP_RADIANCE490",
                "UP_RADIANCE555",
            ):
                if k in row:
                    meta[k] = row.get(k)

            measurements_batch.append(
                (
                    profile_id,
                    wmo_id,
                    cycle_number,
                    profile_time,
                    _to_float(row.get("LATITUDE")),
                    _to_float(row.get("LONGITUDE")),
                    _to_float(row.get("PRES")),
                    _to_int(row.get("PRES_QC")),
                    _to_float(row.get("TEMP")),
                    _to_int(row.get("TEMP_QC")),
                    _to_float(row.get("PSAL")),
                    _to_int(row.get("PSAL_QC")),
                    _to_float(row.get("CNDC")),
                    _to_int(row.get("CNDC_QC")),
                    _to_float(row.get("DOXY")),
                    _to_int(row.get("DOXY_QC")),
                    _to_float(row.get("TEMP_DOXY")),
                    _to_float(row.get("MOLAR_DOXY")),
                    _to_float(row.get("CHLA")),
                    _to_int(row.get("CHLA_QC")),
                    _to_float(row.get("NITRATE")),
                    _to_int(row.get("NITRATE_QC")),
                    _to_float(row.get("PH_IN_SITU_TOTAL")),
                    _to_int(row.get("PH_IN_SITU_TOTAL_QC")),
                    _to_float(row.get("BBP470")),
                    _to_float(row.get("BBP532")),
                    _to_float(row.get("BBP700")),
                    _to_float(row.get("BBP700_2")),
                    _to_float(row.get("CDOM")),
                    _to_int(row.get("CDOM_QC")),
                    _to_float(row.get("DOWNWELLING_PAR")),
                    _to_float(row.get("DOWN_IRRADIANCE380")),
                    _to_float(row.get("DOWN_IRRADIANCE412")),
                    _to_float(row.get("DOWN_IRRADIANCE443")),
                    _to_float(row.get("DOWN_IRRADIANCE490")),
                    _to_float(row.get("DOWN_IRRADIANCE555")),
                    json.dumps(meta),
                )
            )
            num_measurements += 1

            if len(measurements_batch) >= batch_size:
                insert_measurements_batch(conn, measurements_batch)
                measurements_batch.clear()

            if progress_every > 0 and rows_seen % progress_every == 0:
                print(f"  {csv_path.name}: processed {rows_seen:,} rows...")

        if measurements_batch:
            insert_measurements_batch(conn, measurements_batch)

        if wmo_id_any is None:
            raise RuntimeError(f"Could not parse WMO id from {csv_path}")
        return (wmo_id_any, len(profiles_seen), num_measurements)


def refresh_float_stats(conn: psycopg.Connection) -> None:
    sql = """
      with stats as (
        select
          wmo_id,
          count(*) as total_profiles,
          min(profile_time) as start_date,
          max(profile_time) as end_date
        from public.profiles
        group by wmo_id
      ),
      start_pos as (
        select distinct on (wmo_id)
          wmo_id,
          latitude as start_lat,
          longitude as start_lon
        from public.profiles
        order by wmo_id, profile_time asc nulls last
      ),
      end_pos as (
        select distinct on (wmo_id)
          wmo_id,
          latitude as end_lat,
          longitude as end_lon
        from public.profiles
        order by wmo_id, profile_time desc nulls last
      )
      update public.floats f
      set
        total_profiles = stats.total_profiles,
        start_date = stats.start_date,
        end_date = stats.end_date,
        start_lat = start_pos.start_lat,
        start_lon = start_pos.start_lon,
        end_lat = end_pos.end_lat,
        end_lon = end_pos.end_lon
      from stats
      left join start_pos on start_pos.wmo_id = stats.wmo_id
      left join end_pos on end_pos.wmo_id = stats.wmo_id
      where stats.wmo_id = f.wmo_id
    """
    with conn.cursor() as cur:
        cur.execute(sql)


def embed_floats_and_profiles(conn: psycopg.Connection, cfg: OllamaConfig, limit_profiles_per_float: int = 200) -> None:
    """
    Generates embeddings for:
    - floats: one embedding per float summarizing coverage and counts
    - profiles: limited number per float (to keep runtime reasonable)
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            select wmo_id, platform_type, total_profiles, start_date, end_date, start_lat, end_lat, start_lon, end_lon
            from public.floats
            order by wmo_id
            """
        )
        floats = cur.fetchall()

    for (wmo_id, platform_type, total_profiles, start_date, end_date, start_lat, end_lat, start_lon, end_lon) in floats:
        text = (
            "Argo float summary\n"
            f"WMO_ID: {wmo_id}\n"
            f"platform_type: {platform_type}\n"
            f"total_profiles: {total_profiles}\n"
            f"time_range: {start_date} to {end_date}\n"
            f"start_position: lat={start_lat}, lon={start_lon}\n"
            f"end_position: lat={end_lat}, lon={end_lon}\n"
        )
        emb = ollama_embed(text, cfg)
        with conn.cursor() as cur:
            cur.execute("update public.floats set embedding = %s::vector where wmo_id = %s", (_vector_literal(emb), wmo_id))

        with conn.cursor() as cur:
            cur.execute(
                """
                select id, cycle_number, profile_time, latitude, longitude
                from public.profiles
                where wmo_id = %s
                order by profile_time desc nulls last
                limit %s
                """,
                (wmo_id, limit_profiles_per_float),
            )
            profiles = cur.fetchall()

        for (profile_id, cycle_number, profile_time, latitude, longitude) in profiles:
            p_text = (
                "Argo profile\n"
                f"WMO_ID: {wmo_id}\n"
                f"cycle_number: {cycle_number}\n"
                f"profile_time: {profile_time}\n"
                f"latitude: {latitude}\n"
                f"longitude: {longitude}\n"
                "This is an oceanographic vertical profile measurement event."
            )
            p_emb = ollama_embed(p_text, cfg)
            with conn.cursor() as cur:
                cur.execute("update public.profiles set embedding = %s::vector where id = %s", (_vector_literal(p_emb), profile_id))


def main() -> int:
    p = argparse.ArgumentParser(description="Import Argo CSVs into Supabase Postgres (pgvector + PostGIS).")
    p.add_argument("--env-file", default=None, help="Path to env file containing DIRECT_URL/DATABASE_URL.")
    p.add_argument(
        "--data-dir",
        required=True,
        help=r"Path to argo_complete_database_final (e.g. C:\Users\ASUS\argo_complete_database_final).",
    )
    p.add_argument("--setup-only", action="store_true", help="Only run schema/search SQL, no import.")
    p.add_argument("--no-setup", action="store_true", help="Skip running schema/search SQL.")
    p.add_argument("--batch-size", type=int, default=5000, help="Insert batch size for measurements.")
    p.add_argument("--only-float", type=int, default=None, help="Only import one float file by WMO id (e.g. 6904066).")
    p.add_argument("--max-files", type=int, default=None, help="Limit how many float CSV files to import.")
    p.add_argument("--progress-every", type=int, default=50_000, help="Print progress every N CSV rows (0 disables).")
    p.add_argument("--embed", action="store_true", help="Generate embeddings using Ollama (floats + profiles).")
    p.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL.")
    p.add_argument("--ollama-model", default="nomic-embed-text", help="Ollama embedding model (768-dim recommended).")
    p.add_argument("--ollama-timeout-s", type=float, default=60.0, help="Ollama request timeout.")
    args = p.parse_args()

    if args.env_file:
        load_dotenv(dotenv_path=Path(args.env_file), override=True)

    database_url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DIRECT_URL/DATABASE_URL is not set. Provide it via env or use --env-file.")
    database_url = _sanitize_database_url(database_url)

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"--data-dir not found: {data_dir}")

    sql_dir = Path(__file__).resolve().parent / "sql"
    schema_sql = sql_dir / "argo_schema.sql"
    search_sql = sql_dir / "argo_search.sql"
    if not schema_sql.exists() or not search_sql.exists():
        raise SystemExit(f"Missing SQL files in {sql_dir}. Expected argo_schema.sql and argo_search.sql.")

    with psycopg.connect(database_url) as conn:
        conn.execute("set statement_timeout = '0'")

        if not args.no_setup:
            _run_sql_file(conn, schema_sql)
            _run_sql_file(conn, search_sql)
            upsert_feature_catalogs(conn, data_dir=data_dir)
            conn.commit()

        if args.setup_only:
            return 0

        float_csv_dir = data_dir / "csv_by_float"
        if args.only_float is not None:
            csv_paths = [float_csv_dir / f"float_{args.only_float}.csv"]
        else:
            csv_paths = sorted(float_csv_dir.glob("float_*.csv"))
        if not csv_paths:
            raise SystemExit(f"No float CSVs found in: {float_csv_dir}")
        csv_paths = [p for p in csv_paths if p.exists()]
        if not csv_paths:
            raise SystemExit("No matching float CSVs found.")
        if args.max_files is not None and args.max_files > 0:
            csv_paths = csv_paths[: args.max_files]

        for csv_path in csv_paths:
            wmo_id, num_profiles, num_measurements = import_float_csv(
                conn,
                csv_path,
                batch_size=max(100, args.batch_size),
                progress_every=max(0, args.progress_every),
            )
            conn.commit()
            print(f"Imported {csv_path.name}: wmo_id={wmo_id}, profiles={num_profiles}, measurements={num_measurements}")

        refresh_float_stats(conn)
        conn.commit()

        if args.embed:
            cfg = OllamaConfig(base_url=args.ollama_url, model=args.ollama_model, timeout_s=args.ollama_timeout_s)
            embed_floats_and_profiles(conn, cfg=cfg)
            conn.commit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

