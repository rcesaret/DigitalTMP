# -*- coding: utf-8 -*-
"""
Creates and populates wide-format benchmark databases from TMP_DF9.

This script orchestrates an ETL (Extract, Transform, Load) process that
leverages two powerful, purpose-built SQL queries to generate benchmark
databases.

This enhanced version includes prerequisite checking and comprehensive
verification to ensure pipeline idempotency and robust execution.

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
import types
from dataclasses import dataclass as _dataclass
from pathlib import Path
from typing import List

import pandas as pd
from sqlalchemy import create_engine, exc, text
from sqlalchemy.engine import Connection, Engine

# Import verification utilities
try:
    from db_verification import (
        check_pipeline_prerequisites,
        verify_benchmark_database_ready,
        verify_database_exists,
        verify_schema_populated,
    )
except ImportError:
    # Fallback functions if verification module not available
    def verify_database_exists(engine, db_name):
        return False

    def verify_schema_populated(engine, schema_name, min_tables=1):
        return False, {}

    def verify_benchmark_database_ready(engine, table_name="wide_format_data"):
        return False

    def check_pipeline_prerequisites(cfg, script_name):
        return True, []


def dataclass(*args, **kwargs):
    """Safely apply ``dataclasses.dataclass`` even if module isn't
    registered."""

    def wrapper(cls):
        if cls.__module__ not in sys.modules:
            sys.modules[cls.__module__] = types.ModuleType(cls.__module__)
        return _dataclass(*args, **kwargs)(cls)

    return wrapper


# --- Constants ---
LOG_FILE_NAME = "01_create_benchmark_dbs.log"
BENCHMARK_TABLE_NAME = "wide_format_data"
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Comprehensive indexing SQL for benchmark databases
INDEXING_SQL = """
-- ============================================================================
--                      COMPREHENSIVE INDEXING
-- ============================================================================
-- Create a dedicated index for each key analytical variable to ensure
-- a fair performance comparison against the heavily-indexed legacy schemas.
-- ============================================================================

CREATE INDEX idx_ssn ON public.wide_format_data ("SSN");
CREATE INDEX idx_site ON public.wide_format_data ("site");
CREATE INDEX idx_subsite ON public.wide_format_data ("subsite");
CREATE INDEX idx_northing ON public.wide_format_data ("northing");
CREATE INDEX idx_easting ON public.wide_format_data ("easting");
CREATE INDEX idx_unit ON public.wide_format_data ("unit");
CREATE INDEX idx_collectionYear ON public.wide_format_data
    ("collectionYear");
CREATE INDEX idx_collectionQuarter ON public.wide_format_data
    ("collectionQuarter");
CREATE INDEX idx_obsidianTot ON public.wide_format_data ("obsidianTot");
CREATE INDEX idx_constructQual ON public.wide_format_data ("constructQual");
CREATE INDEX idx_arch1XlMe ON public.wide_format_data ("arch1XlMe");
CREATE INDEX idx_arch2XlMe ON public.wide_format_data ("arch2XlMe");
CREATE INDEX idx_func1XlMe ON public.wide_format_data ("func1XlMe");
CREATE INDEX idx_func2XlMe ON public.wide_format_data ("func2XlMe");
CREATE INDEX idx_siteAlteration ON public.wide_format_data
    ("siteAlteration");
CREATE INDEX idx_analysisYear ON public.wide_format_data ("analysisYear");
CREATE INDEX idx_ceramicAbundance ON public.wide_format_data
    ("ceramicAbundance");
