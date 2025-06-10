# -*- coding: utf-8 -*-
"""
Creates and populates wide-format benchmark databases from a legacy DB.

This script performs an ETL (Extract, Transform, Load) process:
1.  EXTRACT: Reads data from a specified complex legacy database (TMP_DF9)
    by executing a large SQL flattening query.
2.  TRANSFORM: Prepares the resulting DataFrame in two ways:
    a. 'numeric': Coded value columns are converted to numeric types.
    b. 'text': Coded value columns are converted to text/string types.
3.  LOAD: Creates two new PostgreSQL databases and loads each transformed
    DataFrame into its respective database.

These benchmark databases serve as a performance baseline to compare against
the highly normalized legacy schemas.

Usage:
    From the src/ directory, run:
    $ python 01_create_benchmark_dbs.py --config config.ini

"""
import argparse
import configparser
import logging
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# --- Constants ---
LOG_FILE_NAME = "01_create_benchmark_dbs.log"
BENCHMARK_TABLE_NAME = "wide_format_data"

# A list of column name substrings that identify "coded value" columns
# which need to be transformed for the numeric vs. text benchmark DBs.
CODED_COLUMN_SUBSTRINGS = [
    "_Code", "_Pres", "_Conf", "_Density", "_Type", "_Orient",
    "_Shape", "_TALUD", "_TABLERO", "_Stairway", "_Color", "_Hard",
    "_Present"
]


# --- Logging Setup ---
def setup_logging(log_path: Path) -> None:
    """Configures logging to both console and a file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
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
        help="Path to the configuration file (default: config.ini)"
    )
    return parser.parse_args()


# --- Database Operations ---
def create_database(db_config: Dict, db_name: str) -> bool:
    """Creates a new PostgreSQL database if it doesn't already exist."""
    logging.info(f"Attempting to create database: '{db_name}'...")
    try:
        with psycopg2.connect(**db_config) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                logging.info(f"Database '{db_name}' created successfully.")
    except psycopg2.errors.DuplicateDatabase:
        logging.warning(f"Database '{db_name}' already exists. Skipping creation.")
    except psycopg2.Error as e:
        logging.error(f"Failed to create database '{db_name}'. Error: {e}")
        return False
    return True


def get_sqlalchemy_engine(db_config: Dict, db_name: str) -> Engine:
    """Creates a SQLAlchemy engine for a specific database."""
    db_url = (
        f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_name}"
    )
    return create_engine(db_url)


def load_flattened_data(engine: Engine, query_path: Path) -> pd.DataFrame | None:
    """Loads data from the source DB using the flattening SQL query."""
    if not query_path.is_file():
        logging.critical(f"Flattening query not found at: {query_path}")
        return None
    
    logging.info("Reading flattening query from file...")
    with open(query_path, 'r', encoding='utf-8') as f:
        query = f.read()

    logging.info("Executing flattening query against source database (this may take a moment)...")
    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(sql=text(query), con=connection)
        logging.info(f"Successfully extracted data into DataFrame with shape: {df.shape}")
        return df
    except Exception as e:
        logging.critical(f"Failed to execute flattening query. Error: {e}")
        return None


def prepare_dataframe(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Prepares DataFrame dtypes for either 'numeric' or 'text' mode."""
    df_copy = df.copy()
    
    coded_cols = [
        col for col in df_copy.columns
        if any(sub in col for sub in CODED_COLUMN_SUBSTRINGS)
    ]
    logging.info(f"Found {len(coded_cols)} coded columns to transform for '{mode}' mode.")

    for col in coded_cols:
        if mode == 'numeric':
            # Convert to numeric, coercing errors to NaT. Use nullable integer.
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').astype('Int64')
        elif mode == 'text':
            # Convert to string, ensuring NaNs become empty strings or a marker.
            df_copy[col] = df_copy[col].astype(str).fillna('NULL_AS_TEXT')
    
    return df_copy


def write_to_database(df: pd.DataFrame, engine: Engine) -> bool:
    """Writes a DataFrame to the specified database."""
    db_name = engine.url.database
    logging.info(f"Writing {df.shape[0]} rows to table '{BENCHMARK_TABLE_NAME}' in database '{db_name}'...")
    try:
        # Use method='multi' for significant performance improvement.
        # chunksize helps manage memory for very large datasets.
        df.to_sql(
            name=BENCHMARK_TABLE_NAME,
            con=engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )
        logging.info(f"Successfully wrote data to '{db_name}'.")
        return True
    except Exception as e:
        logging.error(f"Failed to write DataFrame to '{db_name}'. Error: {e}")
        return False


# --- Main Orchestrator ---
def main() -> None:
    """Main function to orchestrate the benchmark database creation."""
    args = parse_arguments()
    config_path = Path(args.config)
    
    log_file_path = Path(__file__).parent / LOG_FILE_NAME
    setup_logging(log_file_path)

    if not config_path.is_file():
        logging.critical(f"Configuration file not found at: {config_path}")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        # Prepare connection config for the root database
        db_config_root = {
            "host": config.get("postgresql", "host"),
            "port": config.get("postgresql", "port"),
            "user": config.get("postgresql", "user"),
            "password": config.get("postgresql", "password"),
            "dbname": config.get("postgresql", "root_db")
        }
        source_db_name = config.get("databases", "benchmark_source_db")
        benchmark_dbs = [db.strip() for db in config.get("databases", "benchmark_dbs").split(',')]
        flatten_query_path = Path(config.get("paths", "sql_dump_dir")).parent.parent / "sql/flatten_df9.sql"
        flatten_query_path = Path("sql/flatten_df9.sql")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.critical(f"Config file is missing a required section or option: {e}")
        sys.exit(1)

    logging.info("Starting benchmark database creation process...")

    # 1. Create the empty benchmark databases
    for db_name in benchmark_dbs:
        if not create_database(db_config_root, db_name):
            logging.critical(f"Halting process because creation of '{db_name}' failed.")
            sys.exit(1)

    # 2. Extract data from source database
    source_engine = get_sqlalchemy_engine(db_config_root, source_db_name)
    base_df = load_flattened_data(source_engine, flatten_query_path)
    if base_df is None:
        logging.critical("Halting process because data extraction failed.")
        sys.exit(1)

    # 3. Transform and Load for each benchmark DB
    for db_name in benchmark_dbs:
        logging.info(f"--- Processing for benchmark database: {db_name} ---")
        if 'numeric' in db_name:
            mode = 'numeric'
        elif 'text' in db_name:
            mode = 'text'
        else:
            logging.warning(f"Could not determine mode for '{db_name}'. Skipping.")
            continue
            
        transformed_df = prepare_dataframe(base_df, mode)
        target_engine = get_sqlalchemy_engine(db_config_root, db_name)
        write_to_database(transformed_df, target_engine)

    logging.info("--- Benchmark database creation process complete. ---")


if __name__ == "__main__":
    main()