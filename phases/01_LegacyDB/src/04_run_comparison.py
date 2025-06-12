# -*- coding: utf-8 -*-
"""
Aggregates and compares results from the database profiling pipeline.

This script acts as the final synthesizer for the data-gathering phase. It does
not connect to any databases. Instead, it performs the following steps:
1.  Discovers and loads all raw metric files (.csv, .json) from the
    `outputs/metrics/` directory.
2.  Calculates high-level summary metrics for each database.
3.  Calculates advanced comparative performance metrics across all databases.
4.  Generates multiple outputs in the `outputs/reports/` directory:
    a) `comparison_matrix.csv`: A wide-format, machine-readable summary.
    b) `comparison_report.md`: A formatted, human-readable summary.
    c) `report_performance_summary_detailed.csv`: A detailed, long-format
       performance report with calculated efficiency and improvement factors.
    d) `report_performance_pivot_efficiency.csv`: A pivot table for at-a-glance
       comparison of schema efficiency.
"""
import argparse
import configparser
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# --- Constants ---
LOG_FILE_NAME = "04_run_comparison.log"
INPUT_METRICS_DIR = "outputs/metrics"
OUTPUT_REPORTS_DIR = "outputs/reports"


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
        description="Aggregate and compare database profiling results."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.ini",
        help="Path to the configuration file (default: config.ini)",
    )
    return parser.parse_args()


