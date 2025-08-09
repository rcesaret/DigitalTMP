# -*- coding: utf-8 -*-
"""Extract all tables from legacy TMP databases to CSV files.

This script performs comprehensive ETL operations to extract all tables from
the four legacy TMP databases (TMP_DF8, TMP_DF9, TMP_DF10, TMP_REAN_DF2) and
save them as individual CSV files in database-specific subdirectories.

The script follows the DigitalTMP project standards:
- Uses SQLAlchemy Core for all PostgreSQL interactions
- Implements comprehensive logging and error handling
- Preserves data integrity with proper encoding and NULL handling
- Provides detailed progress tracking and verification

Usage
-----
From the ``src/`` directory run::

    $ python 00_db_tables_extract.py --config config.ini

Author: Cascade AI
Date: 2025-01-15
"""

from __future__ import annotations

import argparse
import configparser
import logging
import sys
import types
from dataclasses import dataclass as _dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def dataclass(*args, **kwargs):
    """Safely apply ``dataclasses.dataclass`` even if module isn't
    registered."""

    def wrapper(cls):
        if cls.__module__ not in sys.modules:
            sys.modules[cls.__module__] = types.ModuleType(cls.__module__)
        return _dataclass(*args, **kwargs)(cls)

    return wrapper


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOG_FILE_NAME = "00_db_tables_extract.log"
DEFAULT_CHUNK_SIZE = 10000
DEFAULT_ENCODING = "latin1"
DEFAULT_CSV_DELIMITER = ","


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    """Typed container for validated configuration settings.

    Attributes:
        host: PostgreSQL server hostname
        port: PostgreSQL server port
        user: PostgreSQL username
        password: PostgreSQL password
        root_db: Default PostgreSQL database for connections
        legacy_dbs: List of legacy database names to extract
        output_paths: Mapping of DB names to their CSV output directories
        chunk_size: Row chunk size for large table extraction
        encoding: Character encoding for CSV files
        csv_delimiter: CSV field delimiter
        include_headers: Whether to include column headers in CSVs
        overwrite_existing: Whether to overwrite existing CSV files
        verify_row_counts: Whether to verify row counts after extraction
        verify_file_creation: Whether to verify file creation after extraction
    """

    host: str
    port: str
    user: str
    password: str
    root_db: str
    legacy_dbs: List[str]
    output_paths: Dict[str, Path]
    chunk_size: int = DEFAULT_CHUNK_SIZE
    encoding: str = DEFAULT_ENCODING
    csv_delimiter: str = DEFAULT_CSV_DELIMITER
    include_headers: bool = True
    overwrite_existing: bool = False
    verify_row_counts: bool = True
    verify_file_creation: bool = True


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class TableExtractionError(Exception):
    """Custom exception for table extraction failures."""


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


# ---------------------------------------------------------------------------
# Logging Setup
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
# Configuration Handling
# ---------------------------------------------------------------------------


def _validate_identifier(name: str) -> None:
    """Raise ValueError if *name* is not a valid SQL identifier."""
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"Invalid identifier: {name}")


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

    # Parse legacy databases
    legacy_dbs_raw = db_section.get("legacy_dbs", "")
    legacy_dbs = [db.strip() for db in legacy_dbs_raw.split(",") if db.strip()]
    for db_name in legacy_dbs:
        _validate_identifier(db_name)

    # Build output path mapping
    output_paths = {}
    for db_name in legacy_dbs:
        # Map database names to their configured output directories
        path_key = f"{db_name.lower().replace('_', '_')}_extracted_csvs_dir"
        if path_key in path_section:
            output_dir = config_path.parent / path_section.get(path_key)
        else:
            # Fallback to generic pattern if specific path not configured
            output_dir = config_path.parent / f"../data/db_extracted_tables/{db_name}/"
        output_paths[db_name] = output_dir.resolve()

    # Parse optional extraction settings (with defaults)
    extraction_section = (
        parser["extraction"] if parser.has_section("extraction") else {}
    )
    verification_section = (
        parser["verification"] if parser.has_section("verification") else {}
    )

    return Config(
        host=pg_section.get("host"),
        port=pg_section.get("port"),
        user=pg_section.get("user"),
        password=pg_section.get("password"),
        root_db=pg_section.get("root_db"),
        legacy_dbs=legacy_dbs,
        output_paths=output_paths,
        chunk_size=int(extraction_section.get("chunk_size", DEFAULT_CHUNK_SIZE))
        if extraction_section
        else DEFAULT_CHUNK_SIZE,
        encoding=extraction_section.get("encoding", DEFAULT_ENCODING)
        if extraction_section
        else DEFAULT_ENCODING,
        csv_delimiter=extraction_section.get("csv_delimiter", DEFAULT_CSV_DELIMITER)
        if extraction_section
        else DEFAULT_CSV_DELIMITER,
        include_headers=extraction_section.getboolean("include_headers", True)
        if extraction_section
        else True,
        overwrite_existing=extraction_section.getboolean("overwrite_existing", False)
        if extraction_section
        else False,
        verify_row_counts=verification_section.getboolean("verify_row_counts", True)
        if verification_section
        else True,
        verify_file_creation=verification_section.getboolean(
            "verify_file_creation", True
        )
        if verification_section
        else True,
    )


