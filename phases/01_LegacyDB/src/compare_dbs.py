# compare_dbs.py
"""
Orchestration script to compare multiple PostgreSQL database schemas.

This script performs the following workflow:
1.  Defines a list of target databases to be profiled and compared.
2.  For each database, it calls the `profile_db.py` script as a subprocess
    to generate detailed metrics.
3.  Connects to each database to read the persisted metrics tables created
    by the profiler.
4.  Consolidates all metrics into a single, comprehensive pandas DataFrame.
5.  Saves the consolidated DataFrame to a CSV file (`comparison_matrix.csv`).
6.  Formats the DataFrame into a professional, human-readable Markdown table.
7.  Saves the Markdown report to a file (`comparison_report.md`).

Usage:
    python 02_compare_schemas.py
"""
import argparse
import subprocess
import pandas as pd
from sqlalchemy import create_engine, text

# --- Configuration ---

# Define the databases to profile.
# Add or remove entries here to change the scope of the comparison.
# The 'name' will be used as the column header in the final report.
DATABASES_TO_COMPARE = [
    {
        "name": "DF8",
        "url": "postgresql://postgres:postgres@localhost:5432/tmp_df8"
    },
    {
        "name": "DF9",
        "url": "postgresql://postgres:postgres@localhost:5432/tmp_df9"
    },
    {
        "name": "DF10",
        "url": "postgresql://postgres:postgres@localhost:5432/tmp_df10"
    },
    {
        "name": "Flat raw",
        "url": "postgresql://postgres:postgres@localhost:5432/tmp_flat_raw"
    },
    {
        "name": "Flat w/ text",
        "url": "postgresql://postgres:postgres@localhost:5432/tmp_flat_w_text"
    }
]

METRICS_SCHEMA = "tmp_db_metrics"
TARGET_SCHEMA = "public"
PROFILER_SCRIPT_PATH = "profile_db.py"
OUTPUT_CSV_PATH = "comparison_matrix.csv"
OUTPUT_MD_PATH = "comparison_report.md"


# Define the structure and formatting for the final Markdown report.
# This ensures a consistent and professional layout.
REPORT_STRUCTURE = [
    ("**I. Foundational & Cardinality Metrics**", [
        ("Total Tables", "{:,.0f}"),
        ("Total Columns", "{:,.0f}"),
        ("Total Rows", "{:,.0f}"),
        ("Total Cells (Rows × Cols)", "{:,.0f}"),
        ("SQL Dump File Size (MB)", "{:.2f}") # Placeholder, collected manually
    ]),
    ("**II. Structural Integrity & Content Metrics**", [
        ("Primary Key Uniqueness (%)", "{:.1f}"), # Placeholder
        ("Foreign Key Count", "{:,.0f}"),
        ("NULL Value Count", "{:,.0f}"), # Placeholder
        ("NULL Value Percentage (%)", "{:.2f}"), # Placeholder
        ("Data Type Distribution", "{}"), # Placeholder, complex value
        ("Average Row Length (bytes)", "{:.1f}")
    ]),
    ("**III. Indexing Metrics**", [
        ("Total Index Count", "{:,.0f}"),
        ("Index-to-Table Ratio", "{:.2f}")
    ]),
    ("**IV. Performance & Usability Benchmarks**", [
        ("Query: Full Record Retrieval (s)", "{}"), # Placeholder
        ("Query: Targeted Analytical (s)", "{}"), # Placeholder
        ("Query: Full Data Load (s)", "{}"), # Placeholder
        ("Complexity: Join-Dependency Index (JDI)", "{}"), # Placeholder
        ("Complexity: Lookup Inflation Factor (LIF)", "{}"), # Placeholder
        ("Usability: Lines of Code (Full Record)", "{}"), # Placeholder
        ("Usability: Lines of Code (Targeted Query)", "{}") # Placeholder
    ]),
    ("**V. PostgreSQL Operational Health**", [
        ("Cache Hit Rate (%)", "{:.2f}"),
        ("Index Hit Rate (%)", "{:.2f}"),
        ("Total Table Bloat (MB)", "{:.2f}"),
        ("Total Index Bloat (MB)", "{:.2f}")
    ])
]


