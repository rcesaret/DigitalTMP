# -*- coding: utf-8 -*-
"""
Orchestrates the full database profiling pipeline for Digital TMP Phase 1.

This script serves as the main engine for data gathering. It iterates through
all specified legacy and benchmark databases, connects to each one, and executes
the full suite of profiling functions defined in the `profiling_modules` package.

The output of each profiling function is saved as a separate, structured
data file (.csv or .json) in the `outputs/metrics/` directory. Filenames are
generated systematically to ensure clarity and organization.

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
from typing import Any, Dict, List

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
from sqlalchemy.engine import Engine

# --- Constants ---
LOG_FILE_NAME = "02_run_profiling_pipeline.log"
OUTPUT_METRICS_DIR = "outputs/metrics"


# --- Setup Functions ---


def setup_logging(log_dir: Path) -> None:
    """Configures logging to both console and a file."""
    log_dir.mkdir(exist_ok=True)
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
        description="Run the full database profiling pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.ini",
        help="Path to the configuration file (default: config.ini)",
    )
    return parser.parse_args()


def get_sqlalchemy_engine(db_config: Dict[str, Any], db_name: str) -> Engine | None:
    """Creates a SQLAlchemy engine, returning None on failure."""
    try:
        db_url = (
            f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_name}"
        )
        return create_engine(db_url)
    except Exception as e:
        logging.error(
            "Failed to create SQLAlchemy engine for '%s': %s",
            db_name,
            e,
        )
        return None


def save_results(
    data: List[Dict[str, Any]] | Dict[str, Any],
    db_name: str,
    metric_name: str,
    output_dir: Path,
) -> None:
    """Saves profiling data to a CSV or JSON file."""
    if not data:
        logging.warning(
            "No data to save for metric '%s' on db '%s'.",
            metric_name,
            db_name,
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path_base = output_dir / f"{db_name}_{metric_name}"

    try:
        if isinstance(data, dict):
            # Save single dictionary as JSON
            output_path = file_path_base.with_suffix(".json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        elif isinstance(data, list):
            # Save list of dictionaries as CSV
            output_path = file_path_base.with_suffix(".csv")
            pd.DataFrame(data).to_csv(output_path, index=False)
        else:
            logging.error("Unsupported data type for saving: %s", type(data))
            return

        logging.info(
            "Successfully saved '%s' results to %s",
            metric_name,
            output_path.name,
        )
    except Exception as e:
        logging.error(
            "Failed to save results for metric '%s': %s",
            metric_name,
            e,
        )


# --- Main Orchestrator ---


def main() -> None:
    """Main function to orchestrate the entire profiling pipeline."""
    args = parse_arguments()
    config_path = Path(args.config)

    # Assume log directory is relative to script location
    log_dir = Path(__file__).parent
    setup_logging(log_dir)

    logging.info("--- Starting Database Profiling Pipeline ---")

    logging.info("Reading configuration from: %s", config_path)
    if not config_path.is_file():
        logging.critical("Configuration file not found: %s", config_path)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        db_config_root = dict(config["postgresql"])
        legacy_dbs = [
            db.strip() for db in config.get("databases", "legacy_dbs").split(",")
        ]
        benchmark_dbs = [
            db.strip() for db in config.get("databases", "benchmark_dbs").split(",")
        ]
        all_dbs_to_profile = legacy_dbs + benchmark_dbs

        # Define paths relative to the config file location
        config_dir = config_path.parent
        output_dir = config_dir / config.get("paths", "output_metrics")
        sql_queries_dir = config_dir / config.get("paths", "sql_queries_dir")

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.critical(
            "Config file is missing a required section or option: %s",
            e,
        )
        sys.exit(1)

    for i, db_name in enumerate(all_dbs_to_profile, 1):
        logging.info("=" * 80)
        logging.info(
            "Processing Database %s/%s: %s",
            i,
            len(all_dbs_to_profile),
            db_name,
        )
        logging.info("=" * 80)

        engine = get_sqlalchemy_engine(db_config_root, db_name)
        if not engine:
            logging.error("Skipping database '%s' due to connection failure.", db_name)
            continue

        # Determine schema name. For legacy DBs, use lowercase schema name for
        # reflection. For benchmark DBs, all tables reside in the 'public' schema.
        if db_name in legacy_dbs:
            schema_name = db_name.lower()
        else:
            schema_name = "public"
        logging.info(
            "Target schema for '%s' is '%s'.",
            db_name,
            schema_name,
        )

        # --- Execute Profiling Modules ---

        try:
            logging.info("--> Running: Basic DB Metrics")
            basic_metrics = metrics_basic.get_basic_db_metrics(engine)
            save_results(basic_metrics, db_name, "basic_metrics", output_dir)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Basic DB Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        try:
            logging.info("--> Running: Schema Object Counts")
            schema_counts = metrics_basic.get_schema_object_counts(engine, schema_name)
            save_results(schema_counts, db_name, "schema_counts", output_dir)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Schema Object Counts for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        try:
            logging.info("--> Running: Table Level Metrics")
            table_metrics = metrics_schema.get_table_level_metrics(engine, schema_name)
            save_results(table_metrics, db_name, "table_metrics", output_dir)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Table Level Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        try:
            logging.info("--> Running: Column Structural Metrics")
            column_structure = metrics_schema.get_column_structural_metrics(
                engine, schema_name
            )
            save_results(column_structure, db_name, "column_structure", output_dir)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Column Structural Metrics for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        try:
            logging.info("--> Running: Column Data Profiles (pg_stats)")
            column_profiles = metrics_profile.get_all_column_profiles(
                engine, schema_name
            )
            save_results(column_profiles, db_name, "column_profiles", output_dir)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Column Data Profiles for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        try:
            # Interoperability metrics only make sense for schemas with multiple tables
            if schema_name != "public":
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

        try:
            logging.info("--> Running: Performance Benchmarks")
            perf_benchmarks = metrics_performance.run_performance_benchmarks(
                engine,
                db_name,
                schema_name,
                sql_queries_dir / "canonical_queries",  # Point to queries directory
            )
            save_results(perf_benchmarks, db_name, "performance_benchmarks", output_dir)
        except Exception as e:
            logging.error(
                "CRITICAL ERROR in Performance Benchmarks for '%s': %s",
                db_name,
                e,
                exc_info=True,
            )

        logging.info("--- Finished processing %s ---", db_name)

    logging.info("=" * 80)
    logging.info("--- Database Profiling Pipeline Finished ---")


if __name__ == "__main__":
    main()
