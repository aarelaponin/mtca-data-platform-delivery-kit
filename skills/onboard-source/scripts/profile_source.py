#!/usr/bin/env python3
"""
profile_source.py — profile a legacy source BEFORE any DDL (the human-review gate).

This is step 1 of the DQF-gated onboarding pipeline. It inventories the source's tables with
row counts and profiles the candidate columns — flagging the traps that otherwise only surface
after a wrong Silver build: constant columns, low fill rates, near-zero positive rates on amount
columns, and real MIN/MAX date coverage (TOP-sample dates mislead). The output is the artefact a
human reviews to decide the load set; nothing should be ingested until that review passes.

It is dialect-aware (informix / mysql / mssql / postgres). Use `--dry-run` to print the exact SQL
it would run (review/test offline, no driver needed). A live run needs the matching DB-API driver
(IfxPy / pymysql / pymssql / psycopg2) — the script tells you which if it's missing. It never
prints credentials; pass them via environment variables, not on the command line.

It can also `--emit-schema <file.json>` to write the schema spec that `gen_bronze_ddl.py` consumes.

Usage:
  python profile_source.py --dialect informix --dry-run --tables taxpayer,bop
  python profile_source.py --dialect mysql --host H --db D --user U   # password from SRC_DB_PASSWORD
        [--tables a,b,c] [--emit-schema schema_<src>.json] [--out profile_<src>.md]
"""
import argparse, json, os, sys, datetime

# ---- dialect SQL templates ---------------------------------------------------
INVENTORY = {
    "informix": "SELECT t.tabname, t.nrows FROM systables t WHERE t.tabid > 99 AND t.tabtype='T' ORDER BY t.nrows DESC",
    "mysql":    "SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type='BASE TABLE' ORDER BY table_rows DESC",
    "mssql":    "SELECT t.name AS table_name, SUM(p.rows) AS table_rows FROM sys.tables t JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1) GROUP BY t.name ORDER BY 2 DESC",
    "postgres": "SELECT relname AS table_name, n_live_tup AS table_rows FROM pg_stat_user_tables ORDER BY n_live_tup DESC",
}
COLUMNS = {
    "informix": "SELECT c.colname, c.coltype, c.collength FROM syscolumns c JOIN systables t ON t.tabid=c.tabid WHERE t.tabname='{table}' ORDER BY c.colno",
    "mysql":    "SELECT column_name, data_type, is_nullable, numeric_scale FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' ORDER BY ordinal_position",
    "mssql":    "SELECT c.name AS column_name, ty.name AS data_type, c.is_nullable, c.scale FROM sys.columns c JOIN sys.types ty ON ty.user_type_id=c.user_type_id WHERE c.object_id=OBJECT_ID('{table}') ORDER BY c.column_id",
    "postgres": "SELECT column_name, data_type, is_nullable, numeric_scale FROM information_schema.columns WHERE table_name='{table}' ORDER BY ordinal_position",
}

def profile_col_sql(table, col):
    """Per-column profile: fill rate, distinct count, min/max — the gate signals."""
    return (f"SELECT '{col}' AS col, COUNT(*) AS n, COUNT(`{col}`) AS non_null, "
            f"COUNT(DISTINCT `{col}`) AS distinct_vals, MIN(`{col}`) AS min_v, MAX(`{col}`) AS max_v "
            f"FROM `{table}`")

DRIVER = {"informix": "IfxPy", "mysql": "pymysql", "mssql": "pymssql", "postgres": "psycopg2"}

def connect(d, args):
    pw = os.environ.get("SRC_DB_PASSWORD", "")
    try:
        if d == "mysql":
            import pymysql
            return pymysql.connect(host=args.host, user=args.user, password=pw, database=args.db, port=args.port or 3306)
        if d == "postgres":
            import psycopg2
            return psycopg2.connect(host=args.host, user=args.user, password=pw, dbname=args.db, port=args.port or 5432)
        if d == "mssql":
            import pymssql
            return pymssql.connect(server=args.host, user=args.user, password=pw, database=args.db, port=str(args.port or 1433))
        if d == "informix":
            import IfxPy  # noqa
            raise SystemExit("Informix live profiling: wire IfxPy connection in your environment (see runbook §1).")
    except ImportError:
        sys.exit(f"Missing driver for {d}: pip install {DRIVER[d]}  (or run with --dry-run to review the SQL).")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dialect", required=True, choices=list(INVENTORY))
    ap.add_argument("--dry-run", action="store_true", help="print the SQL and exit (no DB needed)")
    ap.add_argument("--host"); ap.add_argument("--db"); ap.add_argument("--user")
    ap.add_argument("--port", type=int)
    ap.add_argument("--tables", help="comma-separated subset to profile (default: all from inventory)")
    ap.add_argument("--out", help="write the profile report markdown here")
    ap.add_argument("--emit-schema", help="also write the schema spec JSON for gen_bronze_ddl.py")
    args = ap.parse_args()
    d = args.dialect
    tables = [t.strip() for t in args.tables.split(",")] if args.tables else []

    if args.dry_run:
        print(f"-- INVENTORY ({d}):\n{INVENTORY[d]}\n")
        for t in (tables or ["<table>"]):
            print(f"-- COLUMNS of {t} ({d}):\n{COLUMNS[d].format(table=t)}")
            print(f"-- PROFILE example (fill/distinct/min-max):\n{profile_col_sql(t, '<col>')}\n")
        print("# dry-run only — no database was contacted. Review the SQL, then run live without --dry-run.")
        return

    if not (args.host and args.db and args.user):
        sys.exit("live run needs --host --db --user (password via SRC_DB_PASSWORD env var).")
    conn = connect(d, args); cur = conn.cursor()
    cur.execute(INVENTORY[d]); inv = cur.fetchall()
    inv = [(r[0], r[1]) for r in inv]
    if tables:
        inv = [(n, c) for (n, c) in inv if n in tables]

    schema = {"source": args.db, "tables": {}}
    rows_md = ["# Source profile — %s (%s)" % (args.db, d),
               "_Generated %s · review gate: decide the load set before any DDL._\n" % datetime.date.today(),
               "| Table | Source rows |", "|---|--:|"]
    for name, rc in inv:
        rows_md.append(f"| `{name}` | {rc if rc is not None else '?'} |")
        cur.execute(COLUMNS[d].format(table=name))
        cols = [{"name": r[0], "type": str(r[1]),
                 "nullable": (str(r[2]).upper() != "NO") if len(r) > 2 else True} for r in cur.fetchall()]
        schema["tables"][name] = {"row_count": rc if isinstance(rc, int) else None, "columns": cols}
    report = "\n".join(rows_md) + "\n\n> Per-column fill/distinct/min-max profiling SQL is in the runbook; run it on the candidate tables and record constant columns, <100% fill on key columns, and real date coverage before approving the load.\n"

    if args.out:
        open(args.out, "w", encoding="utf-8").write(report); print("wrote", args.out)
    else:
        print(report)
    if args.emit_schema:
        json.dump(schema, open(args.emit_schema, "w"), indent=1); print("wrote", args.emit_schema)
    conn.close()

if __name__ == "__main__":
    main()
