# -*- coding: utf-8 -*-
"""Base utility functions for database object discovery."""
import logging
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_table_names(engine: Engine, schema_name: str) -> List[str]:
    """
    Retrieves a list of all user-defined table names in a given schema.

    Args:
        engine: A SQLAlchemy engine instance connected to the database.
        schema_name: The name of the schema to inspect.

    Returns:
        A list of table names. Returns an empty list on failure.
    """
    query = text(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = :schema AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
    )
    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"schema": schema_name})
            return [row[0] for row in result]
    except Exception as e:
        logging.error(f"Failed to get table names for schema '{schema_name}': {e}")
        return []

def get_view_names(engine: Engine, schema_name: str) -> List[str]:
    """
    Retrieves a list of all view names in a given schema.

    Args:
        engine: A SQLAlchemy engine instance connected to the database.
        schema_name: The name of the schema to inspect.

    Returns:
        A list of view names. Returns an empty list on failure.
    """
    query = text(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = :schema AND table_type = 'VIEW'
        ORDER BY table_name;
        """
    )
    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"schema": schema_name})
            return [row[0] for row in result]
    except Exception as e:
        logging.error(f"Failed to get view names for schema '{schema_name}': {e}")
        return []
