# -*- coding: utf-8 -*-
"""Legacy TMP database setup script.

Refactored to comply with the Teotihuacan Mapping Project coding standards.
The script uses SQLAlchemy Core for all PostgreSQL interactions, validates the
configuration file, and provides robust, idempotent creation and population of
legacy databases.

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
from dataclasses import dataclass as _dataclass
import types


def dataclass(*args, **kwargs):
    """Safely apply ``dataclasses.dataclass`` even if module isn't registered."""
    def wrapper(cls):
        if cls.__module__ not in sys.modules:
            sys.modules[cls.__module__] = types.ModuleType(cls.__module__)
        return _dataclass(*args, **kwargs)(cls)

    return wrapper
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOG_FILE_NAME = "00_setup_databases.log"
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

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
        ConfigurationError: If the config file is missing, malformed, or invalid.
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
            "Please close all other connections to the database and try again.",
            db_name,
        )
        raise e from e
    else:
        logging.error("An unexpected error occurred with database '%s': %s", db_name, e)
        raise e from e


def populate_database(cfg: Config, db_name: str, sql_file: Path) -> None:
    """Populates a database from a SQL dump file using the psql utility."""
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
        logging.info("Successfully populated database '%s'.", db_name)
        if result.stdout:
            logging.debug("psql stdout:\n%s", result.stdout)
        if result.stderr:
            logging.warning("psql stderr:\n%s", result.stderr)

    except AttributeError as e:
        logging.error("Configuration error for psql connection: %s", e)
        raise
    except FileNotFoundError:
        logging.error(
            "psql command not found. Is PostgreSQL installed and in the system's PATH?"
        )
        raise
    except subprocess.CalledProcessError as e:
        logging.error(
            "Failed to populate database '%s'. psql exited with code %d.",
            db_name,
            e.returncode,
        )
        logging.error("psql stderr:\n%s", e.stderr)
        logging.error("psql stdout:\n%s", e.stdout)
        raise


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
    return parser.parse_args()


def main() -> None:
    """Orchestrate the database setup process."""
    args = parse_arguments()
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_dir / LOG_FILE_NAME)

    logging.info("--- Starting Legacy Database Setup ---")
    root_engine = None
    try:
        cfg = load_config(args.config)
        root_engine = get_engine(cfg)

        logging.info("Processing %d legacy databases...", len(cfg.legacy_dbs))
        for db_name in cfg.legacy_dbs:
            sql_file = cfg.dump_dir / f"{db_name}.sql"

            if args.force_recreate:
                logging.info("Force-recreate enabled for '%s'.", db_name)
                drop_database(root_engine, db_name)

            create_database(root_engine, db_name)
            populate_database(cfg, db_name, sql_file)

        logging.info("--- Legacy Database Setup Complete ---")

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
