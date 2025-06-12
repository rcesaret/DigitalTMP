# -*- coding: utf-8 -*-
"""Functions for calculating structural schema, table, and column metrics."""

import logging
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import get_table_names


def get_table_level_metrics(engine: Engine, schema_name: str) -> List[Dict[str, Any]]:
    """
    Calculates metrics for each table in a schema.

    Includes row counts, column counts, sizes, and bloat estimations.

    Args:
        engine: A SQLAlchemy engine instance.
        schema_name: The name of the schema to inspect.

    Returns:
        A list of dictionaries, where each dict represents a table's metrics.
    """
    table_metrics = []
    table_names = get_table_names(engine, schema_name)
    if not table_names:
        return []

    # This is a standard, community-vetted query for table-level stats & bloat.
    query = text(
        """
        WITH constants AS (
            SELECT current_setting('block_size')::numeric AS bs, 23 AS hdr, 4 AS ma
        ),
        tables AS (
            SELECT tbl.oid, tbl.reltuples, tbl.relname,
                   (
                       (reltuples - reltuples * pg_relation_size(tbl.oid) /
                           ( (pg_relation_size(tbl.oid) - COALESCE(toast.relpages, 0) * bs) /
                               NULLIF(reltuples, 0) )
                       ) * 100
                   )::numeric AS null_frac
            FROM pg_class tbl
            JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
            LEFT JOIN pg_class toast ON tbl.reltoastrelid = toast.oid
            WHERE ns.nspname = :schema AND tbl.relkind = 'r'
        )
        SELECT
            tbl.relname AS table_name,
            tbl.reltuples::bigint AS row_estimate,
            (
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = tbl.relname
            ) AS column_count,
            pg_size_pretty(pg_relation_size(tbl.oid)) AS table_size,
            pg_size_pretty(pg_indexes_size(tbl.oid)) AS index_size,
            pg_size_pretty(pg_total_relation_size(tbl.oid)) AS total_size,
            (
                SELECT COUNT(*)
                FROM pg_index i
                WHERE i.indrelid = tbl.oid
            ) AS index_count,
            CASE WHEN tbl.reltuples > 0 THEN
                round(
                    (
                        (tbl.reltuples * (hdr + ma + 4) + (bs - hdr - ma - 4) * (tbl.reltuples/((bs - hdr - ma - 4)/ma) + 1)) / bs
                    ) * bs
                )
            ELSE 0 END AS expected_size_b,
            pg_relation_size(tbl.oid) AS actual_size_b
        FROM pg_class tbl
        JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
        WHERE ns.nspname = :schema AND tbl.relkind = 'r'
        ORDER BY pg_total_relation_size(tbl.oid) DESC;
    """
    )

    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection, params={"schema": schema_name})

        # Calculate bloat in Python for clarity
        df["bloat_bytes"] = df["actual_size_b"] - df["expected_size_b"]
        df["bloat_percent"] = round(
            (df["bloat_bytes"] / df["actual_size_b"].replace(0, 1)) * 100, 2
        )
        df["bloat_size"] = df["bloat_bytes"].apply(
            lambda x: f"{round(x / 1024**2, 2)} MB" if x > 0 else "0 MB"
        )

        # Drop helper columns before returning
        df = df.drop(columns=["expected_size_b", "actual_size_b"])

        table_metrics = df.to_dict("records")
        logging.info(
            "Successfully calculated table-level metrics for %s tables in schema '%s'.",
            len(table_metrics),
            schema_name,
        )

    except Exception as e:
        logging.error(
            "Failed to get table-level metrics for schema '%s': %s",
            schema_name,
            e,
        )

    return table_metrics


def get_column_structural_metrics(
    engine: Engine, schema_name: str
) -> List[Dict[str, Any]]:
    """
    Retrieves structural details for every column in a schema.

    Args:
        engine: A SQLAlchemy engine instance.
        schema_name: The name of the schema to inspect.

    Returns:
        A list of dictionaries, each representing a column's structural info.
    """
    query = text(
        """
        SELECT
            table_name,
            column_name,
            ordinal_position,
            column_default,
            is_nullable,
            data_type,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_schema = :schema
        ORDER BY table_name, ordinal_position;
    """
    )
    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection, params={"schema": schema_name})
        column_metrics = df.to_dict("records")
        logging.info(
            "Successfully retrieved structural metrics for %s columns in schema '%s'.",
            len(column_metrics),
            schema_name,
        )
        return column_metrics
    except Exception as e:
        logging.error(
            "Failed to get column structural metrics for schema '%s': %s",
            schema_name,
            e,
        )
        return []
