# -*- coding: utf-8 -*-
"""
Database Verification Utilities for Phase 1 Pipeline Idempotency

This module provides comprehensive verification functions to ensure
pipeline idempotency and robust error handling. Each function checks
a specific aspect of database state to verify successful completion
of pipeline stages.

Usage:
    from db_verification import (
        verify_database_exists,
        verify_schema_populated,
        verify_benchmark_database_ready,
        check_pipeline_prerequisites
    )
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# --- Database Existence Verification ---


def verify_database_exists(engine: Engine, db_name: str) -> bool:
    """Verify that a database exists and is accessible.

    Args:
        engine: SQLAlchemy engine connected to root database
        db_name: Name of database to check

    Returns:
        True if database exists and is accessible
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            exists = result.scalar() == 1

        if exists:
            # Also verify we can connect to it
            db_url = str(engine.url).rsplit("/", 1)[0] + f"/{db_name}"
            test_engine = create_engine(db_url)
            with test_engine.connect():
                pass  # Just test connection
            test_engine.dispose()
            logging.info(f"Database '{db_name}' exists and is accessible.")
            return True
        else:
            logging.warning(f"Database '{db_name}' does not exist.")
            return False

    except SQLAlchemyError as e:
        logging.error(f"Failed to verify database '{db_name}': {e}")
        return False


# --- Schema Population Verification ---


def verify_schema_populated(
    engine: Engine, schema_name: str, min_tables: int = 1
) -> Tuple[bool, Dict[str, int]]:
    """Verify that a schema exists and is properly populated with data.

    Args:
        engine: SQLAlchemy engine connected to target database
        schema_name: Name of schema to check
        min_tables: Minimum number of tables expected

    Returns:
        Tuple of (is_populated, table_stats)
        table_stats: Dict mapping table_name to row_count
    """
    try:
        with engine.connect() as conn:
            # Check if schema exists
            schema_check = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.schemata "
                    "WHERE schema_name = :name"
                ),
                {"name": schema_name},
            )
            if not schema_check.scalar():
                logging.error(f"Schema '{schema_name}' does not exist.")
                return False, {}

            # Get all tables in schema
            tables_query = text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables_result = conn.execute(tables_query, {"schema": schema_name})
            tables = [row[0] for row in tables_result]

            if len(tables) < min_tables:
                logging.error(
                    f"Schema '{schema_name}' has {len(tables)} tables, "
                    f"expected at least {min_tables}"
                )
                return False, {}

            # Count rows in each table
            table_stats = {}
            total_rows = 0

            for table in tables:
                try:
                    count_query = text(
                        f'SELECT COUNT(*) FROM "{schema_name}"."{table}"'
                    )
                    count_result = conn.execute(count_query)
                    row_count = count_result.scalar()
                    table_stats[table] = row_count
                    total_rows += row_count
                except SQLAlchemyError as e:
                    logging.warning(
                        f"Could not count rows in {schema_name}.{table}: {e}"
                    )
                    table_stats[table] = -1  # Error marker

            is_populated = (
                len(tables) >= min_tables
                and total_rows > 0
                and all(count >= 0 for count in table_stats.values())
            )

            if is_populated:
                logging.info(
                    f"Schema '{schema_name}' is properly populated: "
                    f"{len(tables)} tables, {total_rows} total rows"
                )
            else:
                logging.error(
                    f"Schema '{schema_name}' appears empty or corrupted: "
                    f"{len(tables)} tables, {total_rows} total rows"
                )

            return is_populated, table_stats

    except SQLAlchemyError as e:
        logging.error(f"Failed to verify schema '{schema_name}': {e}")
        return False, {}


# --- Benchmark Database Verification ---


