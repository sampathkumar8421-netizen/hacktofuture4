import argparse
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
import psycopg
from dotenv import load_dotenv


def sanitize_database_url(url: str) -> str:
    """
    - Strip `pgbouncer=true` (libpq rejects unknown params)
    - Remove [] wrappers around password if present (common copy/paste in Supabase)
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


def batched(it: Iterable[tuple], n: int) -> Iterable[list[tuple]]:
    batch: list[tuple] = []
    for x in it:
        batch.append(x)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch


def export_table(
    conn: psycopg.Connection,
    *,
    table: str,
    out_dir: Path,
    limit: int | None,
    where: str | None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Avoid exporting heavy/complex columns by default.
    # We skip embeddings and vector/geometry columns; those aren’t needed for tabular AutoML routing.
    with conn.cursor() as cur:
        cur.execute(
            """
            select column_name, data_type, udt_name
            from information_schema.columns
            where table_schema='public' and table_name=%s
            order by ordinal_position
            """,
            (table,),
        )
        cols = cur.fetchall()

    selected_cols: list[str] = []
    for (name, data_type, udt_name) in cols:
        if name in {"embedding"}:
            continue
        if data_type.lower() in {"user-defined"} and udt_name in {"vector"}:
            continue
        # Geography/geometry columns come back as USER-DEFINED in some setups.
        if name in {"location"}:
            continue
        selected_cols.append(name)

    col_sql = ", ".join(f'"{c}"' for c in selected_cols)
    sql = f"select {col_sql} from public.\"{table}\""
    if where:
        sql += f" where {where}"
    if limit and limit > 0:
        sql += f" limit {int(limit)}"

    df = pd.read_sql_query(sql, conn)
    df.to_parquet(out_dir / f"{table}.parquet", index=False)
    df.to_csv(out_dir / f"{table}.csv", index=False)
    print(f"Exported public.{table}: rows={len(df):,}, cols={len(df.columns)}")


def main() -> int:
    p = argparse.ArgumentParser(description="Export selected public.* tables from Supabase Postgres.")
    p.add_argument("--env-file", default="new.env")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--limit", type=int, default=200000, help="Max rows per table (0 = no limit).")
    p.add_argument(
        "--tables",
        default="floats,profiles,measurements,feature_catalogs",
        help="Comma-separated list of public tables to export.",
    )
    args = p.parse_args()

    load_dotenv(dotenv_path=Path(args.env_file), override=True)
    url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DIRECT_URL/DATABASE_URL not set in env.")
    url = sanitize_database_url(url)

    out_dir = Path(args.out_dir)
    tables = [t.strip() for t in str(args.tables).split(",") if t.strip()]
    limit = None if args.limit == 0 else max(0, int(args.limit))

    with psycopg.connect(url) as conn:
        for t in tables:
            export_table(conn, table=t, out_dir=out_dir, limit=limit, where=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

