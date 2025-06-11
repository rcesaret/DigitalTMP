# -*- coding: utf-8 -*-
"""Functions for running performance benchmark queries."""
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.engine import Engine


def run_performance_benchmarks(engine: Engine, sql_queries_path: Path) -> List[Dict[str, Any]]:
    """
    Executes a set of SQL queries and times their latency.

    Args:
        engine: A SQLAlchemy engine instance.
        sql_queries_path: Path to a .sql file containing semicolon-separated queries.

    Returns:
        A list of dictionaries, each with the query and its execution time in ms.
    """
    benchmarks = []
    if not sql_queries_path.is_file():
        logging.error(f"Benchmark SQL file not found: {sql_queries_path}")
        return benchmarks

    try:
        with open(sql_queries_path, 'r', encoding='utf-8') as f:
            # Split queries by semicolon, filter out empty statements
            queries = [q.strip() for q in f.read().split(';') if q.strip()]
    except IOError as e:
        logging.error(f"Could not read benchmark file '{sql_queries_path}': {e}")
        return benchmarks

    logging.info(f"Running {len(queries)} benchmark queries from '{sql_queries_path.name}'...")
    
    with engine.connect() as connection:
        for i, query in enumerate(queries):
            query_name = f"Query {i+1}"
            result_entry = {
                "query_name": query_name,
                "sql_query": query,
                "latency_ms": None,
                "status": "Failed"
            }
            try:
                start_time = time.monotonic()
                # Execute query but don't fetch results to primarily time the DB engine
                connection.execute(text(query))
                end_time = time.monotonic()
                
                result_entry["latency_ms"] = round((end_time - start_time) * 1000, 2)
                result_entry["status"] = "Success"
                logging.info(f"  {query_name}: {result_entry['latency_ms']} ms")
                
            except Exception as e:
                logging.error(f"  Benchmark query '{query_name}' failed: {e}")
                result_entry["error_message"] = str(e)
            
            benchmarks.append(result_entry)
            
    return benchmarks