# --- Core Logic ---
def load_all_metrics(input_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
     Discovers and loads all metric files from the input directory.
    Filenames are parsed from the right to strip the metric suffix
    (e.g., ``_basic_metrics``) and treat the remaining prefix as the
    database name.

    Args:
        input_dir: The path to the directory containing metric files.

    Returns:
        A nested dictionary mapping: db_name -> metric_name -> data,
        where data is a DataFrame (for CSVs) or a dict (for JSONs).
    """
    logging.info("Scanning for metric files in: %s", input_dir)
    all_data = defaultdict(dict)

    if not input_dir.is_dir():
        logging.error("Input metrics directory not found: %s", input_dir)
        return {}

    metric_files = list(input_dir.glob("*.csv")) + list(input_dir.glob("*.json"))
    logging.info("Found %s metric files to process.", len(metric_files))

    metric_suffixes = [
        "basic_metrics",
        "schema_counts",
        "table_metrics",
        "column_structure",
        "column_profiles",
        "interop_metrics",
        "performance_benchmarks",
    ]
    metric_suffixes.sort(key=len, reverse=True)

    for file_path in metric_files:
        try:
            stem = file_path.stem
            metric_name, db_name = None, None
            for suffix in metric_suffixes:
                if stem.endswith(f"_{suffix}"):
                    metric_name = suffix
                    db_name = stem.rsplit(f"_{suffix}", 1)[0]
                    break

            if not db_name:
                logging.warning(
                    f"Could not determine database name for '{file_path.name}'. Skipping."
                )
                continue

            if file_path.suffix == ".csv":
                all_data[db_name][metric_name] = pd.read_csv(file_path)
            elif file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    all_data[db_name][metric_name] = json.load(f)
        except Exception as e:
            logging.exception(f"Failed to load or parse file '{file_path.name}': {e}")

    return dict(all_data)


def calculate_summary_metrics(db_name: str, db_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    This function calculates a flat dictionary of key summary metrics for a single database.

    Args:
        db_name: The name of the database being summarized.
        db_data: The dictionary of all loaded data for that database.

    Returns:
        A flat dictionary of aggregated metrics.

    This preserves the original summary logic.
    """
    summary = {"Database": db_name}

    # Helper to safely get data and log if missing
    def get_metric_data(key, default=None):
        data = db_data.get(key)
        if data is None:
            logging.warning(f"Metric data '{key}' not found for database '{db_name}'.")
        return data if data is not None else default

    # --- Basic Metrics ---
    basic_metrics = get_metric_data("basic_metrics", {})
    summary["Database Size (MB)"] = basic_metrics.get("database_size_mb")

    # --- Schema Counts ---
    schema_counts = get_metric_data("schema_counts", {})
    summary["Table Count"] = schema_counts.get("table_count")
    summary["View Count"] = schema_counts.get("view_count")

    # --- Table-level Aggregations ---
    table_metrics_df = get_metric_data("table_metrics")
    if table_metrics_df is not None and not table_metrics_df.empty:
        summary["Total Estimated Rows"] = int(table_metrics_df["row_estimate"].sum())
        summary["Total Index Count"] = int(table_metrics_df["index_count"].sum())

    # --- Interoperability Metrics ---
    interop_metrics = get_metric_data("interop_metrics", {})
    summary["JDI (Join Dependency Index)"] = interop_metrics.get("jdi")
    summary["LIF (Logical Interop. Factor)"] = interop_metrics.get("lif")
    summary["NF (Normalization Factor)"] = interop_metrics.get("nf")

    return summary


def calculate_comparative_performance_metrics(
    all_data: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """
    Calculates advanced, comparative performance metrics using the new architecture.
    """
    logging.info("Calculating advanced comparative performance metrics...")
    perf_data = []
    for db_name, db_metrics in all_data.items():
        if "performance_benchmarks" in db_metrics:
            df = db_metrics["performance_benchmarks"].copy()
            df["database"] = db_name
            perf_data.append(df)

    if not perf_data:
        logging.warning("No performance benchmark data found to compare.")
        return pd.DataFrame()

    df = pd.concat(perf_data, ignore_index=True)
    if df.empty or "status" not in df.columns or df[df["status"] == "Success"].empty:
        logging.warning(
            "Performance DataFrame is empty or contains no successful queries."
        )
        return pd.DataFrame()

    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
    df_success = df[df["status"] == "Success"].copy()

    denormalized_dbs = [
        db for db in df_success["database"].unique() if "benchmark" in db
    ]
    if not denormalized_dbs:
        logging.error("No benchmark/denormalized databases found for comparison base.")
        return df

    baseline_latency = (
        df_success[df_success["database"].isin(denormalized_dbs)]
        .groupby("query_id")["latency_ms"]
        .min()
        .rename("baseline_latency_ms")
    )

    df_success = pd.merge(df_success, baseline_latency, on="query_id", how="left")

    df_success["schema_efficiency_factor"] = (
        df_success["latency_ms"] / df_success["baseline_latency_ms"]
    ).round(2)
    df_success["performance_improvement_factor"] = (
        (
            (df_success["latency_ms"] - df_success["baseline_latency_ms"])
            / df_success["latency_ms"]
        )
        * 100
    ).round(2)
    df_success.loc[
        df_success["database"].isin(denormalized_dbs), "performance_improvement_factor"
    ] = 0.0

    logging.info("Successfully calculated comparative performance metrics.")
    return df_success


def generate_markdown_report(
    summary_df: pd.DataFrame, perf_summary_df: pd.DataFrame, output_path: Path
) -> None:
    """Generates a rich, multi-section markdown report, now enhanced with new performance insights."""
    logging.info(
        "Generating comprehensive markdown report to: %s",
        output_path,
    )
    report_parts = [
        f"# Database Comparison Report",
        f"_Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
    ]

    report_parts.append("\n## 1. Executive Summary")
    summary_cols = [
        "Database",
        "Database Size (MB)",
        "Table Count",
        "Total Estimated Rows",
        "JDI (Join Dependency Index)",
        "NF (Normalization Factor)",
    ]
    report_parts.append(summary_df[summary_cols].to_markdown(index=False))

    report_parts.append("\n## 2. Performance Benchmark Comparison")
    if (
        not perf_summary_df.empty
        and "schema_efficiency_factor" in perf_summary_df.columns
    ):
        report_parts.append(
            "### At-a-Glance: Schema Efficiency Factor (Lower is Better)"
        )
        report_parts.append(
            "This table shows how many times slower each database is compared to the fastest benchmark database for each query category. A value of 1.0 means it is as fast as the benchmark."
        )
        pivot_efficiency = perf_summary_df.pivot_table(
            index="database",
            columns="category",
            values="schema_efficiency_factor",
            aggfunc="mean",
        ).round(2)
        report_parts.append(pivot_efficiency.to_markdown())

        report_parts.append("\n### Detailed Latency Breakdown (ms)")
        pivot_latency = perf_summary_df.pivot_table(
            index=["category", "query_id"], columns="database", values="latency_ms"
        ).round(2)
        report_parts.append(pivot_latency.to_markdown())
    else:
        report_parts.append(
            "No performance benchmark data was found or could be calculated."
        )

    report_parts.append("\n## 3. Run Metadata")
    report_parts.append(f"- **Databases Processed**: {summary_df['Database'].tolist()}")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(report_parts))
        logging.info("Successfully wrote markdown report.")
    except Exception as e:
        logging.error("Failed to write markdown report: %s", e)


# --- Main Orchestrator ---
def main() -> None:
    """Main function to orchestrate the comparison and aggregation process."""
    args = parse_arguments()
    config_path = Path(args.config)

    log_dir = Path(__file__).parent
    setup_logging(log_dir)
    logging.info("--- Starting Comparison & Aggregation Script ---")
    logging.info("Reading configuration from: %s", config_path)

    if not config_path.is_file():
        logging.critical("Configuration file not found: %s", config_path)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        project_root = Path(__file__).parent.parent
        input_dir = project_root / config.get("paths", "output_metrics")
        output_dir = project_root / config.get("paths", "output_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.critical(
            "Configuration file is missing a required section or option: %s",
            e,
        )
        sys.exit(1)

    # 1. Load all raw metric data from files
    all_loaded_data = load_all_metrics(input_dir)
    if not all_loaded_data:
        logging.critical("No metric files found or loaded. Halting execution.")
        sys.exit(1)

    # 2. Calculate ORIGINAL summary metrics for each database
    all_db_summaries = [
        calculate_summary_metrics(db_name, db_data)
        for db_name, db_data in sorted(all_loaded_data.items())
    ]
    summary_df = pd.DataFrame(all_db_summaries)

    # 3. Calculate NEW advanced performance metrics
    perf_summary_df = calculate_comparative_performance_metrics(all_loaded_data)

    # 4. Save ALL reports
    # ORIGINAL: machine-readable comparison matrix
    matrix_path = output_dir / "comparison_matrix.csv"
    summary_df.set_index("Database").T.to_csv(matrix_path)
    logging.info(
        "Successfully saved original comparison matrix to %s", matrix_path.name
    )

    # NEW: detailed performance summary
    perf_summary_path = output_dir / "report_performance_summary_detailed.csv"
    perf_summary_df.to_csv(perf_summary_path, index=False)
    logging.info("Saved detailed performance summary report to: %s", perf_summary_path)

    # NEW: high-level performance pivot
    if (
        not perf_summary_df.empty
        and "schema_efficiency_factor" in perf_summary_df.columns
    ):
        pivot_path = output_dir / "report_performance_pivot_efficiency.csv"
        perf_summary_df.pivot_table(
            index="database",
            columns="category",
            values="schema_efficiency_factor",
            aggfunc="mean",
        ).round(2).to_csv(pivot_path)
        logging.info(
            "Saved performance efficiency pivot table to: %s",
            pivot_path,
        )

    # ENHANCED ORIGINAL: human-readable markdown report
    report_path = output_dir / "comparison_report.md"
    generate_markdown_report(summary_df, perf_summary_df, report_path)

    logging.info("--- Comparison & Aggregation Script Finished ---")


if __name__ == "__main__":
    main()
