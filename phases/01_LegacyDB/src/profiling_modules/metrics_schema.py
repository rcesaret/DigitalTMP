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
        no_toast AS (
            SELECT
                tbl.oid, tbl.relname, tbl.reltuples, tbl.relpages, hdr, ma, bs,
                CASE WHEN tbl.reltoastrelid = 0 THEN tbl.relpages
                     ELSE tbl.relpages - toast.relpages
                END AS tbl_pages,
                CASE WHEN tbl.reltoastrelid = 0 THEN 0
                     ELSE toast.relpages
                END AS toast_pages
            FROM pg_class tbl
            JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
            JOIN constants ON true
            LEFT JOIN pg_class toast ON tbl.reltoastrelid = toast.oid
            WHERE ns.nspname = :schema AND tbl.relkind = 'r'
        ),
        table_bytes AS (
            SELECT
                oid, relname, reltuples, relpages, tbl_pages, toast_pages, bs,
                (
                    tbl_pages - (
                        CASE
                            WHEN tbl_pages > 0 AND reltuples > 0
                            THEN
                                (reltuples * (hdr + ma + 4)) /
                                (bs - hdr - ma - 4)
                            ELSE 0
                        END
                    )
                ) * bs AS real_data,
                (
                    CASE
                        WHEN tbl_pages > 0 AND reltuples > 0
                        THEN
                            (
                                tbl_pages -
                                (reltuples * (hdr + ma + 4)) /
                                (bs - hdr - ma - 4)
                            ) *
                            bs *
                            (ma / (hdr + ma + 4))
                        ELSE 0
                    END
                ) AS free_space
            FROM no_toast
        )
        SELECT
            relname AS table_name,
            reltuples::bigint AS row_estimate,
            (
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = relname
            ) AS column_count,
            pg_size_pretty(pg_relation_size(oid)) AS table_size,
            pg_size_pretty(pg_indexes_size(oid)) AS index_size,
            pg_size_pretty(pg_total_relation_size(oid)) AS total_size,
            (
                SELECT COUNT(*)
                FROM pg_index i
                WHERE i.indrelid = oid
            ) AS index_count,
            (real_data + free_space) AS expected_size_b,
            pg_relation_size(oid) AS actual_size_b
        FROM table_bytes
        ORDER BY actual_size_b DESC;
    """
    )

    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection, params={"schema": schema_name})

        # Calculate bloat in Python for clarity
        df["bloat_bytes"] = df["actual_size_b"] - df["expected_size_b"]
        bloat_ratio = df["bloat_bytes"] / df["actual_size_b"].replace(0, 1)
        df["bloat_percent"] = round(bloat_ratio * 100, 2)
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
