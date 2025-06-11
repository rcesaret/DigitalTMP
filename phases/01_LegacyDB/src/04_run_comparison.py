# -*- coding: utf-8 -*-
"""
Aggregates and compares results from the database profiling pipeline.

This script acts as the final synthesizer for the data-gathering phase. It does
not connect to any databases. Instead, it performs the following steps:
1.  Discovers and loads all raw metric files (.csv, .json) from the
    `outputs/metrics/` directory.
2.  Parses filenames to organize data by database.
3.  For each database, it calculates a set of high-level summary metrics
    by aggregating the raw data (e.g., summing row counts from all tables).
4.  Generates two primary outputs in the `outputs/reports/` directory:
    a) `comparison_matrix.csv`: A wide-format, machine-readable summary.
    b) `comparison_report.md`: A formatted, human-readable summary report.

The script is designed to be discovery-driven and resilient. It will only
process the data it finds and will gracefully handle missing files or data
for databases that may have failed during the profiling pipeline.

Usage:
    From the src/ directory, run:
    $ python 04_run_comparison.py --config config.ini
"""
import argparse
import configparser
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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
            logging.FileHandler(log_path, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate and compare database profiling results."
    )
    parser.add_argument(
        "--config", type=str, default="config.ini",
        help="Path to the configuration file (default: config.ini)"
    )
    return parser.parse_args()


# --- Core Logic ---
def load_all_metrics(input_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Discovers and loads all metric files from the input directory.

    Args:
        input_dir: The path to the directory containing metric files.

    Returns:
        A nested dictionary mapping: db_name -> metric_name -> data,
        where data is a DataFrame (for CSVs) or a dict (for JSONs).
    """
    logging.info(f"Scanning for metric files in: {input_dir}")
    all_data = defaultdict(dict)
    
    if not input_dir.is_dir():
        logging.error(f"Input metrics directory not found: {input_dir}")
        return {}

    metric_files = list(input_dir.glob('*.csv')) + list(input_dir.glob('*.json'))
    logging.info(f"Found {len(metric_files)} metric files to process.")

    for file_path in metric_files:
        try:
            parts = file_path.stem.split('_')
            db_name = parts[0]
            metric_name = '_'.join(parts[1:])
            
            if file_path.suffix == '.csv':
                all_data[db_name][metric_name] = pd.read_csv(file_path)
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data[db_name][metric_name] = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load or parse file '{file_path.name}': {e}")
            
    return dict(all_data)


def calculate_summary_metrics(db_name: str, db_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates a flat dictionary of key summary metrics for a single database.
    This function defines the "Metric Aggregation Strategy".

    Args:
        db_name: The name of the database being summarized.
        db_data: The dictionary of all loaded data for that database.

    Returns:
        A flat dictionary of aggregated metrics.
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


def generate_markdown_report(
    summary_df: pd.DataFrame,
    all_data: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """Generates a rich, multi-section markdown report."""
    logging.info(f"Generating comprehensive markdown report to: {output_path}")
    
    report_parts = []
    
    # --- Header ---
    report_parts.append(f"# Database Comparison Report")
    report_parts.append(f"_Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    
    # --- Section 1: Executive Summary ---
    report_parts.append("\n## 1. Executive Summary")
    report_parts.append("This table provides a high-level overview of the key profiling metrics across all analyzed databases.")
    # Reorder columns for presentation
    summary_cols = [
        "Database", "Database Size (MB)", "Table Count", "Total Estimated Rows",
        "JDI (Join Dependency Index)", "NF (Normalization Factor)"
    ]
    report_parts.append(summary_df[summary_cols].to_markdown(index=False))

    # --- Section 2: Performance Benchmarks ---
    report_parts.append("\n## 2. Performance Benchmark Comparison")
    perf_data = []
    for db_name, db_metrics in all_data.items():
        if "performance_benchmarks" in db_metrics:
            df = db_metrics["performance_benchmarks"]
            df['database'] = db_name
            perf_data.append(df)
            
    if perf_data:
        perf_df = pd.concat(perf_data)
        # Pivot for easy comparison
        pivot_perf = perf_df.pivot(index='query_name', columns='database', values='latency_ms')
        report_parts.append("Latency (in milliseconds) for canonical queries. Lower is better.")
        report_parts.append(pivot_perf.to_markdown())
    else:
        report_parts.append("No performance benchmark data was found.")

    # --- Section 3: Run Metadata ---
    report_parts.append("\n## 3. Run Metadata")
    report_parts.append(f"- **Databases Processed**: {list(all_data.keys())}")
    report_parts.append(f"- **Total Raw Metric Files Found**: {sum(len(v) for v in all_data.values())}")

    # --- Write to file ---
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(report_parts))
        logging.info("Successfully wrote markdown report.")
    except Exception as e:
        logging.error(f"Failed to write markdown report: {e}")


# --- Main Orchestrator ---
def main() -> None:
    """Main function to orchestrate the comparison and aggregation process."""
    args = parse_arguments()
    config_path = Path(args.config)
    
    log_dir = Path(__file__).parent
    setup_logging(log_dir)
    logging.info("--- Starting Comparison & Aggregation Script ---")
    
    project_root = Path(__file__).parent.parent
    input_dir = project_root / INPUT_METRICS_DIR
    output_dir = project_root / OUTPUT_REPORTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load all raw metric data from files
    all_loaded_data = load_all_metrics(input_dir)
    if not all_loaded_data:
        logging.critical("No metric files found or loaded. Halting execution.")
        sys.exit(1)

    # 2. Calculate summary metrics for each database
    all_db_summaries = []
    for db_name, db_data in sorted(all_loaded_data.items()):
        logging.info(f"--> Aggregating metrics for '{db_name}'...")
        summary = calculate_summary_metrics(db_name, db_data)
        all_db_summaries.append(summary)
        
    summary_df = pd.DataFrame(all_db_summaries)

    # 3. Create and save the machine-readable comparison matrix
    logging.info("Generating machine-readable comparison matrix...")
    # Transpose the summary so databases are columns, metrics are rows
    comparison_matrix = summary_df.set_index('Database').T
    matrix_path = output_dir / "comparison_matrix.csv"
    comparison_matrix.to_csv(matrix_path)
    logging.info(f"Successfully saved comparison matrix to {matrix_path.name}")

    # 4. Create and save the human-readable markdown report
    report_path = output_dir / "comparison_report.md"
    generate_markdown_report(summary_df, all_loaded_data, report_path)
    
    logging.info("--- Comparison & Aggregation Script Finished ---")


if __name__ == "__main__":
    main()