CREATE INDEX idx_totAll ON public.wide_format_data ("totAll");
CREATE INDEX idx_areaStruct ON public.wide_format_data ("areaStruct");
"""


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
        source_db=db_section.get("benchmark_source_db"),
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
            logging.info("Database '%s' already exists, skipping creation.", db_name)


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
    """Write DataFrame to the specified database table with indexing and
    optimization."""
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

        # Create indexes for optimal performance
        logging.info("Creating comprehensive indexes...")
        with engine.connect().execution_options(autocommit=True) as conn:
            conn.execute(text(INDEXING_SQL))
        logging.info("Successfully created all indexes.")

        # Run ANALYZE to update table statistics for query planner
        logging.info("Running ANALYZE to update table statistics...")
        with engine.connect().execution_options(autocommit=True) as conn:
            conn.execute(text("ANALYZE public.wide_format_data;"))
        logging.info("ANALYZE complete.")

        return True
    except exc.SQLAlchemyError as e:
        logging.error("Failed to write data to database: %s", e)
        return False


def _map_db_to_sql_file(db_name: str) -> str:
    """Generate the corresponding SQL filename for a given benchmark
    database name."""
    if "text_nulls" in db_name:
        return "flatten_df9_text_nulls.sql"
    if "numeric" in db_name:
        return "flatten_df9.sql"
    raise ValueError(f"Cannot determine SQL file for benchmark database: {db_name}")


def verify_benchmark_database(cfg: Config, db_name: str) -> bool:
    """Verify that a benchmark database is properly set up."""
    try:
        target_engine = get_engine(cfg, dbname=db_name)
        is_ready = verify_benchmark_database_ready(target_engine)
        target_engine.dispose()
        return is_ready
    except Exception as e:
        logging.error("Failed to verify benchmark database '%s': %s", db_name, e)
        return False


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
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing benchmark databases, don't create.",
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
    creation_success = True

    try:
        cfg = load_config(args.config)
        root_engine = get_engine(cfg)

        # Check prerequisites
        if not args.verify_only:
            logging.info("Checking prerequisites...")
            prereqs_met, errors = check_pipeline_prerequisites(
                cfg, "01_create_benchmark_dbs.py"
            )
            if not prereqs_met:
                logging.error("Prerequisites not met:")
                for error in errors:
                    logging.error("  - %s", error)
                logging.error("Please run 00_setup_databases.py first.")
                sys.exit(1)
            logging.info("✓ All prerequisites satisfied.")

        benchmark_db_to_sql_map = {
            db_name: _map_db_to_sql_file(db_name) for db_name in cfg.benchmark_dbs
        }

        # Verify or create each benchmark database
        for i, db_name in enumerate(cfg.benchmark_dbs, 1):
            logging.info("=" * 60)
            logging.info(
                "Processing benchmark database %d/%d: %s",
                i,
                len(cfg.benchmark_dbs),
                db_name,
            )
            logging.info("=" * 60)

            # Check if database already exists and is properly set up
            db_exists = verify_database_exists(root_engine, db_name)

            if db_exists and not args.force_recreate:
                is_verified = verify_benchmark_database(cfg, db_name)
                if is_verified:
                    logging.info(
                        "✓ Database '%s' already properly set up, " "skipping.", db_name
                    )
                    if args.verify_only:
                        continue
                    continue
                else:
                    logging.warning(
                        "✗ Database '%s' exists but needs " "reconstruction.", db_name
                    )
                    if args.verify_only:
                        creation_success = False
                        continue

            if args.verify_only:
                if not db_exists:
                    logging.error("Database '%s' does not exist.", db_name)
                    creation_success = False
                continue

            # Create/recreate database
            if args.force_recreate and db_exists:
                logging.info("Force-recreate enabled for '%s'.", db_name)
                drop_database(root_engine, db_name)

            create_database(root_engine, db_name)

            # Extract and load data
            sql_filename = benchmark_db_to_sql_map[db_name]
            query_path = cfg.sql_dir / sql_filename

            source_engine = get_engine(cfg, dbname=cfg.source_db)
            df = extract_transform_data(source_engine, query_path)
            source_engine.dispose()

            if df is None:
                logging.error("Halting: data extraction failed for %s.", db_name)
                creation_success = False
                continue

            target_engine = get_engine(cfg, dbname=db_name)
            write_success = write_to_database(df, target_engine)
            target_engine.dispose()

            if not write_success:
                logging.error("Halting: failed to load data into %s.", db_name)
                creation_success = False
                continue

            # Verify the result
            is_verified = verify_benchmark_database(cfg, db_name)
            if is_verified:
                logging.info(
                    "✓ Database '%s' successfully created and " "verified.", db_name
                )
            else:
                logging.error("✗ Database '%s' creation appears incomplete.", db_name)
                creation_success = False

        # Final summary
        logging.info("=" * 60)
        if args.verify_only:
            if creation_success:
                logging.info("✓ All benchmark databases verified " "successfully.")
            else:
                logging.error("✗ Some benchmark databases failed " "verification.")
        else:
            if creation_success:
                logging.info(
                    "✓ Benchmark database creation complete - " "All databases ready"
                )
            else:
                logging.error("✗ Benchmark database creation encountered " "errors")
        logging.info("=" * 60)

    except (ConfigurationError, ValueError) as e:
        logging.error("Fatal error during setup: %s", e)
        sys.exit(1)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        if root_engine:
            root_engine.dispose()

    if not creation_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
