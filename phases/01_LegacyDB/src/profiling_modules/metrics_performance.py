# -*- coding: utf-8 -*-
"""Enhanced functions for running database-specific performance benchmarks."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_query_metadata(queries_dir: Path) -> Dict[str, Any]:
    """Load query categories and database mappings."""
    metadata_path = queries_dir / "_categories.json"
    if not metadata_path.exists():
        logging.warning(f"Query metadata not found at {metadata_path}")
        return {"categories": {}, "database_mappings": {}}

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error("Failed to decode JSON from %s: %s", metadata_path, e)
        return {"categories": {}, "database_mappings": {}}


def parse_categorized_queries(sql_content: str) -> List[Tuple[str, str, str]]:
    """Parse SQL benchmark files containing category and query markers.

    The SQL files are expected to contain blocks marked with ``-- CATEGORY:`` and
    ``-- QUERY:`` comments::

        -- CATEGORY: baseline
        -- QUERY: 1.1
        SELECT COUNT(*) FROM ...;

    Each ``-- QUERY:`` section corresponds to a single executable SQL statement
    that belongs to the most recently seen category.

    Returns a list of ``(category, query_id, sql)`` tuples.
    """

    queries: List[Tuple[str, str, str]] = []
    current_category = "uncategorized"
    current_entry: Optional[Dict[str, Any]] = None

    for raw_line in sql_content.splitlines():
        line = raw_line.strip()

        if line.startswith("-- CATEGORY:"):
            # Update the active category. This will apply to the next query we
            # encounter.
            current_category = line.split(":", 1)[1].strip()
            continue

        if line.startswith("-- QUERY:"):
            # Finalize any previous query before starting a new one.
            if current_entry is not None:
                sql = " ".join(current_entry["sql_lines"]).strip()
                if sql.endswith(";"):
                    sql = sql[:-1]
                queries.append(
                    (current_entry["category"], current_entry["query_id"], sql)
                )

            query_id = line.split(":", 1)[1].strip()
            current_entry = {
                "category": current_category,
                "query_id": query_id,
                "sql_lines": [],
            }
            continue

        if current_entry is not None and (line and not line.startswith("--")):
            current_entry["sql_lines"].append(line)

    # Finalize the last query block if present.
    if current_entry is not None:
        sql = " ".join(current_entry["sql_lines"]).strip()
        if sql.endswith(";"):
            sql = sql[:-1]
        queries.append((current_entry["category"], current_entry["query_id"], sql))

    return queries


def run_performance_benchmarks(
    engine: Engine, db_name: str, schema_name: str, sql_queries_dir: Path
) -> List[Dict[str, Any]]:
    """
    Execute database-specific performance benchmarks.

    Args:
        engine: SQLAlchemy engine instance
        db_name: Name of the database being profiled
        schema_name: Schema name for the database
        sql_queries_dir: Path to directory containing query files

    Returns:
        List of benchmark results with query metadata
    """
    benchmarks = []

    # Load metadata to find appropriate query file
    metadata = load_query_metadata(sql_queries_dir)
    db_mappings = metadata.get("database_mappings", {})
    categories = metadata.get("categories", {})

    # Determine query file
    query_filename = db_mappings.get(db_name)
    if not query_filename:
        logging.warning(
            f"No specific queries found for database '{db_name}', using legacy approach"
        )
        # Fallback to legacy single file if it exists
        legacy_path = sql_queries_dir.parent / "canonical_queries.sql"
        if legacy_path.exists():
            return run_legacy_benchmarks(engine, legacy_path)
        return benchmarks

    query_file_path = sql_queries_dir / query_filename
    if not query_file_path.exists():
        logging.error("Query file not found: %s", query_file_path)
        return benchmarks

    # Read and parse queries
    try:
        with open(query_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
    except IOError as e:
        logging.error(
            "Could not read query file '%s': %s",
            query_file_path,
            e,
        )
        return benchmarks

    # Parse categorized queries
    queries = parse_categorized_queries(sql_content)

    logging.info(
        "Running %s benchmark queries for '%s' from '%s'...",
        len(queries),
        db_name,
        query_filename,
    )

    with engine.connect() as connection:
        for category, query_id, query_sql in queries:
            # Build descriptive query name
            category_name = categories.get(category, {}).get("name", category)
            query_name = f"{category_name} - Query {query_id}"

            result_entry = {
                "database": db_name,
                "schema": schema_name,
                "category": category,
                "query_id": query_id,
                "query_name": query_name,
                "sql_query": query_sql,
                "latency_ms": None,
                "status": "Failed",
            }

            try:
                start_time = time.monotonic()
                connection.execute(text(query_sql))
                end_time = time.monotonic()

                result_entry["latency_ms"] = round((end_time - start_time) * 1000, 2)
                result_entry["status"] = "Success"
                logging.info("  %s: %s ms", query_name, result_entry["latency_ms"])

            except Exception as e:
                logging.exception("  Query '%s' failed: %s", query_name, e)
                result_entry["error_message"] = str(e)

            benchmarks.append(result_entry)

    return benchmarks


def run_legacy_benchmarks(
    engine: Engine, sql_queries_path: Path
) -> List[Dict[str, Any]]:
    """Backward compatibility: Run benchmarks from single SQL file."""
    # Original implementation for backward compatibility
    benchmarks = []
    if not sql_queries_path.is_file():
        logging.error("Benchmark SQL file not found: %s", sql_queries_path)
        return benchmarks

    try:
        with open(sql_queries_path, "r", encoding="utf-8") as f:
            queries = [q.strip() for q in f.read().split(";") if q.strip()]
    except IOError as e:
        logging.error(
            "Could not read benchmark file '%s': %s",
            sql_queries_path,
            e,
        )
        return benchmarks

    logging.info("Running %s legacy benchmark queries...", len(queries))

    with engine.connect() as connection:
        for i, query in enumerate(queries):
            query_name = f"Query {i + 1}"
            result_entry = {
                "query_name": query_name,
                "sql_query": query,
                "latency_ms": None,
                "status": "Failed",
            }
            try:
                start_time = time.monotonic()
                connection.execute(text(query))
                end_time = time.monotonic()

                result_entry["latency_ms"] = round((end_time - start_time) * 1000, 2)
                result_entry["status"] = "Success"
                logging.info("  %s: %s ms", query_name, result_entry["latency_ms"])

            except Exception as e:
                logging.error("  Benchmark query '%s' failed: %s", query_name, e)
                result_entry["error_message"] = str(e)

            benchmarks.append(result_entry)

    return benchmarks
