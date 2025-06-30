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
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

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


def _require(section: configparser.SectionProxy, key: str) -> str:
    """Return *key* from *section* or raise *ConfigurationError*."""
    try:
        return section[key]
    except KeyError as exc:  # pragma: no cover – clarity outweighs micro-benchmarks
        raise ConfigurationError(
            f"Missing required key '{key}' in section [{section.name}]."
        ) from exc


class ConfigurationError(RuntimeError):
    """Raised when the configuration file is missing required values."""


def load_config(path: Path) -> Config:
    """Load and validate the ini configuration file.

    Args:
        path: Path to ``config.ini``.

    Returns:
        An immutable :class:`Config` instance populated with validated values.

    Raises:
        ConfigurationError: If required sections/keys are absent.
    """
    parser = configparser.ConfigParser()
    if not path.is_file():
        raise ConfigurationError(f"Config file not found: {path}")

    try:
        parser.read(path)
    except configparser.Error as exc:
        raise ConfigurationError(f"Invalid config file: {exc}") from exc

    try:
        pg_section = parser["postgresql"]
        db_section = parser["databases"]
    except KeyError as exc:
        raise ConfigurationError(
            "Required sections [postgresql] or [databases] missing."
        ) from exc

    legacy_dbs_raw = _require(db_section, "legacy_dbs")
    legacy_dbs = [db.strip() for db in legacy_dbs_raw.split(",") if db.strip()]
    if not legacy_dbs:
        raise ConfigurationError("No databases listed under [databases] legacy_dbs.")

    dump_dir = Path(db_section.get("dump_dir", "dumps")).resolve()

    return Config(
        host=_require(pg_section, "host"),
        port=_require(pg_section, "port"),
        user=_require(pg_section, "user"),
        password=_require(pg_section, "password"),
        root_db=_require(pg_section, "root_db"),
        legacy_dbs=legacy_dbs,
        dump_dir=dump_dir,
    )


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _validate_identifier(name: str) -> None:
    """Ensure *name* is a valid PostgreSQL identifier to guard against injection."""
    if not _VALID_IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"'{name}' is not a valid PostgreSQL identifier.")


def get_engine(cfg: Config, *, dbname: str | None = None) -> Engine:
    """Create a SQLAlchemy engine using parameters from *cfg*.

    Args:
        cfg: Validated configuration container.
        dbname: Optional database name override. Defaults to *cfg.root_db*.

    Returns:
        A lazily-initialised SQLAlchemy :class:`Engine`.
    """
    database = dbname or cfg.root_db
    url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}".format(
        user=cfg.user,
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
        db=database,
    )
    return create_engine(url, echo=False, future=True)


def database_exists(conn, db_name: str) -> bool:  # noqa: ANN001 – SA connection type
    """Return ``True`` if *db_name* is present on the server."""
    res = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": db_name}
    )
    return res.scalar_one_or_none() is not None


def create_database(root_engine: Engine, db_name: str) -> None:
    """Create *db_name* if it is absent.

    The operation runs outside a transaction (`AUTOCOMMIT`) as PostgreSQL forbids
    ``CREATE DATABASE`` inside one.
    """
    _validate_identifier(db_name)
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        if database_exists(conn, db_name):
            logging.info("Database '%s' already exists – skipping create.", db_name)
            return
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        logging.info("Created database '%s'.", db_name)


def drop_database(root_engine: Engine, db_name: str) -> None:
    """Drop *db_name* if it exists, terminating active connections first."""
    _validate_identifier(db_name)
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        if not database_exists(conn, db_name):
            logging.info("Database '%s' does not exist – skipping drop.", db_name)
            return
        # Terminate connections to the target database (except current backend)
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


def populate_database(cfg: Config, db_name: str, sql_file: Path) -> None:
    """Run *sql_file* against *db_name*.

    Args:
        cfg: Project configuration container.
        db_name: Target database to populate.
        sql_file: Path to the ``.sql`` dump file.
    """
    if not sql_file.is_file():
        logging.warning("SQL dump not found: %s – skipping population.", sql_file)
        return

    engine = get_engine(cfg, dbname=db_name)
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(sql_file.read_text(encoding="utf-8"))
            logging.info("Populated database '%s' using '%s'.", db_name, sql_file.name)
    finally:
        engine.dispose()


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
    return parser.parse_args()
