# -*- coding: utf-8 -*-
"""
Sets up the legacy Teotihuacan Mapping Project (TMP) databases.

This script reads configuration from a .ini file to connect to a PostgreSQL
server. It then iterates through a list of legacy databases, creating each one
if it does not already exist, and populates it by executing the corresponding
.sql dump file.

The script is designed to be idempotent; it can be run multiple times without
causing errors or changing the state of already-existing databases.

All operations are logged to both the console and a file named
'00_setup_databases.log' in the same directory.

Usage:
    From the src/ directory, run:
    $ python 00_setup_databases.py --config config.ini

"""
import argparse
import configparser
import logging
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# --- Constants ---
LOG_FILE_NAME = "00_setup_databases.log"

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
        description="Create and populate legacy TMP databases in PostgreSQL."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.ini",
        help="Path to the configuration file (default: config.ini)"
    )
    return parser.parse_args()

# --- Database Operations ---
def create_database(db_config: dict, db_name: str) -> bool:
    """
    Creates a new database in PostgreSQL if it doesn't already exist.

    Args:
        db_config: A dictionary with connection details (host, user, etc.).
        db_name: The name of the database to create.

    Returns:
        True if the operation was successful (or DB already existed),
        False otherwise.
    """
    logging.info(f"Attempting to create database: '{db_name}'...")
    try:
        # Connect to the root database to perform CREATE DATABASE
        with psycopg2.connect(**db_config) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cur:
                # Use psycopg2.sql to safely quote the identifier
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                )
                logging.info(f"Database '{db_name}' created successfully.")

    except psycopg2.errors.DuplicateDatabase:
        logging.warning(
            f"Database '{db_name}' already exists. Skipping creation."
        )
    except psycopg2.Error as e:
        logging.error(f"Failed to create database '{db_name}'. Error: {e}")
        return False
    
    return True

def populate_database(db_config: dict, db_name: str, sql_file_path: Path) -> bool:
    """
    Populates a database by executing a .sql script.

    Args:
        db_config: A dictionary with connection details.
        db_name: The name of the target database to populate.
        sql_file_path: The path to the .sql file to execute.

    Returns:
        True on success, False on failure.
    """
    if not sql_file_path.is_file():
        logging.error(f"SQL script not found at: {sql_file_path}")
        return False

    logging.info(f"Populating '{db_name}' from '{sql_file_path.name}'...")
    
    # Update config to connect to the newly created database
    target_db_config = db_config.copy()
    target_db_config["dbname"] = db_name

    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        with psycopg2.connect(**target_db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_script)
        
        logging.info(f"Successfully populated database '{db_name}'.")

    except psycopg2.Error as e:
        logging.error(f"Failed to populate database '{db_name}'. Error: {e}")
        return False
    except IOError as e:
        logging.error(f"Could not read SQL file '{sql_file_path}'. Error: {e}")
        return False
        
    return True

# --- Main Orchestrator ---
def main() -> None:
    """Main function to orchestrate database setup."""
    args = parse_arguments()
    config_path = Path(args.config)
    
    # Assume log file is in the same directory as the script
    log_file_path = Path(__file__).parent / LOG_FILE_NAME
    setup_logging(log_file_path)

    if not config_path.is_file():
        logging.critical(f"Configuration file not found at: {config_path}")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        # Prepare connection config for the root database
        db_config = {
            "host": config.get("postgresql", "host"),
            "port": config.get("postgresql", "port"),
            "user": config.get("postgresql", "user"),
            "password": config.get("postgresql", "password"),
            "dbname": config.get("postgresql", "root_db")
        }
        legacy_dbs = [db.strip() for db in config.get("databases", "legacy_dbs").split(',')]
        sql_dump_dir = Path(config.get("paths", "sql_dump_dir"))
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.critical(f"Configuration file is missing a required section or option: {e}")
        sys.exit(1)
        
    logging.info("Starting legacy database setup process...")

    for db_name in legacy_dbs:
        logging.info(f"--- Processing: {db_name} ---")
        
        # Create the database
        if not create_database(db_config, db_name):
            continue # Skip to next DB if creation failed

        # Populate the database
        sql_file = sql_dump_dir / f"{db_name}.sql"
        populate_database(db_config, db_name, sql_file)

    logging.info("--- Legacy database setup process complete. ---")

if __name__ == "__main__":
    main()
