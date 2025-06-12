# -*- coding: utf-8 -*-
"""Functions for calculating custom interoperability metrics."""

import logging
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.engine import Engine


def calculate_interoperability_metrics(
    engine: Engine, schema_name: str
) -> Dict[str, Any]:
    """
    Calculates a suite of custom interoperability and complexity metrics.

    - JDI (Join Dependency Index): Measures relational complexity.
    - LIF (Logical Interoperability Factor): Heuristic for join potential.
    - NF (Normalization Factor): Composite heuristic for normalization degree.

    Args:
        engine: A SQLAlchemy engine instance.
        schema_name: The name of the schema to inspect.

    Returns:
        A dictionary containing the calculated interoperability metrics.
    """
    metrics = {"schema_name": schema_name, "jdi": None, "lif": None, "nf": None}

    # --- JDI Calculation ---
    fk_query = text(
        """
        SELECT COUNT(*)
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY' AND table_schema = :schema;
    """
    )
    table_count_query = text(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = :schema AND table_type = 'BASE TABLE';
    """
    )

    try:
        with engine.connect() as connection:
            fk_count = connection.execute(
                fk_query, {"schema": schema_name}
            ).scalar_one()
            table_count = connection.execute(
                table_count_query, {"schema": schema_name}
            ).scalar_one()

        if table_count > 1:
            # Formula: Number of FKs / Max possible non-redundant FKs
            jdi = fk_count / (table_count * (table_count - 1) / 2)
            metrics["jdi"] = round(jdi, 4)
        else:
            metrics["jdi"] = 0.0  # A single table has no internal joins
    except Exception as e:
        logging.error(
            "Failed to calculate JDI for schema '%s': %s",
            schema_name,
            e,
        )

    # --- LIF Calculation ---
    # Heuristic: Count pairs of columns with the same name but in different tables.
    # A more advanced version would check for compatible data types.
    lif_query = text(
        """
        WITH column_counts AS (
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema
            GROUP BY column_name
            HAVING COUNT(DISTINCT table_name) > 1
        )
        SELECT COUNT(*) FROM column_counts;
    """
    )
    try:
        with engine.connect() as connection:
            lif_count = connection.execute(
                lif_query, {"schema": schema_name}
            ).scalar_one()
        metrics["lif"] = lif_count
    except Exception as e:
        logging.error(
            "Failed to calculate LIF for schema '%s': %s",
            schema_name,
            e,
        )

    # --- NF Calculation ---
    # Heuristic: Composite score based on JDI and table count.
    # This formula assumes higher JDI and more tables imply higher normalization.
    if metrics["jdi"] is not None and table_count > 0:
        # Normalize table count to a 0-1 scale (cap at 50 tables for sensitivity)
        normalized_table_score = min(table_count, 50) / 50.0
        # Give more weight to relational complexity (JDI)
        nf = (0.7 * metrics["jdi"]) + (0.3 * normalized_table_score)
        metrics["nf"] = round(nf, 4)

    logging.info(
        "Successfully calculated interoperability metrics for schema '%s'.",
        schema_name,
    )
    return metrics