def verify_benchmark_database_ready(
    engine: Engine, table_name: str = "wide_format_data"
) -> bool:
    """Verify that a benchmark database is set up with data and indexes.

    Args:
        engine: SQLAlchemy engine connected to benchmark database
        table_name: Name of the main benchmark table

    Returns:
        True if database is ready for benchmarking
    """
    try:
        with engine.connect() as conn:
            # Check if table exists
            table_check = conn.execute(
                text("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table
                """),
                {"table": table_name},
            )
            if not table_check.scalar():
                logging.error(f"Benchmark table '{table_name}' does not exist.")
                return False

            # Check row count
            count_query = text(f'SELECT COUNT(*) FROM public."{table_name}"')
            row_count = conn.execute(count_query).scalar()

            if row_count == 0:
                logging.error(f"Benchmark table '{table_name}' is empty.")
                return False

            # Check indexes exist
            index_query = text("""
                SELECT COUNT(*) FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = :table
            """)
            index_count = conn.execute(index_query, {"table": table_name}).scalar()

            if index_count < 5:  # Should have many indexes from our fixes
                logging.warning(
                    f"Benchmark table '{table_name}' has only {index_count} "
                    "indexes. Expected comprehensive indexing for fair "
                    "performance comparison."
                )

            # Check table statistics are up to date
            stats_query = text("""
                SELECT last_analyze, last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                AND relname = :table
            """)
            stats_result = conn.execute(stats_query, {"table": table_name}).fetchone()

            if stats_result and (stats_result[0] or stats_result[1]):
                logging.info(
                    f"Benchmark database ready: {row_count} rows, "
                    f"{index_count} indexes, statistics current"
                )
                return True
            else:
                logging.warning(
                    f"Benchmark table '{table_name}' statistics may be "
                    "outdated. Run ANALYZE for optimal query performance."
                )
                return True  # Still functional, just not optimal

    except SQLAlchemyError as e:
        logging.error(f"Failed to verify benchmark database: {e}")
        return False


# --- Pipeline Prerequisites Verification ---


def check_pipeline_prerequisites(cfg, script_name: str) -> Tuple[bool, List[str]]:
    """Check prerequisites for a specific pipeline script.

    Args:
        cfg: Configuration object
        script_name: Name of script to check prerequisites for

    Returns:
        Tuple of (prerequisites_met, error_messages)
    """
    errors = []

    try:
        # Create engine for root database
        conn_str = (
            f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
            f"{cfg.host}:{cfg.port}/{cfg.root_db}"
        )
        root_engine = create_engine(conn_str)

        if script_name == "01_create_benchmark_dbs.py":
            # Check that source database exists and is populated
            if not verify_database_exists(root_engine, cfg.source_db):
                errors.append(
                    f"Source database '{cfg.source_db}' does not exist "
                    f"or is not accessible"
                )
            else:
                # Connect to source database and check schema
                source_conn_str = (
                    f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
                    f"{cfg.host}:{cfg.port}/{cfg.source_db}"
                )
                source_engine = create_engine(source_conn_str)

                # Convention: schema = lowercase db name
                schema_name = cfg.source_db.lower()
                is_populated, table_stats = verify_schema_populated(
                    source_engine, schema_name, min_tables=15
                )

                if not is_populated:
                    errors.append(
                        f"Source schema '{schema_name}' in database "
                        f"'{cfg.source_db}' is not properly populated. "
                        f"Run 00_setup_databases.py first."
                    )

                source_engine.dispose()

        elif script_name == "02_run_profiling_pipeline.py":
            # Check that all databases (legacy and benchmark) exist
            all_dbs = cfg.legacy_dbs + cfg.benchmark_dbs
            for db_name in all_dbs:
                if not verify_database_exists(root_engine, db_name):
                    errors.append(f"Database '{db_name}' does not exist")

        elif script_name == "03_generate_erds.py":
            # Same as profiling - all databases must exist
            all_dbs = cfg.legacy_dbs + cfg.benchmark_dbs
            for db_name in all_dbs:
                if not verify_database_exists(root_engine, db_name):
                    errors.append(f"Database '{db_name}' does not exist")

        elif script_name == "04_run_comparison.py":
            # Check that metric files exist (outputs from profiling)
            metrics_dir = cfg.sql_dir.parent / "outputs" / "metrics"
            if not metrics_dir.exists():
                errors.append(
                    "Metrics directory does not exist. "
                    "Run 02_run_profiling_pipeline.py first."
                )
            else:
                metric_files = list(metrics_dir.glob("*.csv")) + list(
                    metrics_dir.glob("*.json")
                )
                if len(metric_files) == 0:
                    errors.append(
                        "No metric files found. "
                        "Run 02_run_profiling_pipeline.py first."
                    )

        root_engine.dispose()

    except Exception as e:
        errors.append(f"Failed to check prerequisites: {e}")

    prerequisites_met = len(errors) == 0

    if prerequisites_met:
        logging.info(f"✓ All prerequisites met for {script_name}")
    else:
        logging.error(f"✗ Prerequisites not met for {script_name}:")
        for error in errors:
            logging.error(f"  - {error}")

    return prerequisites_met, errors


# --- Comprehensive Pipeline State Check ---


def verify_full_pipeline_state(cfg) -> Dict[str, bool]:
    """Comprehensive check of entire pipeline state.

    Returns:
        Dict mapping stage_name to completion_status
    """
    state = {}

    try:
        conn_str = (
            f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
            f"{cfg.host}:{cfg.port}/{cfg.root_db}"
        )
        root_engine = create_engine(conn_str)

        # Stage 0: Legacy databases setup
        legacy_ready = True
        for db_name in cfg.legacy_dbs:
            if not verify_database_exists(root_engine, db_name):
                legacy_ready = False
                break

            # Check schema population
            db_conn_str = (
                f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
                f"{cfg.host}:{cfg.port}/{db_name}"
            )
            db_engine = create_engine(db_conn_str)
            schema_name = db_name.lower()
            is_populated, _ = verify_schema_populated(
                db_engine, schema_name, min_tables=5
            )
            db_engine.dispose()

            if not is_populated:
                legacy_ready = False
                break

        state["00_setup_databases"] = legacy_ready

        # Stage 1: Benchmark databases
        benchmark_ready = True
        for db_name in cfg.benchmark_dbs:
            if not verify_database_exists(root_engine, db_name):
                benchmark_ready = False
                break

            db_conn_str = (
                f"postgresql+psycopg2://{cfg.user}:{cfg.password}@"
                f"{cfg.host}:{cfg.port}/{db_name}"
            )
            db_engine = create_engine(db_conn_str)
            if not verify_benchmark_database_ready(db_engine):
                benchmark_ready = False
                db_engine.dispose()
                break
            db_engine.dispose()

        state["01_create_benchmark_dbs"] = benchmark_ready

        # Stage 2: Profiling completed
        metrics_dir = cfg.sql_dir.parent / "outputs" / "metrics"
        profiling_ready = (
            metrics_dir.exists()
            and len(list(metrics_dir.glob("*.csv")) + list(metrics_dir.glob("*.json")))
            > 10
        )
        state["02_run_profiling_pipeline"] = profiling_ready

        # Stage 3: ERDs generated
        erds_dir = cfg.sql_dir.parent / "outputs" / "erds"
        erds_ready = erds_dir.exists() and len(list(erds_dir.glob("*.svg"))) > 0
        state["03_generate_erds"] = erds_ready

        # Stage 4: Comparison reports
        reports_dir = cfg.sql_dir.parent / "outputs" / "reports"
        reports_ready = (
            reports_dir.exists()
            and len(list(reports_dir.glob("*.csv")) + list(reports_dir.glob("*.md")))
            > 0
        )
        state["04_run_comparison"] = reports_ready

        root_engine.dispose()

    except Exception as e:
        logging.error(f"Failed to verify pipeline state: {e}")
        # Return partial state if possible

    return state
