# -*- coding: utf-8 -*-
"""Functions for profiling the data content within columns."""

import logging
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.engine import Engine

import pandas as pd

from .base import get_table_names


def get_all_column_profiles(engine: Engine, schema_name: str) -> List[Dict[str, Any]]:
    """
    Calculates data profile metrics (NULLs, distinctness) for all columns.

    This function can be VERY SLOW on large databases as it queries
    each column individually.

    Args:
        engine: A SQLAlchemy engine instance.
        schema_name: The name of the schema to inspect.

    Returns:
        A list of dictionaries, each representing a column's data profile.
    """
    logging.warning(
        "Initiating full column profile. This is a slow operation "
        "that queries each column individually."
    )
    all_profiles = []
    table_names = get_table_names(engine, schema_name)

    # Alternative (faster) approach using pg_stats
    # This is much faster but relies on ANALYZE having been run recently.
    pg_stats_query = text(
        """
        SELECT
            schemaname || '.' || tablename AS fq_table_name,
            tablename,
            attname AS column_name,
            null_frac * 100 AS null_percent,
            n_distinct AS distinct_values_estimate
        FROM pg_stats
        WHERE schemaname = :schema;
    """
    )

    try:
        with engine.connect() as connection:
            df_stats = pd.read_sql_query(
                pg_stats_query, connection, params={"schema": schema_name}
            )

        # Augment with exact counts (the slow part)
        total_rows_map = {}
        for table in table_names:
            try:
                with engine.connect() as connection:
                    row_count_result = connection.execute(
                        text(f'SELECT COUNT(*) FROM "{schema_name}"."{table}";')
                    )
                    total_rows_map[table] = row_count_result.scalar_one()
            except Exception as e:
                logging.error(
                    "Could not get row count for '%s.%s': %s",
                    schema_name,
                    table,
                    e,
                )
                total_rows_map[table] = 0

        # Now, create the final list from the pg_stats DataFrame
        for record in df_stats.to_dict("records"):
            table_name = record["tablename"]
            total_rows = total_rows_map.get(table_name, 0)
            if total_rows > 0:
                record["null_count_estimate"] = int(
                    total_rows * (record["null_percent"] / 100.0)
                )
            else:
                record["null_count_estimate"] = 0
            all_profiles.append(record)

        logging.info(
            "Successfully generated column profiles for %s columns in schema '%s' using pg_stats.",
            len(all_profiles),
            schema_name,
        )

    except Exception as e:
        logging.error(
            "An error occurred during full column profiling for schema '%s': %s",
            schema_name,
            e,
        )
        # Fallback or return empty might be needed here
        return []

    return all_profiles
