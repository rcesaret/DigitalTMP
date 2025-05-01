#!/usr/bin/env python3
import os
from pathlib import Path

import sqlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ─── Hard-coded project config ─────────────────────────────
DB_NAMES    = ["TMP_DF8", "TMP_DF9", "TMP_DF10", "TMP_REAN_DF2"]

# __file__ == .../phases/01_LegacyDB/src/setup_databases.py
SCRIPTS_DIR = (
    Path(__file__)
    .parent        # -> .../phases/01_LegacyDB/src
    .parent        # -> .../phases/01_LegacyDB
    .parent        # -> .../phases
    .parent        # -> <project root>
    / "infrastructure" / "db" / "legacy_db_sql_scripts"
)

# parents[0] == src, [1] == 01_LegacyDB, [2] == phases, [3] == project root
# BASE_DIR    = Path(__file__).resolve().parents[3]
# SCRIPTS_DIR = BASE_DIR / "infrastructure" / "db" / "legacy_db_sql_scripts"

def create_db_if_missing(sys_engine, db_name):
    """Check pg_database; create db if not exists."""
    with sys_engine.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db"),
            {"db": db_name}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            print(f"→ Created database: {db_name}")
        else:
            print(f"→ Database already exists: {db_name}")


def execute_sql_file(engine, filepath):
    """Split a .sql into statements and run them in a transaction."""
    sql_text = filepath.read_text()
    statements = sqlparse.split(sql_text)
    with engine.begin() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    print(f"  • Executed {filepath.name}")


def main():
    # ─── Load only PG_* vars from .env ────────────────────────
    load_dotenv()
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT", "5432")
    user = os.getenv("PG_USER")
    pwd  = os.getenv("PG_PASSWORD")

    # ─── System-level connection to 'postgres' ────────────────
    sys_url    = f"postgresql://{user}:{pwd}@{host}:{port}/postgres"
    sys_engine = create_engine(sys_url)

    for db in DB_NAMES:
        print(f"\n=== Setting up: {db} ===")
        create_db_if_missing(sys_engine, db)

        db_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
        engine = create_engine(db_url)

        ddl_file  = SCRIPTS_DIR / f"{db}_create.sql"
        data_file = SCRIPTS_DIR / f"{db}.sql"

        execute_sql_file(engine, ddl_file)
        execute_sql_file(engine, data_file)

    print("\n✅ All databases created & populated.")


if __name__ == "__main__":
    main()
