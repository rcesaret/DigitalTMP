# -*- coding: utf-8 -*-
"""Functions for calculating basic database and schema-level metrics."""

import logging
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .base import get_table_names, get_view_names


def get_basic_db_metrics(engine: Engine) -> Dict[str, Any]:
    """
    Calculates fundamental metrics for the entire connected database.

    Args:
        engine: A SQLAlchemy engine instance.

    Returns:
        A dictionary containing database-level metrics.
    """
    metrics = {"database_name": None, "database_size_mb": None}
    try:
        with engine.connect() as connection:
            # Get database name
            db_name_result = connection.execute(text("SELECT current_database();"))
            metrics["database_name"] = db_name_result.scalar_one()

            # Get database size
            db_size_query = text(
                "SELECT pg_catalog.pg_database_size(current_database()) / "
                "(1024 * 1024);"
            )
            db_size_result = connection.execute(db_size_query)
            metrics["database_size_mb"] = round(db_size_result.scalar_one(), 2)

            logging.info(
                "Successfully retrieved basic metrics for DB '%s'.",
                metrics["database_name"],
            )

    except Exception as e:
        logging.error("Failed to retrieve basic DB metrics: %s", e)

    return metrics


def get_schema_object_counts(engine: Engine, schema_name: str) -> Dict[str, Any]:
    """
    Counts various object types within a specific schema.

    Args:
        engine: A SQLAlchemy engine instance.
        schema_name: The name of the schema to inspect.

    Returns:
        A dictionary containing counts of schema objects.
    """
    metrics = {
        "schema_name": schema_name,
        "table_count": 0,
        "view_count": 0,
        "function_count": 0,
        "sequence_count": 0,
    }

    # Safely retrieve table and view counts
    try:
        metrics["table_count"] = len(get_table_names(engine, schema_name))
        metrics["view_count"] = len(get_view_names(engine, schema_name))
    except SQLAlchemyError as e:
        logging.error(
            "Failed to retrieve object counts for schema '%s': %s", schema_name, e
        )

    queries = {
        "function_count": text(
            "SELECT COUNT(*) FROM information_schema.routines "
            "WHERE routine_schema = :schema;"
        ),
        "sequence_count": text(
            "SELECT COUNT(*) FROM information_schema.sequences "
            "WHERE sequence_schema = :schema;"
        ),
    }

    try:
        with engine.connect() as connection:
            for key, query in queries.items():
                result = connection.execute(query, {"schema": schema_name})
                metrics[key] = result.scalar_one()
        logging.info(
            "Successfully counted objects for schema '%s'.",
            schema_name,
        )
    except Exception as e:
        logging.error(
            "Failed to count objects for schema '%s': %s",
            schema_name,
            e,
        )

    return metrics