# ---------------------------------------------------------------------------
# Directory Management
# ---------------------------------------------------------------------------


def ensure_output_directories(cfg: Config) -> None:
    """Create all output directories if they don't exist.

    Args:
        cfg: Configuration object containing output paths.

    Raises:
        OSError: If directory creation fails.
    """
    for db_name, output_path in cfg.output_paths.items():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logging.info("Ensured output directory exists: %s", output_path)
        except OSError as e:
            raise OSError(
                f"Failed to create output directory for {db_name}: {e}"
            ) from e


def validate_output_paths(cfg: Config) -> None:
    """Verify all output paths are writable.

    Args:
        cfg: Configuration object containing output paths.

    Raises:
        PermissionError: If any output path is not writable.
    """
    for _db_name, output_path in cfg.output_paths.items():
        if not output_path.exists():
            raise FileNotFoundError(f"Output directory does not exist: {output_path}")

        # Test writability by creating and removing a temporary file
        test_file = output_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logging.debug("Verified write access to: %s", output_path)
        except (PermissionError, OSError) as e:
            raise PermissionError(f"No write access to {output_path}: {e}") from e


# ---------------------------------------------------------------------------
# Database Connection & Operations
# ---------------------------------------------------------------------------


def get_engine(cfg: Config, db_name: str) -> Engine:
    """Return a new SQLAlchemy engine for the specified database.

    Args:
        cfg: Configuration object with connection parameters.
        db_name: Name of the database to connect to.

    Returns:
        SQLAlchemy engine configured for the specified database.

    Raises:
        SQLAlchemyError: If engine creation fails.
    """
    _validate_identifier(db_name)
    conn_str = (
        f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
        f"{cfg.host}:{cfg.port}/{db_name}"
    )
    try:
        engine = create_engine(conn_str)
        return engine
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Failed to create engine for {db_name}: {e}") from e


def validate_database_accessible(engine: Engine, db_name: str) -> bool:
    """Verify that a database exists and is accessible.

    Args:
        engine: SQLAlchemy engine for the database.
        db_name: Name of the database to verify.

    Returns:
        True if database is accessible, False otherwise.
    """
    try:
        with engine.connect() as conn:
            # Simple query to verify connection and access
            result = conn.execute(text("SELECT 1 AS test"))
            success = result.scalar() == 1
            if success:
                logging.info("Successfully verified access to database: %s", db_name)
            else:
                logging.warning("Database connection test failed for: %s", db_name)
            return success
    except SQLAlchemyError as e:
        logging.error("Failed to access database %s: %s", db_name, e)
        return False


