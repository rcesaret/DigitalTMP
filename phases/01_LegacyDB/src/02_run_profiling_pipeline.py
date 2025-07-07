# -*- coding: utf-8 -*-
"""
Orchestrates the full database profiling pipeline for Digital TMP Phase 1.

This script serves as the main engine for data gathering. It iterates
through all specified legacy and benchmark databases, connects to each one,
and executes the full suite of profiling functions defined in the
`profiling_modules` package.

The output of each profiling function is saved as a separate, structured
data file (.csv or .json) in the `outputs/metrics/` directory.
Filenames are generated systematically to ensure clarity and organization.

The pipeline is designed for robustness:
- A failure to connect or process a single database will be logged, and the
  script will proceed to the next database.
- A failure of a single metric-gathering function will be logged, and the
  script will continue to the next metric for that database.

Usage:
    From the src/ directory, run:
    $ python 02_run_profiling_pipeline.py --config config.ini

"""

import argparse
import configparser
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd

# Import all our profiling functions
from profiling_modules import (
    metrics_basic,
    metrics_interop,
    metrics_performance,
    metrics_profile,
    metrics_schema,
)
from sqlalchemy import create_engine

# --- Constants ---
LOG_FILE_NAME = "02_run_profiling_pipeline.log"
OUTPUT_METRICS_DIR = "outputs/metrics"


# --- Setup Functions ---


