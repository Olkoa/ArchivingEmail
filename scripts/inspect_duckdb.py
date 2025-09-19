#!/usr/bin/env python3
"""Quick inspection utility for DuckDB files."""

import argparse
import os
import sys

try:
    import duckdb
except ImportError as exc:
    sys.stderr.write("duckdb package is required to inspect DuckDB files.\n")
    raise


def list_tables(connection):
    query = (
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' ORDER BY table_name"
    )
    return [row[0] for row in connection.execute(query).fetchall()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect tables in a DuckDB database")
    parser.add_argument(
        "duckdb_path",
        nargs="?",
        default="data/Projects/ccccccc/ccccccc.duckdb",
        help="Path to the DuckDB file (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of rows to preview from each table",
    )
    args = parser.parse_args()

    if not os.path.exists(args.duckdb_path):
        sys.stderr.write(f"DuckDB file not found: {args.duckdb_path}\n")
        return 1

    con = duckdb.connect(database=args.duckdb_path, read_only=True)

    tables = list_tables(con)
    if not tables:
        print("No tables found in database.")
        return 0

    print(f"Database: {args.duckdb_path}")
    print("Tables:")
    for name in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {duckdb.identifier(name)}").fetchone()[0]
        print(f"- {name} (rows: {count})")

        if args.limit > 0:
            preview = con.execute(
                f"SELECT * FROM {duckdb.identifier(name)} LIMIT {args.limit}"
            ).fetchdf()
            if not preview.empty:
                print(preview)
            else:
                print("  (no rows)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
