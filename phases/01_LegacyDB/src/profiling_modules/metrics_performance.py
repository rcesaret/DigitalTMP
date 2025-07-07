# -*- coding: utf-8 -*-
"""Functions for running database-specific performance benchmarks."""

import logging
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def run_performance_benchmarks(
    engine: Engine, db_name: str, schema_name: str, query_file_path: Path
) -> pd.DataFrame:
    """
    Runs a set of canonical SQL queries against a database to measure
    performance.

    This function robustly parses SQL files by splitting them based on a
    specific delimiter (`-- END Query`), extracting query metadata from
    comments, and cleaning the SQL before execution.

    Args:
        engine: An active SQLAlchemy Engine instance.
        db_name: The name of the database being profiled.
        schema_name: The name of the schema to run queries against.
        query_file_path: The path to the .sql file containing canonical
                        queries.

    Returns:
        A pandas DataFrame containing the performance results, including
        query name, status, latency, and any errors.
    """
    results = []
    if not query_file_path.exists():
        logging.warning(f"Query file not found for {db_name}: {query_file_path}")
        return pd.DataFrame()

    try:
        with open(query_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
    except IOError as e:
        logging.error(f"Could not read query file {query_file_path}: {e}")
        return pd.DataFrame()

    # Split the script into individual queries using a robust delimiter.
    # The delimiter is a line that starts with "-- END Query"
    # (case-insensitive).
    query_chunks = re.split(r"--\s*END Query.*", sql_script, flags=re.IGNORECASE)

    # Extract category and query ID information
    # Match category comments like "-- CATEGORY: baseline"
    category_pattern = r"--\s*CATEGORY:\s*(\w+)"
    # Match query comments like "-- QUERY: 1.1"
    query_id_pattern = r"--\s*QUERY:\s*(\d+(?:\.\d+)?)"

    # Log information about queries found
    query_count = sum(1 for chunk in query_chunks if chunk.strip())
    log_msg = f"Running {query_count} benchmark queries for '{db_name}'"
    log_msg += f" from '{query_file_path.name}'..."
    logging.info(log_msg)

    with engine.connect() as connection:
        for chunk in query_chunks:
            if not chunk.strip():
                continue

            # Extract category
            category_match = re.search(category_pattern, chunk, re.IGNORECASE)
            category = category_match.group(1) if category_match else "Unknown"

            # Extract query ID
            query_id_match = re.search(query_id_pattern, chunk, re.IGNORECASE)
            query_id = query_id_match.group(1) if query_id_match else "Unknown"

            # Create a meaningful query name
            query_name = f"{category.capitalize()} Performance - Query {query_id}"

            # Clean the SQL by removing all comment lines and extra
            # whitespace. This regex matches comment lines (starting with --)
            # and removes them
            sql_to_execute = re.sub(r"--.*$", "", chunk, flags=re.MULTILINE).strip()

            if not sql_to_execute:
                logging.warning(f"Skipping empty query chunk for: {query_name}")
                continue

            latency_ms: Any = None
            status = "Pending"
            records_returned = 0
            error_message = ""

            # Perform template variable substitution
            # Replace ${schema} with the actual schema name
            final_sql = sql_to_execute.replace("${schema}", schema_name)

            # Each query is run in its own transaction to isolate failures.
            trans = connection.begin()
            try:
                start_time = time.perf_counter()
                result = connection.execute(text(final_sql))

                if result.returns_rows:
                    # Fetch all records to ensure the query is fully executed.
                    records = result.fetchall()
                    records_returned = len(records)
                else:
                    # For statements like INSERT, UPDATE, DELETE
                    records_returned = 0

                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                status = "Success"
                trans.commit()

                # Log successful execution with timing
                logging.info(f"  {query_name}: {latency_ms:.1f} ms")

            except Exception as e:
                trans.rollback()
                status = "Failed"
                # Capture the first line of the error for concise logging.
                error_message = str(e).splitlines()[0]
                logging.error(
                    f"  Benchmark query '{query_name}' failed: {error_message}"
                )

            results.append({
                "query_name": query_name,
                "status": status,
                "latency_ms": latency_ms,
                "records_returned": records_returned,
                "error_message": error_message,
                "executed_sql": final_sql,
            })

    return pd.DataFrame(results)