def run_profiler(db_url, metrics_schema, target_schema):
    """Calls the profile_db.py script as a subprocess."""
    print(f"  > Running profiler on {db_url.split('/')[-1]}...")
    command = [
        "python",
        PROFILER_SCRIPT_PATH,
        "--db-url", db_url,
        "--metrics-schema", metrics_schema,
        "--target-schema", target_schema
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("    ...profiling successful.")
    except subprocess.CalledProcessError as e:
        print(f"    ...ERROR profiling database.")
        print(f"    STDOUT: {e.stdout}")
        print(f"    STDERR: {e.stderr}")
        raise


def fetch_metric(engine, query, default=0):
    """Helper to fetch a single scalar value from a metric query."""
    try:
        return pd.read_sql(query, engine).iloc[0, 0] or default
    except (IndexError, TypeError):
        return default


def fetch_metrics_for_db(db_url, db_name):
    """Connects to a database and fetches all profiled metrics."""
    print(f"  > Fetching metrics from {db_name}...")
    engine = create_engine(db_url)
    metrics = {"Database": db_name}

    # I. Cardinality
    card = pd.read_sql(f'SELECT * FROM "{METRICS_SCHEMA}".metric_schema_cardinality', engine).iloc[0]
    metrics["Total Tables"] = card.get("table_count", 0)
    metrics["Total Columns"] = card.get("column_count", 0)
    metrics["Total Rows"] = card.get("estimated_row_count", 0)
    metrics["Total Cells (Rows × Cols)"] = metrics["Total Tables"] * metrics["Total Columns"]

    # II. Structural Integrity
    metrics["Foreign Key Count"] = fetch_metric(engine, f'SELECT foreign_key_count FROM "{METRICS_SCHEMA}".metric_fk_stats')

    # Calculate average row length from table stats
    table_stats = pd.read_sql(f'SELECT * FROM "{METRICS_SCHEMA}".metric_table_bloat', engine)
    total_bytes = table_stats["table_bytes"].sum()
    metrics["Average Row Length (bytes)"] = total_bytes / metrics["Total Rows"] if metrics["Total Rows"] > 0 else 0

    # III. Indexing
    index_summary = pd.read_sql(f'SELECT * FROM "{METRICS_SCHEMA}".metric_index_summary', engine).iloc[0]
    metrics["Total Index Count"] = index_summary.get("total_indexes", 0)
    metrics["Index-to-Table Ratio"] = metrics["Total Index Count"] / metrics["Total Tables"] if metrics["Total Tables"] > 0 else 0

    # V. Operational Health
    health_stats = pd.read_sql(f'SELECT * FROM "{METRICS_SCHEMA}".metric_operational_health', engine)
    cache_hit = health_stats[health_stats['metric'] == 'Cache Hit Rate (%)']['value']
    index_hit = health_stats[health_stats['metric'] == 'Index Hit Rate (%)']['value']
    metrics["Cache Hit Rate (%)"] = cache_hit.iloc[0] if not cache_hit.empty else 0
    metrics["Index Hit Rate (%)"] = index_hit.iloc[0] if not index_hit.empty else 0

    # Sum bloat stats
    metrics["Total Table Bloat (MB)"] = table_stats['bloat_bytes'].sum() / (1024 * 1024)
    index_details = pd.read_sql(f'SELECT * FROM "{METRICS_SCHEMA}".metric_index_details', engine)
    # Note: Index bloat is harder to estimate without dedicated extensions, so we use size as a proxy here.
    # A full implementation would require a more complex query like the one for table bloat.
    metrics["Total Index Bloat (MB)"] = 0 # Placeholder for simplicity

    return metrics


def format_dataframe_as_markdown(df):
    """Formats the consolidated DataFrame into a professional Markdown table."""
    print("  > Formatting report into Markdown table...")
    # Start with headers
    headers = [col for col in df.columns]
    md_string = "| Metric Category & Name | " + " | ".join(headers) + " |\n"
    md_string += "| :--- |" + " :--: |" * len(headers) + "\n" # Use centered columns for data

    # Iterate through the defined structure
    for category_title, metrics in REPORT_STRUCTURE:
        md_string += f"| {category_title} |" + " |" * len(headers) + "\n"
        for metric_name, fmt_str in metrics:
            row_data = df[df['Metric'] == metric_name].iloc[0]
            # Format each cell
            formatted_cells = []
            for header in headers:
                val = row_data.get(header)
                if pd.isna(val):
                    formatted_cells.append("")
                else:
                    try:
                        formatted_cells.append(fmt_str.format(val))
                    except (ValueError, TypeError):
                        formatted_cells.append(str(val))

            md_string += f"| &nbsp;&nbsp;&nbsp; *{metric_name}* | " + " | ".join(formatted_cells) + " |\n"

    return md_string


def main():
    """Main orchestration function."""
    print("[Step 1/4] Running profiler script on all target databases...")
    for db_config in DATABASES_TO_COMPARE:
        run_profiler(db_config["url"], METRICS_SCHEMA, TARGET_SCHEMA)
    print("...Profiling step complete.\n")

    print("[Step 2/4] Fetching and consolidating metrics from all databases...")
    all_metrics_data = []
    for db_config in DATABASES_TO_COMPARE:
        metrics = fetch_metrics_for_db(db_config["url"], db_config["name"])
        all_metrics_data.append(metrics)
    print("...Fetching step complete.\n")

    # Create the comparison DataFrame
    # Transpose the data to have metrics as rows and databases as columns
    comparison_df = pd.DataFrame(all_metrics_data).set_index('Database').T
    comparison_df.reset_index(inplace=True)
    comparison_df.rename(columns={'index': 'Metric'}, inplace=True)


    print(f"[Step 3/4] Saving raw metrics to '{OUTPUT_CSV_PATH}'...")
    comparison_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print("...CSV saved successfully.\n")

    print(f"[Step 4/4] Generating formatted Markdown report...")
    # Pivot the DataFrame for Markdown formatting
    markdown_df = comparison_df.set_index('Metric')
    markdown_table_string = format_dataframe_as_markdown(markdown_df.T)
    with open(OUTPUT_MD_PATH, 'w', encoding='utf-8') as f:
        f.write(markdown_table_string)
    print(f"...Markdown report saved successfully to '{OUTPUT_MD_PATH}'.\n")

    print("Orchestration complete.")


if __name__ == '__main__':
    main()
