import argparse
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg
from dotenv import load_dotenv


def sanitize_database_url(url: str) -> str:
    # Remove [] wrappers around password if present.
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--env-file", default="new.env")
    args = p.parse_args()

    load_dotenv(dotenv_path=Path(args.env_file), override=True)
    url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DIRECT_URL/DATABASE_URL not set")
    url = sanitize_database_url(url)

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            for table in ("floats", "profiles", "measurements"):
                cur.execute(
                    """
                    select column_name, data_type
                    from information_schema.columns
                    where table_schema = 'public' and table_name = %s
                    order by ordinal_position
                    """,
                    (table,),
                )
                cols = cur.fetchall()
                print(f"\npublic.{table} columns:")
                for (name, dtype) in cols:
                    print(f"  - {name}: {dtype}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

