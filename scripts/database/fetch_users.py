import argparse
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv
import psycopg


def _print_rows(rows: Iterable[tuple], limit: int) -> None:
    count = 0
    for row in rows:
        count += 1
        if count <= limit:
            user_id, email, created_at = row
            print(f"{user_id}\t{email or ''}\t{created_at}")
    print(f"\nTotal rows: {count}")


def _sanitize_database_url(url: str) -> str:
    """
    Supabase pooler URLs often include query params like `pgbouncer=true`.
    Psycopg/libpq rejects unknown URI query parameters, so strip ones we don't need.
    """
    # If the password is wrapped in [] (common when copy/pasting), remove the
    # wrappers because they are not valid in URLs and would break auth.
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
    parser = argparse.ArgumentParser(description="Fetch users from Supabase Postgres (auth.users).")
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional path to env file (e.g. .env or new.env). If omitted, reads from process env.",
    )
    parser.add_argument("--limit", type=int, default=25, help="How many rows to print (still counts all).")
    args = parser.parse_args()

    if args.env_file:
        env_path = Path(args.env_file)
        if not env_path.exists():
            raise SystemExit(f"--env-file not found: {env_path}")
        if env_path.is_file() and env_path.stat().st_size == 0:
            raise SystemExit(f"--env-file is empty: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)

    # Prefer direct connection string if provided (Supabase uses it for migrations).
    database_url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DIRECT_URL/DATABASE_URL is not set. Provide it via env or use --env-file.")
    database_url = _sanitize_database_url(database_url)

    query = """
        select id, email, created_at
        from auth.users
        order by created_at desc
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            _print_rows(cur.fetchall(), limit=max(0, args.limit))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