def discover_tables(engine: Engine, db_name: str) -> List[str]:
    """Discover all user tables in the specified database.

    Args:
        engine: SQLAlchemy engine connected to the target database.
        db_name: Name of the database being queried.

    Returns:
        List of table names found in the database.

    Raises:
        TableExtractionError: If table discovery fails.
    """
    try:
        # Map database name to its corresponding schema name
        schema_name = db_name.lower().replace("_", "_")  # Convert TMP_DF8 -> tmp_df8

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = :schema_name
                    ORDER BY tablename
                """),
                {"schema_name": schema_name},
            )
            tables = [row[0] for row in result]
            logging.info(
                "Discovered %d tables in schema '%s' of database %s",
                len(tables),
                schema_name,
                db_name,
            )
            return tables
    except SQLAlchemyError as e:
        raise TableExtractionError(
            f"Failed to discover tables in {db_name}: {e}"
        ) from e


# ---------------------------------------------------------------------------
# Table Extraction Logic
# ---------------------------------------------------------------------------


def extract_table_to_csv(
    engine: Engine, table_name: str, db_name: str, output_path: Path, cfg: Config
) -> bool:
    """Extract a single table to CSV file with chunked processing.

    Args:
        engine: SQLAlchemy engine for database connection.
        table_name: Name of the table to extract.
        db_name: Name of the database (used to determine schema).
        output_path: Path where CSV file will be written.
        cfg: Configuration object with extraction settings.

    Returns:
        True if extraction successful, False otherwise.

    Raises:
        TableExtractionError: If extraction fails critically.
    """
    csv_file_path = output_path / f"{table_name}.csv"

    # Check if file exists and handle overwrite policy
    if csv_file_path.exists() and not cfg.overwrite_existing:
        # For enhanced idempotency, verify existing file integrity
        if cfg.verify_row_counts:
            try:
                # Quick integrity check: verify row count matches database
                with engine.connect() as conn:
                    db_count = conn.execute(
                        text(f'SELECT COUNT(*) FROM "{table_name}"')
                    ).scalar()

                # Count CSV rows (excluding header if present)
                csv_count = sum(
                    1 for _ in open(csv_file_path, "r", encoding=cfg.encoding)
                )
                if cfg.include_headers:
                    csv_count -= 1

                if db_count == csv_count:
                    logging.info(
                        "CSV file already exists with correct row count, skipping: %s",
                        csv_file_path,
                    )
                    return True
                else:
                    logging.warning(
                        "Existing CSV file has mismatched row count (DB=%d, CSV=%d), re-extracting: %s",
                        db_count,
                        csv_count,
                        csv_file_path,
                    )
                    # Continue to re-extract
            except Exception as e:
                logging.warning(
                    "Could not verify existing CSV file integrity, re-extracting: %s (Error: %s)",
                    csv_file_path,
                    e,
                )
                # Continue to re-extract
        else:
            logging.info("CSV file already exists, skipping: %s", csv_file_path)
            return True

    try:
        # Map database name to its corresponding schema name
        schema_name = db_name.lower().replace("_", "_")  # Convert TMP_DF8 -> tmp_df8
        qualified_table_name = f'"{schema_name}"."{table_name}"'

        logging.info(
            "Extracting table '%s' from schema '%s' to CSV...", table_name, schema_name
        )

        # Get row count for progress tracking
        with engine.connect() as conn:
            count_result = conn.execute(
                text(f"SELECT COUNT(*) FROM {qualified_table_name}")
            )
            total_rows = count_result.scalar()
            logging.info(
                "Table '%s' contains %d rows", qualified_table_name, total_rows
            )

        # Extract data using pandas with chunking for memory efficiency
        rows_written = 0
        first_chunk = True

        # Use pandas read_sql with chunksize for memory-efficient processing
        chunk_iter = pd.read_sql_table(
            table_name, engine, schema=schema_name, chunksize=cfg.chunk_size
        )

        for chunk_df in chunk_iter:
            # Write chunk to CSV
            chunk_df.to_csv(
                csv_file_path,
                mode="w" if first_chunk else "a",
                header=cfg.include_headers and first_chunk,
                index=False,
                encoding=cfg.encoding,
                sep=cfg.csv_delimiter,
            )

            rows_written += len(chunk_df)
            first_chunk = False

            # Progress logging for large tables
            if rows_written % (cfg.chunk_size * 10) == 0:
                logging.info(
                    "Progress: %d/%d rows written for table '%s'",
                    rows_written,
                    total_rows,
                    table_name,
                )

        logging.info(
            "Successfully extracted table '%s': %d rows to %s",
            table_name,
            rows_written,
            csv_file_path,
        )

        # Verify row count if enabled
        if cfg.verify_row_counts and rows_written != total_rows:
            logging.warning(
                "Row count mismatch for table '%s': DB=%d, CSV=%d",
                table_name,
                total_rows,
                rows_written,
            )
            return False

        return True

    except Exception as e:
        logging.error("Failed to extract table '%s': %s", table_name, e)
        # Clean up partial file on failure
        if csv_file_path.exists():
            try:
                csv_file_path.unlink()
                logging.info("Cleaned up partial CSV file: %s", csv_file_path)
            except OSError:
                logging.warning(
                    "Failed to clean up partial CSV file: %s", csv_file_path
                )
        return False


def extract_database_tables(cfg: Config, db_name: str) -> Tuple[int, int]:
    """Extract all tables from a single database to CSV files.

    Args:
        cfg: Configuration object.
        db_name: Name of the database to extract.

    Returns:
        Tuple of (successful_extractions, total_tables).
    """
    logging.info("Starting extraction for database: %s", db_name)

    try:
        # Get database engine and validate access
        engine = get_engine(cfg, db_name)

        if not validate_database_accessible(engine, db_name):
            logging.error("Cannot access database: %s", db_name)
            return (0, 0)

        # Discover all tables in the database
        tables = discover_tables(engine, db_name)
        if not tables:
            logging.warning("No tables found in database: %s", db_name)
            return (0, 0)

        # Get output directory for this database
        output_path = cfg.output_paths[db_name]

        # Extract each table
        successful_extractions = 0
        for table_name in tables:
            try:
                if extract_table_to_csv(engine, table_name, db_name, output_path, cfg):
                    successful_extractions += 1
                else:
                    logging.error("Failed to extract table: %s.%s", db_name, table_name)
            except Exception as e:
                logging.error(
                    "Error extracting table %s.%s: %s", db_name, table_name, e
                )

        logging.info(
            "Database %s extraction complete: %d/%d tables successful",
            db_name,
            successful_extractions,
            len(tables),
        )

        # Clean up engine
        engine.dispose()

        return (successful_extractions, len(tables))

    except Exception as e:
        logging.error("Failed to extract database %s: %s", db_name, e)
        return (0, 0)


# ---------------------------------------------------------------------------
# Multi-Database Orchestration
# ---------------------------------------------------------------------------


def extract_all_databases(cfg: Config) -> Dict[str, Tuple[int, int]]:
    """Extract tables from all configured legacy databases.

    Args:
        cfg: Configuration object with database list and settings.

    Returns:
        Dictionary mapping database names to (successful, total) extraction counts.
    """
    logging.info(
        "Starting extraction for %d databases: %s",
        len(cfg.legacy_dbs),
        ", ".join(cfg.legacy_dbs),
    )

    results = {}

    for db_name in cfg.legacy_dbs:
        try:
            logging.info("=" * 60)
            logging.info("Processing database: %s", db_name)
            logging.info("=" * 60)

            success_count, total_count = extract_database_tables(cfg, db_name)
            results[db_name] = (success_count, total_count)

            if success_count == total_count and total_count > 0:
                logging.info(
                    "[SUCCESS] Database %s: ALL tables extracted (%d/%d)",
                    db_name,
                    success_count,
                    total_count,
                )
            elif success_count > 0:
                logging.warning(
                    "[PARTIAL] Database %s: PARTIAL extraction (%d/%d tables)",
                    db_name,
                    success_count,
                    total_count,
                )
            else:
                logging.error(
                    "[FAILED] Database %s: NO tables extracted (%d total)",
                    db_name,
                    total_count,
                )

        except Exception as e:
            logging.error("Critical error processing database %s: %s", db_name, e)
            results[db_name] = (0, 0)

    return results


# ---------------------------------------------------------------------------
# Verification & Reporting
# ---------------------------------------------------------------------------


def verify_extraction_results(cfg: Config, results: Dict[str, Tuple[int, int]]) -> None:
    """Verify extraction results and generate summary report.

    Args:
        cfg: Configuration object.
        results: Dictionary of database extraction results.
    """
    logging.info("=" * 60)
    logging.info("EXTRACTION VERIFICATION & SUMMARY")
    logging.info("=" * 60)

    total_databases = len(results)
    total_tables_expected = sum(total for _, total in results.values())
    total_tables_extracted = sum(success for success, _ in results.values())

    # Verify file creation if enabled
    if cfg.verify_file_creation:
        logging.info("Verifying CSV file creation...")

        for db_name, (success_count, _total_count) in results.items():
            output_path = cfg.output_paths[db_name]
            csv_files = list(output_path.glob("*.csv"))

            if len(csv_files) != success_count:
                logging.warning(
                    "File count mismatch for %s: expected %d, found %d CSV files",
                    db_name,
                    success_count,
                    len(csv_files),
                )
            else:
                logging.info(
                    "File verification passed for %s: %d CSV files",
                    db_name,
                    len(csv_files),
                )

    # Generate summary statistics
    success_rate = (
        (total_tables_extracted / total_tables_expected * 100)
        if total_tables_expected > 0
        else 0
    )

    logging.info("EXTRACTION SUMMARY:")
    logging.info("  • Databases processed: %d", total_databases)
    logging.info("  • Total tables expected: %d", total_tables_expected)
    logging.info("  • Total tables extracted: %d", total_tables_extracted)
    logging.info("  • Overall success rate: %.1f%%", success_rate)

    # Per-database summary
    logging.info("PER-DATABASE RESULTS:")
    for db_name, (success_count, total_count) in results.items():
        db_success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        status = (
            "[OK]"
            if success_count == total_count
            else "[PARTIAL]"
            if success_count > 0
            else "[FAILED]"
        )
        logging.info(
            "  %s %s: %d/%d tables (%.1f%%)",
            status,
            db_name,
            success_count,
            total_count,
            db_success_rate,
        )


# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate the complete table extraction process.

    This function coordinates all aspects of the ETL process:
    1. Parse command-line arguments
    2. Load and validate configuration
    3. Set up logging and directories
    4. Extract tables from all databases
    5. Verify results and generate reports
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Set up logging (before any other operations)
        log_path = args.config.parent / LOG_FILE_NAME
        setup_logging(log_path)

        logging.info("=" * 60)
        logging.info("TMP DATABASE TABLE EXTRACTION STARTED")
        logging.info("=" * 60)
        logging.info("Script: %s", __file__)
        logging.info("Config: %s", args.config)
        logging.info("Dry run: %s", args.dry_run)

        # Load and validate configuration
        logging.info("Loading configuration...")
        cfg = load_config(args.config)
        logging.info("Configuration loaded successfully")
        logging.info("Databases to process: %s", ", ".join(cfg.legacy_dbs))

        # Ensure output directories exist and are writable
        logging.info("Preparing output directories...")
        ensure_output_directories(cfg)
        validate_output_paths(cfg)

        # Show configuration summary
        logging.info("EXTRACTION SETTINGS:")
        logging.info("  • Chunk size: %d rows", cfg.chunk_size)
        logging.info("  • Encoding: %s", cfg.encoding)
        logging.info("  • CSV delimiter: '%s'", cfg.csv_delimiter)
        logging.info("  • Include headers: %s", cfg.include_headers)
        logging.info("  • Overwrite existing: %s", cfg.overwrite_existing)
        logging.info("  • Verify row counts: %s", cfg.verify_row_counts)

        if args.dry_run:
            logging.info("DRY RUN MODE - No actual extraction will be performed")
            logging.info(
                "Would extract tables from databases: %s", ", ".join(cfg.legacy_dbs)
            )
            for db_name, output_path in cfg.output_paths.items():
                logging.info("  %s → %s", db_name, output_path)
            return

        # Perform the extraction
        logging.info("Starting table extraction process...")
        results = extract_all_databases(cfg)

        # Verify results and generate summary
        verify_extraction_results(cfg, results)

        # Determine overall success
        total_expected = sum(total for _, total in results.values())
        total_success = sum(success for success, _ in results.values())

        if total_success == total_expected and total_expected > 0:
            logging.info("[SUCCESS] EXTRACTION COMPLETED SUCCESSFULLY")
            logging.info(
                "All %d tables extracted from %d databases",
                total_expected,
                len(cfg.legacy_dbs),
            )
        elif total_success > 0:
            logging.warning("[PARTIAL] EXTRACTION PARTIALLY COMPLETED")
            logging.warning(
                "Extracted %d/%d tables from %d databases",
                total_success,
                total_expected,
                len(cfg.legacy_dbs),
            )
        else:
            logging.error("[FAILED] EXTRACTION FAILED")
            logging.error("No tables were successfully extracted")
            sys.exit(1)

    except ConfigurationError as e:
        logging.error("Configuration error: %s", e)
        sys.exit(1)
    except Exception as e:
        logging.error("Critical error during extraction: %s", e)
        logging.exception("Full traceback:")
        sys.exit(1)
    finally:
        logging.info("=" * 60)
        logging.info("TMP DATABASE TABLE EXTRACTION FINISHED")
        logging.info("=" * 60)


# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    """Return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract all tables from legacy TMP databases to CSV files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default="config.ini",
        help="Path to the configuration file (default: config.ini)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without actually performing extraction",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Run main extraction process
    try:
        main()
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
