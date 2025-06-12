# -*- coding: utf-8 -*-
"""
Creates and populates wide-format benchmark databases from TMP_DF9.

This script orchestrates an ETL (Extract, Transform, Load) process that leverages
two powerful, purpose-built SQL queries to generate benchmark databases.

1.  EXTRACT & TRANSFORM: It executes one of two complex SQL scripts against the
    live TMP_DF9 database:
    a) `flatten_df9.sql`: Flattens 18+ tables into a wide format, preserving
       numeric codes for categorical data.
    b) `flatten_df9_text_nulls.sql`: Performs the same flattening but also
       translates numeric codes to their text descriptions and converts
       known NA-marker values (e.g., -1, 'NONE') to standard SQL NULLs.
2.  LOAD: It creates two new PostgreSQL databases and loads the resulting
    DataFrame from each query into its respective database.

This approach offloads the complex transformation logic to the database engine
for maximum performance and robustness.

Usage:
    From the src/ directory, run:
    $ python 01_create_benchmark_dbs.py --config config.ini

"""

import argparse
import configparser
import logging
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# --- Constants ---
LOG_FILE_NAME = "01_create_benchmark_dbs.log"
BENCHMARK_TABLE_NAME = "wide_format_data"

# Mapping of benchmark database names to their corresponding SQL query files.
# This makes the script's logic clear and easily extensible.
BENCHMARK_DB_TO_SQL_MAP = {
    "tmp_benchmark_wide_numeric": "flatten_df9.sql",
    "tmp_benchmark_wide_text_nulls": "flatten_df9_text_nulls.sql",
}


# --- Logging Setup ---


def setup_logging(log_path: Path) -> None:
    """Configures logging to both console and a file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w"),  # Overwrite log on each run
            logging.StreamHandler(sys.stdout),
        ],
    )


# --- Argument Parsing ---


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create wide-format benchmark databases from TMP_DF9."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.ini",
        help="Path to the configuration file (default: config.ini)",
    )
    return parser.parse_args()


# --- Database Operations ---


def create_database(db_config: Dict, db_name: str) -> bool:
    """Creates a new PostgreSQL database if it doesn't already exist."""
    logging.info("Attempting to create database: '%s'...", db_name)
    try:
        with psycopg2.connect(**db_config) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                )
                logging.info("Database '%s' created successfully.", db_name)
    except psycopg2.errors.DuplicateDatabase:
        logging.warning("Database '%s' already exists. Skipping creation.", db_name)
    except psycopg2.Error as e:
        logging.error("Failed to create database '%s'. Error: %s", db_name, e)
        return False
    return True


def get_sqlalchemy_engine(db_config: Dict, db_name: str) -> Engine:
    """Creates a SQLAlchemy engine for a specific database."""
    try:
        db_url = (
            f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_name}"
        )
        return create_engine(db_url)
    except Exception as e:
        logging.critical(
            "Failed to create SQLAlchemy engine for '%s'. Error: %s", db_name, e
        )
        sys.exit(1)


def extract_transform_data(engine: Engine, query_path: Path) -> pd.DataFrame | None:
    """Loads and transforms data from the source DB using a specific SQL query."""
    if not query_path.is_file():
        logging.critical("SQL query file not found at: %s", query_path)
        return None

    logging.info("Reading query from '%s'...", query_path.name)
    with open(query_path, "r", encoding="utf-8") as f:
        query = f.read()

    logging.info(
        "Executing query against source database (this may take several minutes)..."
    )
    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(sql=text(query), con=connection)
        logging.info(
            "Successfully extracted data into DataFrame with shape: %s", df.shape
        )
        return df
    except Exception as e:
        logging.critical(
            "Failed to execute query from '%s'. Error: %s", query_path.name, e
        )
        return None


def write_to_database(df: pd.DataFrame, engine: Engine) -> bool:
    """Writes a DataFrame to the specified database."""
    db_name = engine.url.database
    logging.info(
        "Writing %s rows to table '%s' in database '%s'...",
        df.shape[0],
        BENCHMARK_TABLE_NAME,
        db_name,
    )
    try:
        # Using method='multi' is crucial for bulk insert performance.
        # chunksize helps manage memory for extremely large datasets.
        df.to_sql(
            name=BENCHMARK_TABLE_NAME,
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000,
        )
        logging.info("Successfully wrote data to '%s'.", db_name)
        return True
    except Exception as e:
        logging.error("Failed to write DataFrame to '%s'. Error: %s", db_name, e)
        return False


# --- Main Orchestrator ---


def main() -> None:
    """Main function to orchestrate the benchmark database creation."""
    args = parse_arguments()
    config_path = Path(args.config)

    log_file_path = Path(__file__).parent / LOG_FILE_NAME
    setup_logging(log_file_path)

    logging.info("Reading configuration...")
    if not config_path.is_file():
        logging.critical("Configuration file not found: %s", config_path)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        db_config_root = dict(config["postgresql"])
        source_db_name = config.get("databases", "benchmark_source_db")
        # The new benchmark DB name from the user's updated SQL script
        benchmark_dbs = ["tmp_benchmark_wide_numeric", "tmp_benchmark_wide_text_nulls"]
        sql_dir = Path(config.get("paths", "sql_queries_dir"))

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.critical("Config file is missing a required section or option: %s", e)
        sys.exit(1)

    logging.info("Starting benchmark database creation process...")

    # 1. Create the empty benchmark databases first
    for db_name in benchmark_dbs:
        if not create_database(db_config_root, db_name):
            logging.critical(
                "Halting: failed to create prerequisite database '%s'.",
                db_name,
            )
            sys.exit(1)

    # 2. Establish connection to the source database
    source_engine = get_sqlalchemy_engine(db_config_root, source_db_name)

    # 3. Loop through the map, execute the correct SQL, and load the correct DB
    for db_name, sql_filename in BENCHMARK_DB_TO_SQL_MAP.items():
        logging.info("--- Processing benchmark database: %s ---", db_name)
        query_path = sql_dir / sql_filename

        # Extract and Transform using the specified SQL query
        df = extract_transform_data(source_engine, query_path)
        if df is None:
            logging.error("Halting: data extraction failed for %s.", db_name)
            continue  # Try the next one, but this is a critical failure

        # Load data into the target benchmark database
        target_engine = get_sqlalchemy_engine(db_config_root, db_name)
        if not write_to_database(df, target_engine):
            logging.error("Halting: failed to load data into %s.", db_name)

    logging.info("--- Benchmark database creation process complete. ---")


if __name__ == "__main__":
    main()
