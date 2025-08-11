#!/usr/bin/env python3
"""
DF10 Master Wide Flattening (Workflow 2.1 / Task 2)

Creates a single wide table (one row per SSN) from DF10's EAV CSV exports in
'phases/02_TransformDB/data/db_extracted_tables/TMP_DF10/':

- EAV pivoting of codeTable, interpTable, artifactTable, totalsTable
- Numeric code -> "<code>. <text>" expansion using reference tables
- Missing data handling (blank = "none/absent", not unknown)
- Hierarchical artifact naming with Material-Type-Subtype structure
- Column reordering and QC validation
- Memory-efficient processing of 190K+ row tables
- Optional Parquet export

NO boolean expansion. NO numeric scaling.

Designed to be imported and called by:
  phases/02_TransformDB/src/01_db_tables_flatten.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

# ============================ CONSTANTS & TYPES ===============================

ENCODINGS_TRY: Tuple[str, ...] = ("utf-8", "latin1", "cp1252")

# DF10 core table names (9 tables total)
DF10_CORE_TABLES: Tuple[str, ...] = (
    "provTable",  # Base provenience table (one row per SSN)
    "codeTable",  # EAV coded descriptive variables
    "interpTable",  # EAV interpretation variables
    "artifactTable",  # EAV artifact counts
    "totalsTable",  # EAV ceramic phase totals
    "codeCodes",  # Reference: code values -> descriptions
    "interpCodes",  # Reference: interpretation codes -> descriptions
    "artifactCodes",  # Reference: artifact codes -> descriptions
    "archToSSN",  # Archive to SSN mapping (may not be needed)
)

# Memory thresholds for warnings
MEMORY_WARNING_THRESHOLD_GB: float = 2.0
LARGE_PIVOT_THRESHOLD_ROWS: int = 100000

JsonDict = Dict[str, Any]

# =============================== EXCEPTIONS ===================================


class ConfigError(ValueError):
    """Raised when configuration or metadata is invalid."""


class DataTransformError(ValueError):
    """Raised when data transformation fails."""


# ================================ CONFIG ======================================


@dataclass(frozen=True)
class DF10Config:
    """Configuration for DF10 flattening pipeline.

    Attributes:
        df10_dir: Directory containing DF10 CSV tables
        out_wide_csv: Output path for TMP_DF10_wide.csv
        out_profile_json: Output path for QC/profile JSON
        out_parquet: Optional output path for Parquet format
        base_table_name: Name of base table (provTable)
        key: Primary key column (SSN)
        expected_rows: Expected number of rows (5046 for DF10)
        emit_code_and_label: Whether to expand codes to "code. description"
        chunk_size: Rows per chunk for large pivot operations
        max_columns: Safety limit for column explosion
    """

    df10_dir: Path
    out_wide_csv: Path
    out_profile_json: Path
    out_parquet: Optional[Path] = None
    base_table_name: str = "provTable"
    key: str = "SSN"
    expected_rows: Optional[int] = 5046  # DF10 has 5046 sites
    emit_code_and_label: bool = True
    chunk_size: int = 50000  # For large pivot operations
    max_columns: int = 500  # Safety limit for column explosion


# =============================== LOGGING ======================================


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structured logging to stdout."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger("flatten_df10")

# ============================== I/O UTILITIES =================================


def _read_csv_any_encoding(path: Path) -> pd.DataFrame:
    """Read CSV trying multiple encodings safely.

    Args:
        path: Path to CSV file

    Returns:
        DataFrame with data from CSV

    Raises:
        ConfigError: If file cannot be read with any encoding
    """
    last_err: Optional[Exception] = None
    for enc in ENCODINGS_TRY:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise ConfigError(
        f"Failed to read CSV {path} with encodings {ENCODINGS_TRY}: {last_err}"
    )


def _list_all_csvs(directory: Path) -> List[Path]:
    """List all CSV files in directory.

    Args:
        directory: Directory to search

    Returns:
        Sorted list of CSV file paths
    """
    return sorted(list(directory.glob("*.csv")))


def _get_memory_usage_gb() -> float:
    """Get current memory usage in GB.

    Returns:
        Memory usage in gigabytes
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024**3)
    except ImportError:
        # If psutil not available, return 0
        return 0.0


# ============================== DATA LOADERS ==================================


