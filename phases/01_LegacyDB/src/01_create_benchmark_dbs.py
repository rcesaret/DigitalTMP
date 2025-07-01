# -*- coding: utf-8 -*-
"""
Creates and populates wide-format benchmark databases from TMP_DF9.

This script orchestrates an ETL (Extract, Transform, Load) process that leverages
two powerful, purpose-built SQL queries to generate benchmark databases.

Usage:
    From the src/ directory, run:
    $ python 01_create_benchmark_dbs.py --config config.ini

"""

from __future__ import annotations

import argparse
import configparser
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
from sqlalchemy import create_engine, exc, text
from sqlalchemy.engine import Connection, Engine

# --- Constants ---
LOG_FILE_NAME = "01_create_benchmark_dbs.log"
BENCHMARK_TABLE_NAME = "wide_format_data"
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# --- Data Structures ---
@dataclass(frozen=True)
class Config:
    """Typed container for validated configuration settings."""

    host: str
    port: str
    user: str
    password: str
    root_db: str
    source_db: str
    benchmark_dbs: List[str]
    sql_dir: Path


# --- Logging Setup ---
def setup_logging(log_path: Path) -> None:
    """Configures logging to both console and a file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# --- Configuration Handling ---
class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


def _validate_identifier(name: str) -> None:
    """Raise ValueError if *name* is not a valid SQL identifier."""
    if not _VALID_IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid identifier: '{name}'")


def load_config(config_path: Path) -> Config:
    """Parse and validate the ``.ini`` configuration file."""
    if not config_path.is_file():
        raise ConfigurationError(f"Config file not found: {config_path}")

    parser = configparser.ConfigParser()
    parser.read(config_path)

    try:
        pg_section = parser["postgresql"]
        db_section = parser["databases"]
        path_section = parser["paths"]
    except KeyError as e:
        raise ConfigurationError(f"Missing required section in config: {e}") from e

    benchmark_dbs_raw = db_section.get("benchmark_dbs", "")
    benchmark_dbs = [db.strip() for db in benchmark_dbs_raw.split(",") if db.strip()]
    for db_name in benchmark_dbs:
        _validate_identifier(db_name)

    sql_dir = (config_path.parent / path_section.get("sql_queries_dir")).resolve()

    return Config(
        host=pg_section.get("host"),
        port=pg_section.get("port"),
        user=pg_section.get("user"),
        password=pg_section.get("password"),
        root_db=pg_section.get("root_db"),
        source_db=db_section.get("source_db"),
        benchmark_dbs=benchmark_dbs,
        sql_dir=sql_dir,
    )


# --- Database Helpers ---
def get_engine(cfg: Config, dbname: str | None = None) -> Engine:
    """Return a new SQLAlchemy engine for the specified database."""
    target_db = dbname or cfg.root_db
    conn_str = (
        f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
        f"{cfg.host}:{cfg.port}/{target_db}"
    )
    return create_engine(conn_str)


def database_exists(conn: Connection, db_name: str) -> bool:
    """Return ``True`` if *db_name* exists."""
    _validate_identifier(db_name)
    result = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :name"),
        {"name": db_name},
    )
    return result.scalar() == 1


def create_database(root_engine: Engine, db_name: str) -> None:
    """Create a new database if it does not already exist."""
    _validate_identifier(db_name)
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        if not database_exists(conn, db_name):
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            logging.info("Successfully created database: %s", db_name)
        else:
            logging.warning("Database '%s' already exists, skipping creation.", db_name)


def drop_database(root_engine: Engine, db_name: str) -> None:
    """Drop a database if it exists, terminating active connections."""
    _validate_identifier(db_name)
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        if database_exists(conn, db_name):
            conn.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :name AND pid <> pg_backend_pid();
                    """
                ),
                {"name": db_name},
            )
            conn.execute(text(f'DROP DATABASE "{db_name}"'))
            logging.info("Dropped database '%s'.", db_name)


# --- ETL Functions ---
def extract_transform_data(engine: Engine, query_path: Path) -> pd.DataFrame | None:
    """Extract and transform data using a SQL query."""
    try:
        logging.info("Executing data extraction query from: %s", query_path.name)
        with engine.connect() as conn:
            df = pd.read_sql_query(query_path.read_text(encoding="utf-8"), conn)
        logging.info("Successfully extracted %d rows.", len(df))
        return df
    except exc.SQLAlchemyError as e:
        logging.error("Data extraction failed: %s", e)
        return None


def write_to_database(df: pd.DataFrame, engine: Engine) -> bool:
    """Write DataFrame to the specified database table."""
    try:
        logging.info("Loading data into table '%s'...", BENCHMARK_TABLE_NAME)
        df.to_sql(
            BENCHMARK_TABLE_NAME,
            engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
        )
        logging.info("Successfully loaded data.")
        return True
    except exc.SQLAlchemyError as e:
        logging.error("Failed to write data to database: %s", e)
        return False


def _map_db_to_sql_file(db_name: str) -> str:
    """Generate the corresponding SQL filename for a given benchmark database name."""
    if "text_nulls" in db_name:
        return "flatten_df9_text_nulls.sql"
    if "numeric" in db_name:
        return "flatten_df9.sql"
    raise ValueError(f"Cannot determine SQL file for benchmark database: {db_name}")


# --- Main Routine ---
def parse_arguments() -> argparse.Namespace:
    """Return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create and populate benchmark databases."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.ini"),
        help="Path to the configuration file (default: ./config.ini)",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="If specified, drop existing databases before creating them.",
    )
    return parser.parse_args()


def main() -> None:
    """Orchestrate the ETL process."""
    args = parse_arguments()
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_dir / LOG_FILE_NAME)

    logging.info("--- Starting benchmark database creation process ---")
    root_engine = None
    try:
        cfg = load_config(args.config)
        root_engine = get_engine(cfg)

        benchmark_db_to_sql_map = {
            db_name: _map_db_to_sql_file(db_name) for db_name in cfg.benchmark_dbs
        }

        if args.force_recreate:
            for db_name in cfg.benchmark_dbs:
                logging.info("Force-recreate enabled for '%s'.", db_name)
                drop_database(root_engine, db_name)

        for db_name in cfg.benchmark_dbs:
            create_database(root_engine, db_name)

        source_engine = get_engine(cfg, dbname=cfg.source_db)

        for db_name, sql_filename in benchmark_db_to_sql_map.items():
            logging.info("--- Processing benchmark database: %s ---", db_name)
            query_path = cfg.sql_dir / sql_filename

            df = extract_transform_data(source_engine, query_path)
            if df is None:
                logging.error("Halting: data extraction failed for %s.", db_name)
                continue

            target_engine = get_engine(cfg, dbname=db_name)
            if not write_to_database(df, target_engine):
                logging.error("Halting: failed to load data into %s.", db_name)

        logging.info("--- Benchmark database creation process complete. ---")

    except (ConfigurationError, ValueError) as e:
        logging.error("Fatal error during setup: %s", e)
        sys.exit(1)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        if root_engine:
            root_engine.dispose()


if __name__ == "__main__":
    main()
