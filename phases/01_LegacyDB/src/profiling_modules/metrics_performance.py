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
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_categorized_queries(sql_content: str) -> List[Tuple[str, str, str]]:
    """
    Parse SQL file with category markers.
    
    Expected format:
    -- CATEGORY: baseline
    -- QUERY: 1.1
    SELECT COUNT(*) FROM ...;
    
    Returns list of (category, query_id, sql) tuples.
    """
    queries = []
    current_category = "uncategorized"
    current_query_id = ""
    
    # Split by query markers instead of just semicolons
    sections = sql_content.split('-- QUERY:')
    
    for section in sections[1:]:  # Skip first empty section
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Extract query ID from first line
        query_id = lines[0].strip()
        
        # Look for category marker in preceding lines
        sql_lines = []
        for line in lines[1:]:
            if line.strip().startswith('-- CATEGORY:'):
                current_category = line.split(':', 1)[1].strip()
            elif line.strip() and not line.strip().startswith('--'):
                sql_lines.append(line)
        
        # Join SQL lines and clean up
        sql = ' '.join(sql_lines).strip()
        if sql.endswith(';'):
            sql = sql[:-1]
            
        if sql:
            queries.append((current_category, query_id, sql))
    
    return queries


def run_performance_benchmarks(
    engine: Engine, 
    db_name: str,
    schema_name: str,
    sql_queries_dir: Path
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
        logging.warning(f"No specific queries found for database '{db_name}', using legacy approach")
        # Fallback to legacy single file if it exists
        legacy_path = sql_queries_dir.parent / "canonical_queries.sql"
        if legacy_path.exists():
            return run_legacy_benchmarks(engine, legacy_path)
        return benchmarks
    
    query_file_path = sql_queries_dir / query_filename
    if not query_file_path.exists():
        logging.error(f"Query file not found: {query_file_path}")
        return benchmarks
    
    # Read and parse queries
    try:
        with open(query_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except IOError as e:
        logging.error(f"Could not read query file '{query_file_path}': {e}")
        return benchmarks
    
    # Parse categorized queries
    queries = parse_categorized_queries(sql_content)
    
    logging.info(f"Running {len(queries)} benchmark queries for '{db_name}' from '{query_filename}'...")
    
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
                "status": "Failed"
            }
            
            try:
                start_time = time.monotonic()
                connection.execute(text(query_sql))
                end_time = time.monotonic()
                
                result_entry["latency_ms"] = round((end_time - start_time) * 1000, 2)
                result_entry["status"] = "Success"
                logging.info(f"  {query_name}: {result_entry['latency_ms']} ms")
                
            except Exception as e:
                logging.error(f"  Query '{query_name}' failed: {e}")
                result_entry["error_message"] = str(e)
            
            benchmarks.append(result_entry)
    
    return benchmarks


def run_legacy_benchmarks(engine: Engine, sql_queries_path: Path) -> List[Dict[str, Any]]:
    """Backward compatibility: Run benchmarks from single SQL file."""
    # Original implementation for backward compatibility
    benchmarks = []
    if not sql_queries_path.is_file():
        logging.error(f"Benchmark SQL file not found: {sql_queries_path}")
        return benchmarks

    try:
        with open(sql_queries_path, 'r', encoding='utf-8') as f:
            queries = [q.strip() for q in f.read().split(';') if q.strip()]
    except IOError as e:
        logging.error(f"Could not read benchmark file '{sql_queries_path}': {e}")
        return benchmarks

    logging.info(f"Running {len(queries)} legacy benchmark queries...")
    
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