def setup_logging(log_dir: Path) -> None:
    """Configures logging to both console and a file."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the full database profiling pipeline for Digital TMP."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the configuration file (e.g., config.ini).",
    )
    return parser.parse_args()


def get_db_connection_string(config: configparser.ConfigParser) -> str:
    """Constructs the database connection string from the config file."""
    db_config = config["postgresql"]
    return (
        f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/"
    )


def get_db_list(config: configparser.ConfigParser) -> List[str]:
    """Retrieves the list of databases to profile from the config file."""
    legacy_dbs = config.get("databases", "legacy_dbs").split(",")
    benchmark_dbs = config.get("databases", "benchmark_dbs").split(",")
    return [db.strip() for db in legacy_dbs + benchmark_dbs]


def save_results(
    data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]],
    db_name: str,
    metric_name: str,
    output_dir: Path,
) -> None:
    """Saves profiling data to a CSV or JSON file."""
    if data is None:
        logging.warning(
            "No data returned for metric '%s' on db '%s'.",
            metric_name,
            db_name,
        )
        return

    if isinstance(data, list):
        if not data:
            logging.warning(
                "Empty list for metric '%s' on db '%s'. Nothing to save.",
                metric_name,
                db_name,
            )
            return
        file_path = output_dir / f"{db_name}_{metric_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logging.info("Saved '%s' results to %s", metric_name, file_path.name)
    elif isinstance(data, pd.DataFrame):
        if data.empty:
            logging.warning(
                "Empty DataFrame for metric '%s' on db '%s'. Nothing to save.",
                metric_name,
                db_name,
            )
            return
        file_path = output_dir / f"{db_name}_{metric_name}.csv"
        data.to_csv(file_path, index=False)
        logging.info("Saved '%s' results to %s", metric_name, file_path.name)
    elif isinstance(data, dict):
        file_path = output_dir / f"{db_name}_{metric_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logging.info("Saved '%s' results to %s", metric_name, file_path.name)
    else:
        logging.error("Unsupported data type for saving: %s", type(data))


def main() -> None:
    """Main function to orchestrate the profiling pipeline."""
    args = parse_arguments()
    config_path = Path(args.config).resolve()

    if not config_path.is_file():
        print(f"FATAL: Configuration file not found at '{config_path}'")
        sys.exit(1)

    # Resolve paths relative to the config file's location. This assumes
    # a fixed project structure where the config file is located at:
    # <project_root>/phases/01_LegacyDB/src/config.ini
    project_root = config_path.parent.parent.parent.parent
    log_dir = project_root / "logs"
    output_dir = project_root / OUTPUT_METRICS_DIR
    # The SQL directory is inside the phase directory, not the project root.
    sql_queries_dir = config_path.parent.parent / "sql"

    setup_logging(log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()
    config.read(config_path)

    base_conn_str = get_db_connection_string(config)
    databases_to_profile = get_db_list(config)
    legacy_db_names = [
        db.strip() for db in config.get("databases", "legacy_dbs").split(",")
    ]

    logging.info("--- Starting Database Profiling Pipeline ---")
    logging.info("Found %d databases to profile.", len(databases_to_profile))
    logging.info("Output directory is: %s", output_dir)
    logging.info("=" * 80)

    for i, db_name in enumerate(databases_to_profile):
        logging.info(
            "Processing Database %d/%d: %s",
            i + 1,
            len(databases_to_profile),
            db_name,
        )
        logging.info("=" * 80)

        try:
            engine = create_engine(f"{base_conn_str}{db_name}")
            with engine.connect():
                logging.info("Successfully connected to database: %s", db_name)
        except Exception as e:
            logging.error(
                "Could not connect to database '%s'. Skipping. Error: %s",
                db_name,
                e,
            )
            continue

        # Determine the correct schema name for this database.
        # Legacy DBs use a schema matching their name (lowercased).
        # Benchmark DBs use the 'public' schema.
        if db_name in legacy_db_names:
            schema_name = db_name.lower()
        else:
            schema_name = "public"
        logging.info("Target schema for '%s' is '%s'.", db_name, schema_name)

        # --- Basic DB Metrics ---
        try:
            logging.info("--> Running: Basic DB Metrics")
            basic_info = metrics_basic.get_basic_db_metrics(engine)
            save_results(basic_info, db_name, "basic_metrics", output_dir)
            logging.info("Retrieved basic metrics for DB '%s'.", db_name)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Basic DB Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        # --- Schema Object Counts ---
        try:
            logging.info("--> Running: Schema Object Counts")
            schema_counts = metrics_basic.get_schema_object_counts(engine, schema_name)
            save_results(schema_counts, db_name, "schema_counts", output_dir)
            logging.info("Counted objects for schema '%s'.", schema_name)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Schema Object Counts for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        # --- Table Level Metrics ---
        try:
            logging.info("--> Running: Table Level Metrics")
            table_metrics = metrics_schema.get_table_level_metrics(engine, schema_name)
            save_results(table_metrics, db_name, "table_metrics", output_dir)
            if table_metrics:
                logging.info(
                    "Calculated table-level metrics for %d tables in '%s'.",
                    len(table_metrics),
                    schema_name,
                )
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Table Level Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        # --- Column Structural Metrics ---
        try:
            logging.info("--> Running: Column Structural Metrics")
            column_structure = metrics_schema.get_column_structural_metrics(
                engine, schema_name
            )
            save_results(column_structure, db_name, "column_structure", output_dir)
            if column_structure:
                logging.info(
                    "Retrieved structural metrics for %d columns in '%s'.",
                    len(column_structure),
                    schema_name,
                )
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Column Structural Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        # --- Column Data Profiles (pg_stats) ---
        try:
            logging.info("--> Running: Column Data Profiles (pg_stats)")
            logging.warning(
                "Initiating full column profile. This is a slow operation "
                "that queries each column individually."
            )
            column_profiles = metrics_profile.get_all_column_profiles(
                engine, schema_name
            )
            save_results(column_profiles, db_name, "column_profiles", output_dir)
        except Exception as e:
            logging.error(
                "Failed to get column profiles for schema '%s': %s",
                schema_name,
                e,
            )

        # --- Interoperability Metrics ---
        try:
            # This metric only applies to schemas with more than one table.
            if db_name in legacy_db_names:
                logging.info("--> Running: Interoperability Metrics")
                interop_metrics = metrics_interop.calculate_interoperability_metrics(
                    engine, schema_name
                )
                save_results(interop_metrics, db_name, "interop_metrics", output_dir)
            else:
                logging.info(
                    "--> Skipping: Interoperability Metrics "
                    "(not applicable to single-table schema)."
                )
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Interoperability Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        # --- Performance Benchmarks ---
        # This metric is optional and depends on a query file being defined.
        logging.info("--> Running: Performance Benchmarks")
        # Check config for a specific query file for the current database.
        if config.has_section("database_query_files"):
            query_file_map = dict(config.items("database_query_files"))
            query_file_name = query_file_map.get(db_name.lower()) or query_file_map.get(
                db_name.upper()
            )
            logging.info(
                "Found query file mapping for '%s': %s",
                db_name,
                query_file_name,
            )
        else:
            query_file_name = None

        if query_file_name:
            # Construct the path to the query file
            query_file_path = sql_queries_dir / "canonical_queries" / query_file_name

            # Log the complete path for debugging
            logging.info("Looking for query file at: %s", query_file_path)

            if not query_file_path.is_file():
                logging.error(
                    "Query file not found for '%s': %s",
                    db_name,
                    query_file_path,
                )
            else:
                try:
                    # Run the performance benchmarks
                    perf_benchmarks = metrics_performance.run_performance_benchmarks(
                        engine, db_name, schema_name, query_file_path
                    )
                    save_results(
                        perf_benchmarks,
                        db_name,
                        "performance_benchmarks",
                        output_dir,
                    )
                except Exception as e:
                    logging.error(
                        "CRITICAL ERROR in Performance Benchmarks for " "'%s': %s",
                        db_name,
                        e,
                        exc_info=True,
                    )
        else:
            logging.info(
                "--> Skipping: Performance Benchmarks for '%s' "
                "(no query file specified).",
                db_name,
            )

        logging.info("--- Finished processing %s ---", db_name)

    logging.info("=" * 80)
    logging.info("--- Database Profiling Pipeline Finished ---")


if __name__ == "__main__":
    main()
