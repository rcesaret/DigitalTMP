# -*- coding: utf-8 -*-
"""Legacy TMP database setup script.

Refactored to comply with the Teotihuacan Mapping Project coding standards.
The script uses SQLAlchemy Core for all PostgreSQL interactions, validates the
configuration file, and provides robust, idempotent creation and population of
legacy databases.

This enhanced version includes comprehensive verification to ensure true
idempotency and reliable pipeline execution.

Usage
-----
From the ``src/`` directory run::

    $ python 00_setup_databases.py --config config.ini

"""

from __future__ import annotations

import argparse
import configparser
import logging
import os
import re
import subprocess
import sys
import types
from dataclasses import dataclass as _dataclass
from pathlib import Path
from typing import List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine


def dataclass(*args, **kwargs):
    """Safely apply ``dataclasses.dataclass`` even if module isn't
    registered."""

    def wrapper(cls):
        if cls.__module__ not in sys.modules:
            sys.modules[cls.__module__] = types.ModuleType(cls.__module__)
        return _dataclass(*args, **kwargs)(cls)

    return wrapper


# Import our verification utilities
try:
    from db_verification import verify_database_exists, verify_schema_populated
except ImportError:
    # Fallback if module not available
    def verify_database_exists(engine, db_name):
        return False

    def verify_schema_populated(engine, schema_name, min_tables=1):
        return False, {}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOG_FILE_NAME = "00_setup_databases.log"
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Expected minimum tables per database for verification
DB_MIN_TABLES = {
    "TMP_DF8": 27,
    "TMP_DF9": 62,
    "TMP_DF10": 9,
    "TMP_REAN_DF2": 13,
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    """Typed container for validated configuration settings."""

    host: str
    port: str
    user: str
    password: str
    root_db: str
    legacy_dbs: List[str]
    dump_dir: Path


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(log_path: Path) -> None:
    """Configure logging to console *and* rotating file.

    Args:
        log_path: Destination of the log file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# ---------------------------------------------------------------------------
# Configuration handling
# ---------------------------------------------------------------------------


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


def load_config(config_path: Path) -> Config:
    """Parse and validate the ``.ini`` configuration file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        A validated ``Config`` object.

    Raises:
        ConfigurationError: If the config file is missing, malformed, or
            invalid.
    """
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

    legacy_dbs_raw = db_section.get("legacy_dbs", "")
    legacy_dbs = [db.strip() for db in legacy_dbs_raw.split(",") if db.strip()]
    for db_name in legacy_dbs:
        _validate_identifier(db_name)

    dump_dir = (config_path.parent / path_section.get("sql_dump_dir")).resolve()

    return Config(
        host=pg_section.get("host"),
        port=pg_section.get("port"),
        user=pg_section.get("user"),
        password=pg_section.get("password"),
        root_db=pg_section.get("root_db"),
        legacy_dbs=legacy_dbs,
        dump_dir=dump_dir,
    )


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _validate_identifier(name: str) -> None:
    """Raise ValueError if *name* is not a valid SQL identifier."""
    if not _VALID_IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid identifier: '{name}'")


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
        if database_exists(conn, db_name):
            logging.info("Database '%s' already exists – skipping creation.", db_name)
            return
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        logging.info("Created database '%s'.", db_name)


def drop_database(root_engine: Engine, db_name: str) -> None:
    """Drop a database if it exists, terminating active connections."""
    _validate_identifier(db_name)
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        if not database_exists(conn, db_name):
            logging.info("Database '%s' does not exist – skipping drop.", db_name)
            return
        try:
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
        except Exception as e:
            handle_db_error(e, db_name)


def handle_db_error(e: Exception, db_name: str) -> None:
    """Log database-related errors with specific guidance."""
    if "does not exist" in str(e):
        logging.warning("Database '%s' does not exist, skipping drop.", db_name)
    elif "is being accessed by other users" in str(e):
        logging.error(
            "Could not drop database '%s' because it is in use. "
            "Please close all other connections to the database and "
            "try again.",
            db_name,
        )
        raise e from e
    else:
        logging.error("An unexpected error occurred with database '%s': %s", db_name, e)
        raise e from e


def populate_database(cfg: Config, db_name: str, sql_file: Path) -> bool:
    """Populates a database from a SQL dump file using the psql utility.

    Returns:
        True if population was successful, False otherwise.
    """
    try:
        user = cfg.user
        password = cfg.password
        host = cfg.host
        port = cfg.port

        # Set the password via environment variable for security
        env = os.environ.copy()
        env["PGPASSWORD"] = password

        command = [
            "psql",
            "-U",
            user,
            "-h",
            host,
            "-p",
            port,
            "-d",
            db_name,
            "-f",
            str(sql_file),
        ]

        logging.info(
            "Executing psql to populate database '%s' from '%s'...",
            db_name,
            sql_file.name,
        )
        result = subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Check for common warning patterns that might indicate issues
        if result.stderr:
            stderr_lower = result.stderr.lower()
            if "error" in stderr_lower:
                logging.error("psql reported errors:\n%s", result.stderr)
                return False
            elif "duplicate key" in stderr_lower:
                logging.warning(
                    "psql reported duplicate key warnings "
                    "(expected on re-population):\n%s",
                    result.stderr,
                )
            else:
                logging.info("psql completed with warnings:\n%s", result.stderr)

        if result.stdout:
            logging.debug("psql stdout:\n%s", result.stdout)

        logging.info("Successfully executed psql for database '%s'.", db_name)
        return True

    except AttributeError as e:
        logging.error("Configuration error for psql connection: %s", e)
        return False
    except FileNotFoundError:
        logging.error(
            "psql command not found. Is PostgreSQL installed and in the "
            "system's PATH?"
        )
        return False
    except subprocess.CalledProcessError as e:
        logging.error(
            "Failed to populate database '%s'. psql exited with code %d.",
            db_name,
            e.returncode,
        )
        logging.error("psql stderr:\n%s", e.stderr)
        logging.error("psql stdout:\n%s", e.stdout)
        return False


def verify_database_setup(cfg: Config, db_name: str) -> Tuple[bool, str]:
    """Verify that a database was properly set up with data.

    Args:
        cfg: Configuration object
        db_name: Name of database to verify

    Returns:
        Tuple of (success, message)
    """
    try:
        # Connect to the database
        db_engine = get_engine(cfg, db_name)

        # Verify basic connection
        with db_engine.connect():
            pass

        # Check schema population
        # Convention: schema name = lowercase db name
        schema_name = db_name.lower()
        min_tables = DB_MIN_TABLES.get(db_name, 5)

        is_populated, table_stats = verify_schema_populated(
            db_engine, schema_name, min_tables
        )

        db_engine.dispose()

        if is_populated:
            total_rows = sum(count for count in table_stats.values() if count > 0)
            return (
                True,
                f"Database '{db_name}' verified: "
                f"{len(table_stats)} tables, {total_rows} total rows",
            )
        else:
            return (False, f"Database '{db_name}' appears empty or " f"corrupted")

    except Exception as e:
        return False, f"Failed to verify database '{db_name}': {e}"


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    """Return command-line arguments."""
    parser = argparse.ArgumentParser(description="Setup legacy TMP databases.")
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
        help="Only verify existing databases, don't create or populate.",
    )
    return parser.parse_args()


def main() -> None:
    """Orchestrate the database setup process."""
    args = parse_arguments()
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_dir / LOG_FILE_NAME)

    logging.info("--- Starting Legacy Database Setup ---")
    root_engine = None
    setup_success = True

    try:
        cfg = load_config(args.config)
        root_engine = get_engine(cfg)

        logging.info("Processing %d legacy databases...", len(cfg.legacy_dbs))

        # Verify dump files exist
        for db_name in cfg.legacy_dbs:
            sql_file = cfg.dump_dir / f"{db_name}.sql"
            if not sql_file.is_file():
                logging.error("SQL dump file not found: %s", sql_file)
                setup_success = False

        if not setup_success:
            logging.error("Missing SQL dump files. Cannot proceed.")
            sys.exit(1)

        # Process each database
        for i, db_name in enumerate(cfg.legacy_dbs, 1):
            logging.info("=" * 60)
            logging.info(
                "Processing database %d/%d: %s", i, len(cfg.legacy_dbs), db_name
            )
            logging.info("=" * 60)

            sql_file = cfg.dump_dir / f"{db_name}.sql"

            # Check if database already exists and is populated
            db_exists = verify_database_exists(root_engine, db_name)

            if db_exists and not args.force_recreate:
                # Verify existing database
                is_verified, message = verify_database_setup(cfg, db_name)
                if is_verified:
                    logging.info("✓ %s", message)
                    if args.verify_only:
                        continue
                    logging.info(
                        "Database '%s' already properly set up, " "skipping.", db_name
                    )
                    continue
                else:
                    logging.warning("✗ %s", message)
                    if args.verify_only:
                        setup_success = False
                        continue
                    logging.info(
                        "Database '%s' exists but needs " "re-population.", db_name
                    )

            if args.verify_only:
                if not db_exists:
                    logging.error("Database '%s' does not exist.", db_name)
                    setup_success = False
                continue

            # Create/recreate database
            if args.force_recreate and db_exists:
                logging.info("Force-recreate enabled for '%s'.", db_name)
                drop_database(root_engine, db_name)

            create_database(root_engine, db_name)

            # Populate database
            populate_success = populate_database(cfg, db_name, sql_file)

            if not populate_success:
                logging.error("Failed to populate database '%s'.", db_name)
                setup_success = False
                continue

            # Verify population was successful
            is_verified, message = verify_database_setup(cfg, db_name)
            if is_verified:
                logging.info("✓ %s", message)
            else:
                logging.error("✗ %s", message)
                setup_success = False

        # Final summary
        logging.info("=" * 60)
        if args.verify_only:
            if setup_success:
                logging.info("✓ All legacy databases verified successfully.")
            else:
                logging.error("✗ Some legacy databases failed verification.")
        else:
            if setup_success:
                logging.info(
                    "✓ Legacy Database Setup Complete - " "All databases ready"
                )
            else:
                logging.error("✗ Legacy Database Setup encountered errors")
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

    if not setup_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