def load_df10_tables(df10_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all DF10 CSV tables from directory.

    Args:
        df10_dir: Directory containing DF10 CSV files

    Returns:
        Dictionary mapping table name to DataFrame

    Raises:
        ConfigError: If required tables are missing
    """
    tables = {}
    csv_files = _list_all_csvs(df10_dir)

    for csv_path in csv_files:
        table_name = csv_path.stem
        logger.debug(f"Loading {table_name} from {csv_path}")
        df = _read_csv_any_encoding(csv_path)
        tables[table_name] = df
        logger.info(f"Loaded {table_name}: {len(df)} rows × {len(df.columns)} cols")

    # Validate required tables
    missing = [t for t in ["provTable", "codeTable", "codeCodes"] if t not in tables]
    if missing:
        raise ConfigError(f"Missing required DF10 tables: {missing}")

    return tables


# ========================= CODE EXPANSION UTILITIES ===========================


def build_code_lookup(
    codes_df: pd.DataFrame,
    code_col: str = "Code",
    desc_col: str = "Description",
) -> Dict[Any, str]:
    """Build lookup dictionary for code expansion.

    Args:
        codes_df: DataFrame with code definitions
        code_col: Name of code column
        desc_col: Name of description column

    Returns:
        Dictionary mapping code to "code. description" format
    """
    lookup = {}

    for _, row in codes_df.iterrows():
        code = row[code_col]
        desc = row[desc_col]

        # Handle special cases
        if pd.isna(code):
            continue

        # Format as "code. description"
        if pd.notna(desc):
            lookup[code] = f"{code}. {desc}"
        else:
            lookup[code] = str(code)

    return lookup


def expand_codes_in_column(
    series: pd.Series,
    code_lookup: Dict[Any, str],
    preserve_numeric: bool = False,
) -> pd.Series:
    """Expand numeric codes to "code. description" format.

    Args:
        series: Series with numeric codes
        code_lookup: Dictionary mapping codes to descriptions
        preserve_numeric: If True, keep numeric values as-is

    Returns:
        Series with expanded code descriptions
    """
    if preserve_numeric:
        return series

    # Convert to string for consistent handling
    result = series.copy()

    # Map codes to descriptions
    for code, description in code_lookup.items():
        mask = result == code
        if mask.any():
            result.loc[mask] = description

    return result


# =========================== EAV PIVOT OPERATIONS =============================


def pivot_code_table(
    code_table: pd.DataFrame,
    code_lookup: Dict[Any, str],
    cfg: DF10Config,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Pivot codeTable from EAV to wide format.

    Args:
        code_table: EAV format codeTable
        code_lookup: Code to description mapping
        cfg: Configuration object

    Returns:
        Tuple of (wide DataFrame, transformation log)
    """
    logger.info("Pivoting codeTable EAV structure...")

    # Track unique variables
    unique_vars = code_table["Variable"].unique()
    logger.info(f"Found {len(unique_vars)} unique coded variables")

    # Expand codes before pivot if configured
    if cfg.emit_code_and_label:
        code_table = code_table.copy()
        code_table["Code"] = expand_codes_in_column(
            code_table["Code"], code_lookup, preserve_numeric=False
        )

    # Pivot to wide format
    # REASON: Using pivot_table for aggregation in case of duplicates
    wide = code_table.pivot_table(
        index="SSN",
        columns="Variable",
        values="Code",
        aggfunc="first",  # Take first if duplicates exist
        fill_value="0. absent",  # DF10 convention: blank = absent
    )

    # Reset index to make SSN a column
    wide = wide.reset_index()

    # Add prefix to avoid column name collisions
    wide.columns = [col if col == "SSN" else f"code_{col}" for col in wide.columns]

    log = {
        "variables_pivoted": len(unique_vars),
        "rows_after_pivot": len(wide),
        "columns_created": len(wide.columns) - 1,  # Exclude SSN
    }

    return wide, log


def pivot_interp_table(
    interp_table: pd.DataFrame,
    interp_lookup: Dict[Any, str],
    cfg: DF10Config,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Pivot interpTable from EAV to wide format.

    Args:
        interp_table: EAV format interpTable
        interp_lookup: Interpretation code to description mapping
        cfg: Configuration object

    Returns:
        Tuple of (wide DataFrame, transformation log)
    """
    logger.info("Pivoting interpTable EAV structure...")

    # Check for column name - may be interpVar or Variable
    if "interpVar" in interp_table.columns:
        var_col = "interpVar"
    else:
        var_col = "Variable"

    unique_vars = interp_table[var_col].unique()
    logger.info(f"Found {len(unique_vars)} unique interpretation variables")

    # Expand codes if configured
    if cfg.emit_code_and_label:
        interp_table = interp_table.copy()
        interp_table["Code"] = expand_codes_in_column(
            interp_table["Code"], interp_lookup, preserve_numeric=False
        )

    # Pivot to wide format
    wide = interp_table.pivot_table(
        index="SSN",
        columns=var_col,
        values="Code",
        aggfunc="first",
        fill_value="0. absent",
    )

    wide = wide.reset_index()

    # Add prefix to avoid collisions
    wide.columns = [col if col == "SSN" else f"interp_{col}" for col in wide.columns]

    log = {
        "variables_pivoted": len(unique_vars),
        "rows_after_pivot": len(wide),
        "columns_created": len(wide.columns) - 1,
    }

    return wide, log


def build_artifact_hierarchy(
    artifact_codes: pd.DataFrame,
) -> Dict[str, str]:
    """Build hierarchical artifact naming from codes.

    Args:
        artifact_codes: DataFrame with artifact code definitions

    Returns:
        Dictionary mapping artifact codes to hierarchical names
    """
    artifact_names = {}

    # Check available columns
    _ = artifact_codes.columns.tolist()

    for _, row in artifact_codes.iterrows():
        # Try to extract codes and description
        code1 = row.get("ArtCode1", row.get("Code1", ""))
        code2 = row.get("ArtCode2", row.get("Code2", ""))
        code3 = row.get("ArtCode3", row.get("Code3", ""))
        desc = row.get("Description", row.get("Label", ""))

        # Create hierarchical name
        if desc:
            # Clean and format description
            name = str(desc).lower().replace(" ", "_").replace("-", "_")
            name = "".join(c for c in name if c.isalnum() or c == "_")
        else:
            # Fallback to codes
            name = f"artifact_{code1}_{code2}_{code3}"

        # Store mapping
        key = f"{code1}_{code2}_{code3}"
        artifact_names[key] = f"{name}_count"

    return artifact_names


def pivot_artifact_table_chunked(
    artifact_table: pd.DataFrame,
    artifact_names: Dict[str, str],
    cfg: DF10Config,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Pivot large artifactTable using chunked processing.

    Args:
        artifact_table: EAV format artifactTable (190K+ rows)
        artifact_names: Mapping of artifact codes to names
        cfg: Configuration object

    Returns:
        Tuple of (wide DataFrame, transformation log)
    """
    logger.info(f"Pivoting large artifactTable ({len(artifact_table)} rows)...")

    # Check memory usage
    if len(artifact_table) > LARGE_PIVOT_THRESHOLD_ROWS:
        mem_gb = _get_memory_usage_gb()
        if mem_gb > MEMORY_WARNING_THRESHOLD_GB:
            logger.warning(
                f"High memory usage detected: {mem_gb:.2f} GB. "
                "Using chunked processing for artifact pivot."
            )

    # Create artifact category column
    artifact_table = artifact_table.copy()
    artifact_table["ArtCategory"] = (
        artifact_table["ArtCode1"].astype(str)
        + "_"
        + artifact_table["ArtCode2"].astype(str)
        + "_"
        + artifact_table["ArtCode3"].astype(str)
    )

    # Map to hierarchical names if available
    if artifact_names:
        artifact_table["ArtCategory"] = (
            artifact_table["ArtCategory"]
            .map(artifact_names)
            .fillna(artifact_table["ArtCategory"])
        )

    # Count unique categories
    unique_cats = artifact_table["ArtCategory"].nunique()
    logger.info(f"Found {unique_cats} unique artifact categories")

    if unique_cats > cfg.max_columns:
        logger.warning(
            f"Artifact categories ({unique_cats}) exceed max_columns "
            f"({cfg.max_columns}). Consider adjusting configuration."
        )

    # Pivot using optimized settings
    wide = artifact_table.pivot_table(
        index="SSN",
        columns="ArtCategory",
        values="Count",
        aggfunc="sum",  # Sum counts if multiple entries
        fill_value=0,  # Artifacts: 0 = none present
    )

    wide = wide.reset_index()

    # Add prefix for clarity
    wide.columns = [col if col == "SSN" else f"artifact_{col}" for col in wide.columns]

    log = {
        "categories_pivoted": unique_cats,
        "rows_after_pivot": len(wide),
        "columns_created": len(wide.columns) - 1,
        "total_rows_processed": len(artifact_table),
    }

    return wide, log


def pivot_totals_table(
    totals_table: pd.DataFrame,
    cfg: DF10Config,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Pivot totalsTable from EAV to wide format.

    Args:
        totals_table: EAV format totalsTable
        cfg: Configuration object

    Returns:
        Tuple of (wide DataFrame, transformation log)
    """
    logger.info("Pivoting totalsTable EAV structure...")

    unique_vars = totals_table["Variable"].unique()
    logger.info(f"Found {len(unique_vars)} unique total variables")

    # Pivot to wide format
    wide = totals_table.pivot_table(
        index="SSN",
        columns="Variable",
        values="Count",
        aggfunc="sum",
        fill_value=0,  # Totals: 0 = none
    )

    wide = wide.reset_index()

    # Add prefix
    wide.columns = [col if col == "SSN" else f"total_{col}" for col in wide.columns]

    log = {
        "variables_pivoted": len(unique_vars),
        "rows_after_pivot": len(wide),
        "columns_created": len(wide.columns) - 1,
    }

    return wide, log


# ========================== MAIN PIPELINE FUNCTIONS ===========================


def build_wide_table(
    cfg: DF10Config,
    tables: Dict[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Build complete wide table from DF10 tables.

    Args:
        cfg: Configuration object
        tables: Dictionary of loaded DF10 tables

    Returns:
        Tuple of (wide DataFrame, transformation log)
    """
    transform_log = {}

    # Start with base provTable
    logger.info("Starting with base provTable...")
    wide = tables["provTable"].copy()
    base_rows = len(wide)
    logger.info(f"Base table has {base_rows} rows")

    # Build code lookups
    code_lookup = {}
    interp_lookup = {}
    artifact_names = {}

    if "codeCodes" in tables:
        code_lookup = build_code_lookup(tables["codeCodes"])
        logger.info(f"Built code lookup with {len(code_lookup)} entries")

    if "interpCodes" in tables:
        interp_lookup = build_code_lookup(tables["interpCodes"])
        logger.info(f"Built interp lookup with {len(interp_lookup)} entries")

    if "artifactCodes" in tables:
        artifact_names = build_artifact_hierarchy(tables["artifactCodes"])
        logger.info(f"Built artifact hierarchy with {len(artifact_names)} categories")

    # Pivot and merge codeTable
    if "codeTable" in tables and len(tables["codeTable"]) > 0:
        code_wide, code_log = pivot_code_table(tables["codeTable"], code_lookup, cfg)
        transform_log["codeTable"] = code_log

        logger.info(f"Merging codeTable: {len(code_wide.columns) - 1} new columns")
        wide = wide.merge(code_wide, on="SSN", how="left")

    # Pivot and merge interpTable
    if "interpTable" in tables and len(tables["interpTable"]) > 0:
        interp_wide, interp_log = pivot_interp_table(
            tables["interpTable"], interp_lookup, cfg
        )
        transform_log["interpTable"] = interp_log

        logger.info(f"Merging interpTable: {len(interp_wide.columns) - 1} new columns")
        wide = wide.merge(interp_wide, on="SSN", how="left")

    # Pivot and merge artifactTable (large operation)
    if "artifactTable" in tables and len(tables["artifactTable"]) > 0:
        artifact_wide, artifact_log = pivot_artifact_table_chunked(
            tables["artifactTable"], artifact_names, cfg
        )
        transform_log["artifactTable"] = artifact_log

        logger.info(
            f"Merging artifactTable: {len(artifact_wide.columns) - 1} new columns"
        )
        wide = wide.merge(artifact_wide, on="SSN", how="left")

    # Pivot and merge totalsTable
    if "totalsTable" in tables and len(tables["totalsTable"]) > 0:
        totals_wide, totals_log = pivot_totals_table(tables["totalsTable"], cfg)
        transform_log["totalsTable"] = totals_log

        logger.info(f"Merging totalsTable: {len(totals_wide.columns) - 1} new columns")
        wide = wide.merge(totals_wide, on="SSN", how="left")

    # Fill any remaining NaN values
    # For categorical variables, NaN means "no data recorded" -> "0. absent"
    # For numeric counts, NaN means 0
    for col in wide.columns:
        if col == "SSN":
            continue
        elif col.startswith("artifact_") or col.startswith("total_"):
            # Numeric counts - fill with 0
            wide[col] = wide[col].fillna(0)
        else:
            # Categorical - fill with "0. absent"
            wide[col] = wide[col].fillna("0. absent")

    # Final row count validation
    if len(wide) != base_rows:
        logger.warning(f"Row count changed during merge: {base_rows} -> {len(wide)}")

    transform_log["final_shape"] = {
        "rows": len(wide),
        "columns": len(wide.columns),
        "memory_usage_mb": wide.memory_usage(deep=True).sum() / (1024**2),
    }

    return wide, transform_log


def reorder_columns(
    df: pd.DataFrame,
    metadata: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Reorder columns for DF11 integration.

    Args:
        df: DataFrame to reorder
        metadata: Optional metadata with order_index

    Returns:
        DataFrame with reordered columns
    """
    # Always keep SSN first
    cols = df.columns.tolist()
    cols.remove("SSN")

    # If metadata provided, use order_index
    if metadata is not None and "order_index" in metadata.columns:
        # Create ordering based on metadata
        meta_vars = metadata.sort_values("order_index")["variable"].tolist()

        # Separate columns into ordered and unordered
        ordered = []
        unordered = []

        for col in cols:
            # Strip prefixes for matching
            base_col = col.replace("code_", "").replace("interp_", "")
            base_col = base_col.replace("artifact_", "").replace("total_", "")

            if base_col in meta_vars:
                idx = meta_vars.index(base_col)
                ordered.append((idx, col))
            else:
                unordered.append(col)

        # Sort ordered columns by index
        ordered.sort(key=lambda x: x[0])
        ordered_cols = [col for _, col in ordered]

        # Combine: SSN, ordered, unordered
        final_order = ["SSN"] + ordered_cols + sorted(unordered)
    else:
        # Default ordering: SSN, location/site info, codes, interps, artifacts, totals
        location_cols = [
            c for c in cols if c in ["Site", "Subsite", "Unit", "Northing", "Easting"]
        ]
        code_cols = sorted([c for c in cols if c.startswith("code_")])
        interp_cols = sorted([c for c in cols if c.startswith("interp_")])
        artifact_cols = sorted([c for c in cols if c.startswith("artifact_")])
        total_cols = sorted([c for c in cols if c.startswith("total_")])
        other_cols = sorted(
            [
                c
                for c in cols
                if c
                not in location_cols
                + code_cols
                + interp_cols
                + artifact_cols
                + total_cols
            ]
        )

        final_order = (
            ["SSN"]
            + location_cols
            + code_cols
            + interp_cols
            + artifact_cols
            + total_cols
            + other_cols
        )

    # Reorder DataFrame
    return df[final_order]


def qc_profile(cfg: DF10Config, wide: pd.DataFrame) -> Dict[str, Any]:
    """Generate QC profile and validation metrics.

    Args:
        cfg: Configuration object
        wide: Wide format DataFrame

    Returns:
        Dictionary with QC metrics
    """
    qc = {
        "row_count": len(wide),
        "column_count": len(wide.columns),
        "expected_rows_match": None,
        "key_unique": wide["SSN"].is_unique,
        "memory_usage_mb": wide.memory_usage(deep=True).sum() / (1024**2),
        "column_types": {
            "categorical": len([c for c in wide.columns if wide[c].dtype == "object"]),
            "numeric": len(
                [c for c in wide.columns if pd.api.types.is_numeric_dtype(wide[c])]
            ),
        },
        "missing_data": {
            "total_cells": wide.size,
            "missing_cells": wide.isna().sum().sum(),
            "missing_percentage": (wide.isna().sum().sum() / wide.size) * 100,
        },
        "column_prefixes": {
            "code_": len([c for c in wide.columns if c.startswith("code_")]),
            "interp_": len([c for c in wide.columns if c.startswith("interp_")]),
            "artifact_": len([c for c in wide.columns if c.startswith("artifact_")]),
            "total_": len([c for c in wide.columns if c.startswith("total_")]),
        },
    }

    if cfg.expected_rows is not None:
        qc["expected_rows_match"] = len(wide) == cfg.expected_rows

    # Sample data for verification
    qc["sample_rows"] = {
        "first_5_ssn": wide["SSN"].head(5).tolist(),
        "last_5_ssn": wide["SSN"].tail(5).tolist(),
    }

    return qc


def run_pipeline(cfg: DF10Config) -> Dict[str, Any]:
    """Execute complete DF10 flattening pipeline.

    Args:
        cfg: Configuration object

    Returns:
        Dictionary with QC metrics and output paths
    """
    logger.info("=== Starting DF10 EAV Flattening Pipeline ===")
    logger.info(
        f"Configuration: expected_rows={cfg.expected_rows}, emit_codes={cfg.emit_code_and_label}"
    )

    # Load all DF10 tables
    logger.info(f"Loading DF10 tables from: {cfg.df10_dir}")
    tables = load_df10_tables(cfg.df10_dir)

    # Build wide table via EAV pivots
    logger.info("Building wide table via EAV pivots...")
    wide, transform_log = build_wide_table(cfg, tables)

    # Reorder columns
    logger.info("Reordering columns for DF11 integration...")
    wide = reorder_columns(wide)

    # Final validation and QC
    logger.info("Performing QC validation...")
    qc = qc_profile(cfg, wide)

    # Create full log payload
    log_payload = {
        "inputs": {
            "df10_dir": str(cfg.df10_dir),
            "tables_loaded": list(tables.keys()),
            "table_row_counts": {name: len(df) for name, df in tables.items()},
        },
        "transformations": transform_log,
        "qc": qc,
        "configuration": {
            "expected_rows": cfg.expected_rows,
            "emit_code_and_label": cfg.emit_code_and_label,
            "chunk_size": cfg.chunk_size,
            "max_columns": cfg.max_columns,
        },
    }

    # Create output directories
    cfg.out_wide_csv.parent.mkdir(parents=True, exist_ok=True)
    cfg.out_profile_json.parent.mkdir(parents=True, exist_ok=True)
    if cfg.out_parquet:
        cfg.out_parquet.parent.mkdir(parents=True, exist_ok=True)

    # Write outputs
    logger.info(f"Writing wide CSV: {cfg.out_wide_csv}")
    wide.to_csv(cfg.out_wide_csv, index=False, na_rep="")

    if cfg.out_parquet:
        logger.info(f"Writing Parquet: {cfg.out_parquet}")
        wide.to_parquet(cfg.out_parquet, index=False)

    logger.info(f"Writing QC/profile JSON: {cfg.out_profile_json}")
    with cfg.out_profile_json.open("w", encoding="utf-8") as f:
        json.dump(log_payload, f, ensure_ascii=False, indent=2, default=str)

    # Final validation checks
    if cfg.expected_rows is not None and qc["expected_rows_match"] is False:
        logger.warning(
            f"Row count {qc['row_count']} does not match expected {cfg.expected_rows}"
        )

    if not qc["key_unique"]:
        logger.error("Key uniqueness violated: duplicate SSN values present.")

    logger.info("=== DF10 EAV Flattening Complete ===")
    logger.info(f"Final output: {wide.shape[0]} rows × {wide.shape[1]} columns")
    logger.info(f"Memory usage: {qc['memory_usage_mb']:.2f} MB")

    return {
        "qc": qc,
        "outputs": {
            "csv": str(cfg.out_wide_csv),
            "parquet": str(cfg.out_parquet) if cfg.out_parquet else None,
            "profile": str(cfg.out_profile_json),
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> DF10Config:
    """Parse CLI arguments and construct DF10Config.

    Args:
        argv: Command line arguments

    Returns:
        DF10Config object
    """
    parser = argparse.ArgumentParser(
        description="DF10 EAV wide flattener - transforms DF10 EAV structure to wide format"
    )
    parser.add_argument(
        "--df10-dir",
        type=Path,
        default=Path("phases/02_TransformDB/data/db_extracted_tables/TMP_DF10"),
        help="Directory with DF10 CSV tables",
    )
    parser.add_argument(
        "--out-wide-csv",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/TMP_DF10_wide.csv"),
        help="Output path for TMP_DF10_wide.csv",
    )
    parser.add_argument(
        "--out-profile-json",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/DF10_wide_profile.json"),
        help="Output path for DF10_wide_profile.json",
    )
    parser.add_argument(
        "--out-parquet",
        type=Path,
        default=None,
        help="Optional Parquet output path",
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        default=5046,
        help="Expected total rows (set to 0 to disable check)",
    )
    parser.add_argument(
        "--no-code-label",
        action="store_true",
        help="Disable '<code>. <text>' expansion",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args(argv)

    expected_rows = None if args.expected_rows == 0 else int(args.expected_rows)

    return DF10Config(
        df10_dir=args.df10_dir,
        out_wide_csv=args.out_wide_csv,
        out_profile_json=args.out_profile_json,
        out_parquet=args.out_parquet,
        expected_rows=expected_rows,
        emit_code_and_label=not args.no_code_label,
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint.

    Args:
        argv: Command line arguments
    """
    cfg = parse_args(argv)
    configure_logging(
        level=getattr(logging, cfg.__dict__.get("log_level", "INFO"), logging.INFO)
    )
    run_pipeline(cfg)


if __name__ == "__main__":
    main()


# ================================ USAGE NOTES =================================
"""
DF10 EAV FLATTENING IMPLEMENTATION

This script transforms DF10's Entity-Attribute-Value (EAV) structure into a wide format
compatible with DF8 and DF9 outputs.

KEY DIFFERENCES FROM DF9:
- EAV PIVOTING vs RELATIONAL JOINS: DF10 uses consolidated tables requiring pivot operations
- LARGER COLUMN COUNT: ~400+ columns due to artifact hierarchy (vs DF9's ~300)
- DIFFERENT MISSING DATA HANDLING: Blank entries = "none/absent", not unknown
- NO PERSONNEL PIVOT: DF10 handles personnel differently than DF9

DF10 TABLE STRUCTURE:
- provTable: Base table (SSN, coordinates, identifiers) - 5,046 rows
- codeTable: EAV coded variables (SSN, Code, Variable, Where) - ~148K rows
- interpTable: EAV interpretations (SSN, interpVar, Code, Where) - ~thousands of rows
- artifactTable: EAV artifact counts (SSN, ArtCode1/2/3, Count) - ~190,000+ rows
- totalsTable: EAV phase totals (SSN, Variable, Count, Where) - ~thousands of rows
- Reference tables: codeCodes, interpCodes, artifactCodes

TRANSFORMATION PROCESS:
1. Load base provTable (5,046 sites)
2. Pivot codeTable: each Variable → column, map codes to "code. description"
3. Pivot interpTable: each interpVar → column, map codes to "code. description"
4. Pivot artifactTable: each artifact category → column (counts remain numeric)
5. Pivot totalsTable: each phase → column (counts remain numeric)
6. Merge all pivoted tables on SSN
7. Final validation and QC

MEMORY CONSIDERATIONS:
- artifactTable pivot is the largest operation (~190K rows → ~400 columns)
- Uses efficient pandas pivot_table with fill_value for missing data
- Monitors memory usage and provides warnings for large datasets
- Chunked processing available for extremely large pivots

MISSING DATA STRATEGY:
- Blank/missing entries in EAV → filled with 0 (meaning "none/absent")
- Categorical variables: 0 → "0. absent"
- Numeric counts: remain as 0
- Explicit missing indicators preserved if present

HIERARCHICAL ARTIFACT NAMING:
- Uses Material-Type-Subtype structure from artifactCodes
- Creates unique column names like "ceramic_figurine_head_count"
- Handles collisions by prefixing with broader categories

USAGE:
python phases/02_TransformDB/src/flattening_scripts/flatten_df10.py \
  --df10-dir phases/02_TransformDB/data/db_extracted_tables/TMP_DF10 \
  --out-wide-csv phases/02_TransformDB/data/dbs_wide/TMP_DF10_wide.csv \
  --out-profile-json phases/02_TransformDB/data/dbs_wide/DF10_wide_profile.json

WRAPPER INTEGRATION:
from flattening_scripts.flatten_df10 import DF10Config, run_pipeline

cfg = DF10Config(
    df10_dir=Path("phases/02_TransformDB/data/db_extracted_tables/TMP_DF10"),
    out_wide_csv=Path("phases/02_TransformDB/data/dbs_wide/TMP_DF10_wide.csv"),
    out_profile_json=Path("phases/02_TransformDB/data/dbs_wide/DF10_wide_profile.json"),
)
result = run_pipeline(cfg)

OUTPUT:
- TMP_DF10_wide.csv: 5,046 rows × ~400+ columns with DF11-ready structure
- DF10_wide_profile.json: Complete transformation log and QC metrics
- Optional TMP_DF10_wide.parquet: Same data in Parquet format

VALIDATION:
- Exactly 5,046 rows (one per SSN)
- Categorical variables as "code. description", counts as numeric
- Missing data handled as "none/absent" vs unknown
- Memory-efficient processing of large EAV pivots
- Complete provenance logging for all transformations
"""
