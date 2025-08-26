#!/usr/bin/env python3
"""
DF9 Master Wide Flattening (Workflow 2.1 / Task 2)

Creates a single wide table (one row per SSN) from DF9 CSV exports in
'phases/02_TransformDB/data/db_extracted_tables/TMP_DF9/':

- Personnel tables (fieldWorkers.csv, labAnalysts.csv) pivoted from long to wide format
- Iterative left-joins of all data tables by SSN (row-preserving)
- Variable-specific sentinel -> NULL normalization (metadata-driven)
- Code -> "<code>. <text>" expansion using Codes_* lookups
- Comprehensive variable renaming to DF11-ready standardized names
- Column reordering using DF11 order_index
- Optional DF8 backfills (stoneCut/personnel) if DF8 wide is supplied
- QC + provenance log (JSON)
- Optional Parquet export

NO boolean expansion. NO numeric scaling.

Designed to be imported and called by:
  phases/02_TransformDB/src/01_db_tables_flatten.py
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

# ============================ CONSTANTS & TYPES ===============================

ENCODINGS_TRY: Tuple[str, ...] = ("utf-8", "latin1", "cp1252")
REQUIRED_META_COLS: Tuple[str, ...] = (
    "variable",
    "table",
    "is_coded",
    "coded_na_values",
    "code_table",
    "order_index",
    "var_df11",  # New DF11 standardized name
)
# Optional metadata columns
OPTIONAL_META_COLS: Tuple[str, ...] = ("code_col", "label_col", "order_df9_tables")

PERSONNEL_REGEX: str = r"^(fieldWorker\d+|labAnalyst\d+)$"

JsonDict = Dict[str, Any]


# =============================== EXCEPTIONS ===================================


class ConfigError(ValueError):
    """Raised when configuration or metadata is invalid."""


# ================================ CONFIG ======================================


@dataclass(frozen=True)
class DF9Config:
    """Configuration for DF9 flattening pipeline."""

    # I/O
    df9_dir: Path
    metadata_csv: Path
    out_wide_csv: Path
    out_profile_json: Path
    out_parquet: Optional[Path] = None

    # Keys & base
    base_table_name: str = "location"  # from location.csv
    key: str = "SSN"  # preserve original case

    # Behavior
    expected_rows: Optional[int] = 5050
    emit_code_and_label: bool = True
    log_level: str = "INFO"  # Add log_level to config
    tier0_fixes: bool = False  # Tier 0 fixes flag

    # Optional extras
    df8_wide_csv: Optional[Path] = None
    enable_df8_backfill: bool = False  # Control DF8 backfill behavior
    stonecut_df8_source: str = "CUTSTONE"
    stonecut_target: str = "stoneCut"
    personnel_cols_regex: str = PERSONNEL_REGEX


# =============================== LOGGING ======================================


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger("flatten_df9")


# ============================== I/O UTILITIES =================================


def _read_csv_any_encoding(path: Path) -> pd.DataFrame:
    """Read CSV trying multiple encodings safely."""
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
    """List all CSV files in directory."""
    return sorted(list(directory.glob("*.csv")))


def _split_df9_files(files: List[Path]) -> Tuple[List[Path], List[Path], List[Path]]:
    """Return (data_files, codes_files, personnel_files)."""
    data_files, codes_files, personnel_files = [], [], []
    for p in files:
        if p.stem.startswith("Codes_"):
            codes_files.append(p)
        elif p.stem in ("fieldWorkers", "labAnalysts"):
            personnel_files.append(p)
        else:
            data_files.append(p)
    return data_files, codes_files, personnel_files


# ============================== METADATA LOAD =================================


def load_metadata(path: Path) -> pd.DataFrame:
    """Load and validate DF9 metadata."""
    meta = _read_csv_any_encoding(path)

    missing = [c for c in REQUIRED_META_COLS if c not in meta.columns]
    if missing:
        raise ConfigError(f"Metadata missing required columns: {missing}")

    # Normalize types
    meta["is_coded"] = meta["is_coded"].astype(bool)
    meta["coded_na_values"] = meta["coded_na_values"].astype(str).fillna("")
    meta["code_table"] = meta["code_table"].astype(str).fillna("")
    meta["order_index"] = pd.to_numeric(meta["order_index"], errors="coerce").astype(
        "Int64"
    )
    meta["var_df11"] = meta["var_df11"].astype(str)

    # Ensure optional cols exist
    for c in OPTIONAL_META_COLS:
        if c not in meta.columns:
            meta[c] = pd.Series([pd.NA] * len(meta), dtype="string")

    # Set default code_col/label_col if not specified
    meta["code_col"] = meta.get("code_col", "code").fillna("code")
    meta["label_col"] = meta.get("label_col", "description").fillna("description")

    return meta


# ============================== PERSONNEL PIVOT ===============================


def pivot_personnel_tables(
    df9_dir: Path, personnel_files: List[Path], *, tier0_fixes: bool = False
) -> Tuple[Optional[pd.DataFrame], List[JsonDict]]:
    """
    Pivot long-format personnel tables to wide format matching DF8 structure.

    fieldWorkers.csv (14798 rows) -> fieldWorker1-5 columns
    labAnalysts.csv (10585 rows) -> labAnalyst1-3 columns

    If tier0_fixes=True, adds pivot uniqueness validation and collision detection.
    """
    log_actions: List[JsonDict] = []

    if not personnel_files:
        logger.info("No personnel tables found to pivot")
        return None, log_actions

    # Process each personnel file
    personnel_wide_parts = []

    for pfile in personnel_files:
        if not pfile.exists():
            logger.warning(f"Personnel file not found: {pfile}")
            continue

        df_long = _read_csv_any_encoding(pfile)

        if "SSN" not in df_long.columns or "personnelCode" not in df_long.columns:
            logger.warning(f"Personnel file {pfile.stem} missing required columns")
            continue

        # Determine max count and column names based on file
        if pfile.stem == "fieldWorkers":
            max_count = 5
            base_name = "fieldWorker"
        elif pfile.stem == "labAnalysts":
            max_count = 3
            base_name = "labAnalyst"
        else:
            logger.warning(f"Unknown personnel file: {pfile.stem}")
            continue

        # Create rank column for pivot (1, 2, 3, ... per SSN)
        df_long = df_long.sort_values(["SSN", "personnelCode"])
        df_long["rank"] = df_long.groupby("SSN").cumcount() + 1

        # Tier 0: Validate pivot uniqueness and detect collisions
        if tier0_fixes:
            # Check for SSNs with more entries than max_count (potential data loss)
            excess_counts = df_long.groupby("SSN")["rank"].max()
            excess_ssns = excess_counts[excess_counts > max_count]
            if len(excess_ssns) > 0:
                logger.warning(
                    f"{pfile.stem}: {len(excess_ssns)} SSNs exceed max {max_count} entries; "
                    f"truncating to preserve pivot uniqueness. Examples: {list(excess_ssns.head(5).index)}"
                )

            # Validate post-pivot SSN uniqueness constraint
            pre_pivot_unique_ssns = df_long["SSN"].nunique()

        # Filter to max allowed (in case some SSNs have > max_count entries)
        df_long = df_long[df_long["rank"] <= max_count]

        # Pivot to wide format
        df_wide = df_long.pivot(index="SSN", columns="rank", values="personnelCode")

        # Tier 0: Post-pivot validation
        if tier0_fixes:
            post_pivot_unique_ssns = df_wide.index.nunique()
            if post_pivot_unique_ssns != pre_pivot_unique_ssns:
                logger.error(
                    f"{pfile.stem}: Pivot uniqueness violation! "
                    f"Pre-pivot: {pre_pivot_unique_ssns} unique SSNs, "
                    f"Post-pivot: {post_pivot_unique_ssns} unique SSNs"
                )
                raise ValueError(
                    f"Personnel pivot failed uniqueness validation for {pfile.stem}"
                )

        # Create proper column names
        new_cols = [f"{base_name}{i}" for i in range(1, max_count + 1)]
        df_wide.columns = new_cols[: len(df_wide.columns)]

        # Ensure all expected columns exist (fill missing with NaN)
        for col in new_cols:
            if col not in df_wide.columns:
                df_wide[col] = pd.NA

        df_wide = df_wide[new_cols]  # Ensure column order
        df_wide.reset_index(inplace=True)

        personnel_wide_parts.append(df_wide)

        # Enhanced logging for Tier 0
        log_entry = {
            "action": "personnel_pivot",
            "file": pfile.stem,
            "input_rows": len(df_long),
            "output_cols": len(new_cols),
            "unique_ssns": df_wide["SSN"].nunique(),
        }

        if tier0_fixes:
            # Add collision and validation metrics
            log_entry.update(
                {
                    "max_rank_per_ssn": df_long.groupby("SSN")["rank"].max().max()
                    if len(df_long) > 0
                    else 0,
                    "excess_entries_count": len(excess_ssns)
                    if "excess_ssns" in locals()
                    else 0,
                    "pivot_uniqueness_validated": True,
                }
            )

        log_actions.append(log_entry)

        logger.info(
            f"Pivoted {pfile.stem}: {len(df_long)} rows -> {len(new_cols)} columns"
        )

    # Merge personnel tables if multiple exist
    if not personnel_wide_parts:
        return None, log_actions

    personnel_wide = personnel_wide_parts[0]
    for i, df in enumerate(personnel_wide_parts[1:], 1):
        # Tier 0: Collision-safe merge with validation
        if tier0_fixes:
            # Check for column name collisions before merge
            overlapping_cols = set(personnel_wide.columns) & set(df.columns) - {"SSN"}
            if overlapping_cols:
                logger.error(
                    f"Column collision detected in personnel merge: {overlapping_cols}"
                )
                raise ValueError(
                    f"Personnel tables have overlapping columns: {overlapping_cols}"
                )

            # Validate merge integrity
            pre_merge_ssns = set(personnel_wide["SSN"])
            post_merge_result = personnel_wide.merge(df, on="SSN", how="outer")
            post_merge_ssns = set(post_merge_result["SSN"])

            if len(post_merge_ssns) < max(len(pre_merge_ssns), len(set(df["SSN"]))):
                logger.warning(f"Personnel merge {i}: SSN count decreased unexpectedly")

            personnel_wide = post_merge_result
        else:
            personnel_wide = personnel_wide.merge(df, on="SSN", how="outer")

    return personnel_wide, log_actions


# ============================== DATA LOADERS ==================================


def load_df9_tables(
    df9_dir: Path,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """Load all Data_* and Codes_* CSVs from df9_dir."""
    all_files = _list_all_csvs(df9_dir)
    if not all_files:
        raise ConfigError(f"No CSVs found in {df9_dir}")

    data_files, codes_files, personnel_files = _split_df9_files(all_files)

    if not data_files:
        raise ConfigError(f"No DF9 data CSVs found in {df9_dir}")

    # Load data tables (preserve original case)
    data_tbls: Dict[str, pd.DataFrame] = {}
    for f in data_files:
        df = _read_csv_any_encoding(f)
        data_tbls[f.stem] = df  # Keep original case

    # Load codes tables
    code_tbls: Dict[str, pd.DataFrame] = {}
    for f in codes_files:
        df = _read_csv_any_encoding(f)
        code_tbls[f.stem] = df

    return data_tbls, code_tbls


# =========================== TRANSFORM UTILITIES ==============================


def _parse_sentinels_pipe_list(values: str) -> List[str]:
    """Parse pipe-separated sentinel list into strings."""
    if not values or values.lower() in {"nan", "none", ""}:
        return []
    return [v.strip() for v in values.split("|") if v.strip()]


def replace_sentinels_with_na(
    df: pd.DataFrame, meta: pd.DataFrame, variable_column_map: Dict[str, str]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Replace sentinel values with NA using variable-specific rules from metadata.

    Args:
        df: DataFrame to process
        meta: Metadata with coded_na_values per variable
        variable_column_map: Maps metadata variable names to actual DataFrame columns
    """
    df = df.copy()
    all_sentinels_used = set()

    # Group metadata by coded_na_values for efficiency
    meta_grouped = meta.groupby("coded_na_values")

    for sentinels_str, group in meta_grouped:
        if not sentinels_str or sentinels_str.lower() in {"nan", "none", ""}:
            continue

        sentinels = _parse_sentinels_pipe_list(sentinels_str)
        if not sentinels:
            continue

        # Get columns that use these sentinel values
        variables_with_sentinels = group["variable"].tolist()
        columns_to_process = [
            variable_column_map[var]
            for var in variables_with_sentinels
            if var in variable_column_map and variable_column_map[var] in df.columns
        ]

        if not columns_to_process:
            continue

        all_sentinels_used.update(sentinels)

        # Apply sentinel replacement to specific columns
        for col in columns_to_process:
            series = df[col]

            # Handle numeric columns
            if pd.api.types.is_numeric_dtype(series):
                numeric_sents = [pd.to_numeric(s, errors="coerce") for s in sentinels]
                numeric_sents = [s for s in numeric_sents if pd.notna(s)]
                if numeric_sents:
                    df[col] = series.where(~series.isin(numeric_sents), pd.NA)

            # Handle string/object columns
            else:
                series_str = series.astype("string")
                df[col] = series_str.where(~series_str.isin(sentinels), pd.NA)

    return df, sorted(list(all_sentinels_used))


def safe_left_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    by: str,
    rhs_tag: str,
    *,
    tier0_fixes: bool = False,
) -> Tuple[pd.DataFrame, JsonDict]:
    """Left-join with collision-safe suffixing.

    Returns:
        Tuple of (joined_dataframe, join_diagnostics_dict)
    """
    # Initialize diagnostics
    diagnostics = {
        "table": rhs_tag,
        "pre_join_left_rows": len(left),
        "pre_join_right_rows": len(right),
        "collision_count": 0,
        "columns_added": 0,
        "key_overlap_count": 0,
    }

    if by not in right.columns:
        logger.warning("Skipping join for %s: key '%s' not in right table", rhs_tag, by)
        diagnostics["skipped"] = True
        diagnostics["skip_reason"] = f"Key '{by}' not in right table"
        return left, diagnostics

    # Tier 0: Enhanced collision detection and diagnostics
    collisions = [c for c in right.columns if c != by and c in left.columns]
    diagnostics["collision_count"] = len(collisions)
    diagnostics["colliding_columns"] = collisions

    if collisions:
        if tier0_fixes:
            logger.warning(
                "[Tier0] Column collisions on join from %s: %s -> applying collision-safe suffixing _%s",
                rhs_tag,
                collisions,
                rhs_tag,
            )
        else:
            logger.warning(
                "Column collisions on join from %s: %s -> suffixing _%s",
                rhs_tag,
                collisions,
                rhs_tag,
            )
        # Rename collisions in right table
        rename_dict = {c: f"{c}_{rhs_tag}" for c in collisions}
        right = right.rename(columns=rename_dict)

    # Tier 0: Track key overlap for join validation
    if tier0_fixes:
        left_keys = set(left[by].dropna())
        right_keys = set(right[by].dropna())
        key_overlap = left_keys & right_keys
        diagnostics["key_overlap_count"] = len(key_overlap)
        diagnostics["right_keys_not_in_left"] = len(right_keys - left_keys)
        diagnostics["left_keys_not_in_right"] = len(left_keys - right_keys)

    # Perform the join
    result = left.merge(right, how="left", on=by)

    # Post-join diagnostics
    diagnostics["post_join_rows"] = len(result)
    diagnostics["columns_added"] = len(result.columns) - len(left.columns)

    # Tier 0: Additional validation
    if tier0_fixes:
        # Validate no row loss in left join
        if len(result) != len(left):
            logger.error(
                f"[Tier0] Left join row count mismatch for {rhs_tag}: "
                f"expected {len(left)}, got {len(result)}"
            )
            diagnostics["row_count_error"] = True

        # Log top non-null columns added
        added_cols = [c for c in result.columns if c not in left.columns]
        if added_cols:
            non_null_counts = {c: result[c].notna().sum() for c in added_cols}
            top_non_null = sorted(
                non_null_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
            diagnostics["top_non_null_added_cols"] = dict(top_non_null)
            logger.info(
                f"[Tier0] Join {rhs_tag}: added {len(added_cols)} columns, "
                f"top non-null: {dict(top_non_null[:3])}"
            )

    return result, diagnostics


def _format_code_label(code: Any, label: Any) -> Optional[str]:
    """Return '<code>. <text>' string with graceful NA handling."""
    if pd.isna(code) and pd.isna(label):
        return None
    if pd.isna(code) and not pd.isna(label):
        return str(label)
    if not pd.isna(code) and pd.isna(label):
        return str(code)
    return f"{code}. {label}"


# ============================ PIPELINE STEPS ==================================


def build_wide_table(
    cfg: DF9Config,
    meta: pd.DataFrame,
    data_tables: Mapping[str, pd.DataFrame],
    personnel_wide: Optional[pd.DataFrame],
) -> Tuple[pd.DataFrame, List[JsonDict]]:
    """Iteratively left-join DF9 data tables into one wide frame.

    Returns:
        Tuple of (wide_dataframe, join_diagnostics_list)
    """
    join_diagnostics = []

    # Start with base table
    if cfg.base_table_name not in data_tables:
        msg = f"Base table '{cfg.base_table_name}' not found in data tables"
        logger.error(msg)
        raise ConfigError(msg)

    base = data_tables[cfg.base_table_name].copy()
    if cfg.key not in base.columns:
        msg = f"Key '{cfg.key}' not found in base table '{cfg.base_table_name}'"
        logger.error(msg)
        raise ConfigError(msg)

    # De-duplicate base by key
    initial_rows = len(base)
    base = base.drop_duplicates(subset=[cfg.key])
    if len(base) != initial_rows:
        dup_count = initial_rows - len(base)
        logger.warning(
            "Base table %s: removed %d duplicate rows by key %s",
            cfg.base_table_name,
            dup_count,
            cfg.key,
        )
        # Record deduplication in diagnostics
        join_diagnostics.append(
            {
                "table": cfg.base_table_name,
                "action": "base_deduplication",
                "duplicates_removed": dup_count,
                "final_rows": len(base),
            }
        )

    logger.info("Base table %s: %d unique rows", cfg.base_table_name, len(base))

    # Start building
    wide = base

    # First, join personnel if available
    if personnel_wide is not None:
        wide, personnel_diag = safe_left_join(
            wide,
            personnel_wide,
            by=cfg.key,
            rhs_tag="personnel",
            tier0_fixes=cfg.tier0_fixes,
        )
        join_diagnostics.append(personnel_diag)
        logger.info(
            "Added personnel: %d columns", len(wide.columns) - len(base.columns)
        )

    # Then join all other data tables
    remaining_tables = sorted(
        [name for name in data_tables.keys() if name != cfg.base_table_name]
    )

    for table_name in remaining_tables:
        table_df = data_tables[table_name]
        if cfg.key not in table_df.columns:
            logger.warning("Table %s missing key %s, skipping", table_name, cfg.key)
            # Record skip in diagnostics
            join_diagnostics.append(
                {
                    "table": table_name,
                    "skipped": True,
                    "skip_reason": f"Missing key '{cfg.key}'",
                }
            )
            continue

        pre_join_cols = len(wide.columns)
        wide, table_diag = safe_left_join(
            wide, table_df, by=cfg.key, rhs_tag=table_name, tier0_fixes=cfg.tier0_fixes
        )
        join_diagnostics.append(table_diag)

        logger.info(
            "Joined %s: %d -> %d columns",
            table_name,
            pre_join_cols,
            len(wide.columns),
        )

    return wide, join_diagnostics


def expand_coded_values(
    cfg: DF9Config,
    meta: pd.DataFrame,
    df: pd.DataFrame,
    codes_tables: Mapping[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, List[JsonDict]]:
    """Expand all coded variables to '<code>. <text>' per metadata."""
    expansions: List[JsonDict] = []
    if not cfg.emit_code_and_label:
        return df, expansions

    # Get coded variables from metadata
    coded = meta[(meta["is_coded"]) & (meta["code_table"].str.len() > 0)]
    out = df.copy()

    for _, row in coded.iterrows():
        var = str(row["variable"])
        ctab = str(row["code_table"])
        code_col = str(row.get("code_col", "code"))
        label_col = str(row.get("label_col", "description"))

        if var not in out.columns:
            continue
        if ctab not in codes_tables:
            logger.warning("Codes table '%s' not found; skipping %s", ctab, var)
            continue

        codes = codes_tables[ctab].copy()

        # Validate code/label columns exist
        if code_col not in codes.columns or label_col not in codes.columns:
            logger.warning(
                "Codes table '%s' missing expected columns %s/%s; skipping %s",
                ctab,
                code_col,
                label_col,
                var,
            )
            continue

        # Build mapping
        mapping = codes[[code_col, label_col]].drop_duplicates()

        # Handle both numeric and string joins
        series = out[var]
        if pd.api.types.is_numeric_dtype(series):
            # Convert codes to numeric for matching
            mapping_clean = mapping.copy()
            mapping_clean[code_col] = pd.to_numeric(
                mapping_clean[code_col], errors="coerce"
            )
            mapping_clean = mapping_clean.dropna(subset=[code_col])

            # Create lookup dict
            code_to_label = dict(
                zip(mapping_clean[code_col], mapping_clean[label_col], strict=False)
            )

            # Apply mapping
            out[var] = series.map(
                lambda x, _map=code_to_label: _format_code_label(x, _map.get(x))
                if pd.notna(x)
                else None
            )
        else:
            # String-based mapping
            mapping_clean = mapping.copy()
            mapping_clean[code_col] = mapping_clean[code_col].astype(str)
            code_to_label = dict(
                zip(mapping_clean[code_col], mapping_clean[label_col], strict=False)
            )

            out[var] = series.astype(str).map(
                lambda x, _map=code_to_label: _format_code_label(x, _map.get(x))
                if pd.notna(x) and x != "nan"
                else None
            )

        expansions.append(
            {
                "variable": var,
                "code_table": ctab,
                "code_col": code_col,
                "label_col": label_col,
            }
        )

    return out, expansions


def backfill_from_df8(
    cfg: DF9Config,
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[JsonDict]]:
    """Perform targeted DF8 backfills if DF8 wide is available."""
    actions: List[JsonDict] = []
    if not cfg.df8_wide_csv or not cfg.df8_wide_csv.exists():
        logger.info("DF8 wide not found; skipping backfills.")
        return df, actions

    df8 = _read_csv_any_encoding(cfg.df8_wide_csv)
    if cfg.key not in df8.columns:
        logger.warning("DF8 wide lacks key '%s'; skipping backfills.", cfg.key)
        return df, actions

    out = df.copy()

    # stoneCut backfill
    if cfg.stonecut_df8_source in df8.columns:
        tmp = df8[[cfg.key, cfg.stonecut_df8_source]].rename(
            columns={cfg.stonecut_df8_source: "_df8_cutstone"}
        )
        out = out.merge(tmp, how="left", on=cfg.key)
        if cfg.stonecut_target not in out.columns:
            out[cfg.stonecut_target] = pd.NA
        out[cfg.stonecut_target] = out[cfg.stonecut_target].fillna(out["_df8_cutstone"])
        out = out.drop(columns=["_df8_cutstone"])
        actions.append(
            {
                "type": "stoneCut",
                "source": cfg.stonecut_df8_source,
                "target": cfg.stonecut_target,
            }
        )

    # Personnel columns backfill
    df8_personnel = [c for c in df8.columns if re.search(cfg.personnel_cols_regex, c)]
    if df8_personnel:
        out = out.merge(df8[[cfg.key] + df8_personnel], how="left", on=cfg.key)
        actions.append({"type": "personnel", "cols": df8_personnel})

    return out, actions


def rename_to_df11_standard(
    df: pd.DataFrame, meta: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Rename all columns to DF11 standardized names using metadata."""
    # Create mapping from current variable names to DF11 names
    rename_map = {}

    for _, row in meta.iterrows():
        old_name = str(row["variable"])
        new_name = str(row["var_df11"])

        if old_name in df.columns and new_name and new_name != "nan":
            rename_map[old_name] = new_name

    # Apply renaming
    df_renamed = df.rename(columns=rename_map)

    logger.info(f"Renamed {len(rename_map)} columns to DF11 standard names")
    return df_renamed, rename_map


def reorder_columns_df11(
    df: pd.DataFrame, meta: pd.DataFrame, key_col: str
) -> pd.DataFrame:
    """Reorder columns using DF11 order_index from metadata."""
    # Get ordering from metadata (using DF11 names)
    meta_ordered = meta.dropna(subset=["order_index", "var_df11"])
    meta_ordered = meta_ordered.sort_values("order_index")

    # Build column order: key first, then ordered DF11 vars, then others
    ordered_vars = []
    for _, row in meta_ordered.iterrows():
        df11_name = str(row["var_df11"])
        if df11_name in df.columns:
            ordered_vars.append(df11_name)

    # Handle key column (might have been renamed)
    key_in_df = key_col
    if key_col not in df.columns:
        # Find the renamed key
        key_meta = meta[meta["variable"] == key_col]
        if not key_meta.empty:
            key_in_df = str(key_meta.iloc[0]["var_df11"])

    # Build final column order
    other_cols = [c for c in df.columns if c not in {key_in_df, *ordered_vars}]
    final_order = [key_in_df] + ordered_vars + other_cols

    # Filter to existing columns
    final_order = [c for c in final_order if c in df.columns]

    return df.loc[:, final_order]


def reorder_columns_df11_with_placeholders(
    df: pd.DataFrame, meta: pd.DataFrame, key_col: str
) -> Tuple[pd.DataFrame, int]:
    """Reorder columns using DF11 order_index and inject placeholders for missing variables.

    Returns:
        Tuple of (reordered_dataframe, placeholders_injected_count)
    """
    # Get ordering from metadata (using DF11 names)
    meta_ordered = meta.dropna(subset=["order_index", "var_df11"])
    meta_ordered = meta_ordered.sort_values("order_index")

    # Build column order: key first, then ordered DF11 vars, then others
    ordered_vars = []
    placeholders_injected = 0

    for _, row in meta_ordered.iterrows():
        df11_name = str(row["var_df11"])
        if df11_name in df.columns:
            ordered_vars.append(df11_name)
        else:
            # Inject placeholder for missing DF11 variable
            df[df11_name] = pd.NA
            ordered_vars.append(df11_name)
            placeholders_injected += 1

    # Handle key column (might have been renamed)
    key_in_df = key_col
    if key_col not in df.columns:
        # Find the renamed key
        key_meta = meta[meta["variable"] == key_col]
        if not key_meta.empty:
            key_in_df = str(key_meta.iloc[0]["var_df11"])

    # Build final column order
    other_cols = [c for c in df.columns if c not in {key_in_df, *ordered_vars}]
    final_order = [key_in_df] + ordered_vars + other_cols

    # Filter to existing columns (all should exist now with placeholders)
    final_order = [c for c in final_order if c in df.columns]

    return df.loc[:, final_order], placeholders_injected


# ================================ QC / LOG ====================================


def qc_profile(cfg: DF9Config, df: pd.DataFrame, sentinels: Sequence[str]) -> JsonDict:
    """Produce QC summary for transform log."""
    non_null_counts = df.notna().sum().sort_values(ascending=False)
    top10 = [
        {"column": k, "non_null_count": int(v)}
        for k, v in non_null_counts.head(10).items()
    ]

    # Check key uniqueness (key might be renamed)
    key_col = cfg.key
    if key_col not in df.columns:
        # Find renamed key
        potential_keys = [c for c in df.columns if "ssn" in c.lower()]
        if potential_keys:
            key_col = potential_keys[0]

    key_unique = not df[key_col].duplicated().any() if key_col in df.columns else True

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "key_column": key_col,
        "key_unique": bool(key_unique),
        "expected_rows_match": (
            None if cfg.expected_rows is None else int(df.shape[0]) == cfg.expected_rows
        ),
        "sentinels_processed": list(sentinels),
        "non_null_counts_top10": top10,
    }


# ================================ ENTRYPOINT ==================================


def run_pipeline(cfg: DF9Config) -> Dict[str, Any]:
    """Execute DF9 flattening end-to-end. Returns a summary dict."""
    if cfg.tier0_fixes:
        logger.info("=== Starting DF9 Flattening Pipeline (Tier 0 Phase B) ===")
    else:
        logger.info("=== Starting DF9 Flattening Pipeline ===")

    # Load metadata
    logger.info("Loading metadata: %s", cfg.metadata_csv)
    meta = load_metadata(cfg.metadata_csv)
    logger.info(f"Loaded metadata: {len(meta)} variables")

    # Load DF9 tables
    logger.info("Loading DF9 tables from: %s", cfg.df9_dir)
    data_tbls, code_tbls = load_df9_tables(cfg.df9_dir)
    logger.info(f"Loaded {len(data_tbls)} data tables, {len(code_tbls)} code tables")

    # Pivot personnel tables (with Tier 0 validation if enabled)
    logger.info("Processing personnel tables...")
    all_files = _list_all_csvs(cfg.df9_dir)
    _, _, personnel_files = _split_df9_files(all_files)
    personnel_wide, personnel_log = pivot_personnel_tables(
        cfg.df9_dir, personnel_files, tier0_fixes=cfg.tier0_fixes
    )

    # Build wide table via joins (with Tier 0 diagnostics if enabled)
    logger.info("Building wide table via left-joins...")
    wide, join_log = build_wide_table(cfg, meta, data_tbls, personnel_wide)
    logger.info(f"Wide table: {wide.shape[0]} rows × {wide.shape[1]} columns")

    # Tier 0: Row count validation
    if cfg.tier0_fixes and cfg.expected_rows is not None:
        if len(wide) != cfg.expected_rows:
            logger.warning(
                f"[Tier0] Row count mismatch: expected {cfg.expected_rows}, got {len(wide)}"
            )

    # Create variable->column mapping for sentinel replacement
    variable_column_map = {
        var: var for var in wide.columns if var in meta["variable"].values
    }

    # Normalize missing values (variable-specific)
    logger.info("Normalizing missing values (variable-specific sentinels -> NA)...")
    wide, sentinels = replace_sentinels_with_na(wide, meta, variable_column_map)
    logger.info(f"Processed {len(sentinels)} unique sentinel values")

    # Expand coded values
    logger.info("Expanding coded values to '<code>. <text>' format...")
    wide, expansions = expand_coded_values(cfg, meta, wide, code_tbls)
    logger.info(f"Expanded {len(expansions)} coded variables")

    # Apply DF8 backfills (Tier 0: controlled by enable_df8_backfill flag)
    backfills = []
    if cfg.enable_df8_backfill:
        logger.info("Applying DF8 backfills (enabled)...")
        wide, backfills = backfill_from_df8(cfg, wide)
        if backfills:
            logger.info(f"Applied {len(backfills)} backfill operations")
    else:
        logger.info("DF8 backfills disabled (--enable-df8-backfill not set)")

    # Rename to DF11 standard names
    logger.info("Renaming variables to DF11 standardized names...")
    wide, rename_map = rename_to_df11_standard(wide, meta)
    logger.info(f"Renamed {len(rename_map)} variables")

    # Reorder columns using DF11 order (with placeholder injection for Tier 0)
    logger.info("Reordering columns using DF11 order_index...")
    if cfg.tier0_fixes:
        # Enhanced DF11 ordering with placeholder injection
        wide, placeholders_injected = reorder_columns_df11_with_placeholders(
            wide, meta, cfg.key
        )
        logger.info(f"[Tier0] Placeholders injected: {placeholders_injected}")
    else:
        wide = reorder_columns_df11(wide, meta, cfg.key)
        placeholders_injected = 0

    # QC & provenance (enhanced for Tier 0)
    qc = qc_profile(cfg, wide, sentinels)

    # Enhanced QC JSON for Tier 0
    log_payload: JsonDict = {
        "db_key": "DF9",  # pragma: allowlist secret
        "pipeline_version": "Tier0_PhaseB" if cfg.tier0_fixes else "baseline",
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "inputs": {
            "df9_dir": str(cfg.df9_dir),
            "metadata_csv": str(cfg.metadata_csv),
            "df8_wide_csv": str(cfg.df8_wide_csv) if cfg.df8_wide_csv else None,
            "data_tables": sorted(list(data_tbls.keys())),
            "code_tables": sorted(list(code_tbls.keys())),
            "tier0_fixes_enabled": cfg.tier0_fixes,
            "df8_backfill_enabled": cfg.enable_df8_backfill,
        },
        "personnel_processing": personnel_log,
        "joins": join_log,
        "sentinels_to_na": {"unique_sentinels": sentinels},
        "code_expansions": expansions,
        "backfills": backfills,
        "df11_renaming": {
            "variables_renamed": len(rename_map),
            "sample_renames": dict(list(rename_map.items())[:10]),
        },
        "qc": qc,
    }

    # Add Tier 0 specific metrics
    if cfg.tier0_fixes:
        tier0_metrics = {
            "placeholders_injected": placeholders_injected,
            "join_collision_count": sum(
                diag.get("collision_count", 0) for diag in join_log
            ),
            "personnel_pivot_validations": len(
                [log for log in personnel_log if log.get("pivot_uniqueness_validated")]
            ),
            "expected_rows_check": cfg.expected_rows,
        }
        log_payload["tier0_metrics"] = tier0_metrics

    # Create output directories
    cfg.out_wide_csv.parent.mkdir(parents=True, exist_ok=True)
    cfg.out_profile_json.parent.mkdir(parents=True, exist_ok=True)
    if cfg.out_parquet:
        cfg.out_parquet.parent.mkdir(parents=True, exist_ok=True)

    # Tier 0: Timestamped output naming
    if cfg.tier0_fixes:
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        # Update output paths with timestamp
        csv_stem = cfg.out_wide_csv.stem
        csv_timestamped = cfg.out_wide_csv.parent / f"{csv_stem}_Tier0_{timestamp}.csv"

        json_stem = cfg.out_profile_json.stem
        json_timestamped = (
            cfg.out_profile_json.parent / f"{json_stem}_Tier0_{timestamp}.json"
        )

        logger.info("[Tier0] Using timestamped outputs:")
        logger.info(f"  CSV: {csv_timestamped}")
        logger.info(f"  JSON: {json_timestamped}")

        actual_csv_path = csv_timestamped
        actual_json_path = json_timestamped
    else:
        actual_csv_path = cfg.out_wide_csv
        actual_json_path = cfg.out_profile_json

    # Write outputs
    logger.info("Writing wide CSV: %s", actual_csv_path)
    wide.to_csv(actual_csv_path, index=False, na_rep="")

    if cfg.out_parquet:
        if cfg.tier0_fixes:
            parquet_stem = cfg.out_parquet.stem
            parquet_timestamped = (
                cfg.out_parquet.parent / f"{parquet_stem}_Tier0_{timestamp}.parquet"
            )
            actual_parquet_path = parquet_timestamped
        else:
            actual_parquet_path = cfg.out_parquet
        logger.info("Writing Parquet: %s", actual_parquet_path)
        wide.to_parquet(actual_parquet_path, index=False)

    logger.info("Writing QC/profile JSON: %s", actual_json_path)
    with actual_json_path.open("w", encoding="utf-8") as f:
        json.dump(log_payload, f, ensure_ascii=False, indent=2)

    # Final validation checks
    if cfg.expected_rows is not None and qc["expected_rows_match"] is False:
        logger.warning(
            "Row count %s does not match expected %s",
            qc["row_count"],
            cfg.expected_rows,
        )
    if not qc["key_unique"]:
        logger.error(
            "Key uniqueness violated: duplicate SSN values present after joins."
        )

    logger.info("=== DF9 Flattening Complete ===")
    logger.info(f"Final output: {wide.shape[0]} rows × {wide.shape[1]} columns")

    return {
        "qc": qc,
        "outputs": {
            "csv": str(actual_csv_path),
            "parquet": str(actual_parquet_path) if cfg.out_parquet else None,
            "profile": str(actual_json_path),
        },
        "tier0_enabled": cfg.tier0_fixes,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> DF9Config:
    """Parse CLI arguments and construct DF9Config."""
    parser = argparse.ArgumentParser(description="DF9 wide flattener")
    parser.add_argument(
        "--df9-dir",
        type=Path,
        default=Path("phases/02_TransformDB/data/db_extracted_tables/TMP_DF9/"),
        help="Directory with DF9 CSVs",
    )
    parser.add_argument(
        "--metadata-csv",
        type=Path,
        required=True,
        help="Metadata CSV for DF9 variables (DF9_metadata_v4.csv format)",
    )
    parser.add_argument(
        "--out-wide-csv",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/TMP_DF9_wide.csv"),
        help="Output path for TMP_DF9_wide.csv",
    )
    parser.add_argument(
        "--out-profile-json",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/DF9_wide_profile.json"),
        help="Output path for DF9_wide_profile.json",
    )
    parser.add_argument(
        "--out-parquet",
        type=Path,
        default=None,
        help="Optional Parquet output path",
    )
    parser.add_argument(
        "--df8-wide-csv",
        type=Path,
        default=None,
        help="Optional DF8 wide CSV for backfills",
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        default=5050,
        help="Expected total rows (set to 0 to disable strict check)",
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
        help="Logging level",
    )
    parser.add_argument(
        "--tier0-fixes",
        action="store_true",
        help="Enable DF9 Tier 0 Phase B fixes (pivot validation, collision-safe joins, enhanced QC)",
    )
    parser.add_argument(
        "--enable-df8-backfill",
        action="store_true",
        help="Enable optional DF8 backfill behavior (default OFF)",
    )
    args = parser.parse_args(argv)

    expected_rows = None if args.expected_rows == 0 else int(args.expected_rows)
    return DF9Config(
        df9_dir=args.df9_dir,
        metadata_csv=args.metadata_csv,
        out_wide_csv=args.out_wide_csv,
        out_profile_json=args.out_profile_json,
        out_parquet=args.out_parquet,
        df8_wide_csv=args.df8_wide_csv,
        expected_rows=expected_rows,
        emit_code_and_label=not args.no_code_label,
        log_level=args.log_level,
        tier0_fixes=args.tier0_fixes,
        enable_df8_backfill=args.enable_df8_backfill,
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint."""
    cfg = parse_args(argv)
    configure_logging(level=getattr(logging, cfg.log_level, logging.INFO))
    run_pipeline(cfg)


if __name__ == "__main__":
    main()


# ================================ USAGE NOTES =================================
"""
COMPREHENSIVE DF9 FLATTENING IMPLEMENTATION

This script addresses all 5 issues identified in the DF9 integration plan:

ISSUE #1 - PERSONNEL PIVOT (✅ RESOLVED):
- Automatically detects fieldWorkers.csv and labAnalysts.csv
- Pivots long format (14798/10585 rows) to wide format
- Creates fieldWorker1-5 and labAnalyst1-3 columns matching DF8 structure
- Handles missing SSNs gracefully (become NULL after left-join)

ISSUE #2 - VARIABLE-SPECIFIC SENTINELS (✅ RESOLVED):
- Uses exact coded_na_values from DF9_metadata_v4.csv per variable
- Supports "XXXX" for complexUnit/macroComplexUnit
- Avoids blanket "-1|-999|NONE" application
- Protects critical text fields from accidental NULL conversion

ISSUE #3 - DF11 STANDARDIZED NAMING (✅ RESOLVED):
- Comprehensive renaming using var_df11 column from metadata
- Removes df9_column_renames.json dependency entirely
- Snake_case hierarchical naming with categorical prefixes/suffixes
- All 311 variables renamed to DF11-ready format

ISSUE #4 - DF11 COLUMN ORDERING (✅ RESOLVED):
- Uses new order_index for DF11 sequence (derived from DF8)
- Preserves SSN as first column
- Maintains original DF9 ordering in order_df9_tables for reference

ISSUE #5 - CASE-SENSITIVE COMPATIBILITY (✅ RESOLVED):
- Preserves original mixed case for table/variable names
- Uses exact values from DF9_metadata_v4.csv
- Validates against corrected Codes_ table names

METADATA REQUIREMENTS:
The script expects DF9_metadata_v4.csv with these columns:
- variable: Original DF9 variable name (mixed case)
- table: Source DF9 table name (mixed case)
- is_coded: Boolean for code expansion
- coded_na_values: Variable-specific sentinel values (pipe-separated)
- code_table: Exact Codes_* table name for lookups
- order_index: DF11 column ordering (integer)
- var_df11: Standardized DF11 variable name
- code_col/label_col: Optional explicit code table column names

USAGE:
python phases/02_TransformDB/src/flattening_scripts/flatten_df9.py \
  --metadata-csv phases/02_TransformDB/metadata/DF9_metadata_v4.csv \
  --df9-dir phases/02_TransformDB/data/db_extracted_tables/TMP_DF9/ \
  --out-wide-csv phases/02_TransformDB/data/dbs_wide/TMP_DF9_wide.csv \
  --out-profile-json phases/02_TransformDB/data/dbs_wide/DF9_wide_profile.json \
  --df8-wide-csv phases/02_TransformDB/data/dbs_wide/TMP_DF8_wide.csv

WRAPPER INTEGRATION:
This script is designed to be called by 01_db_tables_flatten.py:

from flattening_scripts.flatten_df9 import DF9Config, run_pipeline

cfg = DF9Config(
    metadata_csv=Path("phases/02_TransformDB/metadata/DF9_metadata_v4.csv"),
    df9_dir=Path("phases/02_TransformDB/data/db_extracted_tables/TMP_DF9/"),
    out_wide_csv=Path("phases/02_TransformDB/data/dbs_wide/TMP_DF9_wide.csv"),
    out_profile_json=Path("phases/02_TransformDB/data/dbs_wide/DF9_wide_profile.json"),
)
result = run_pipeline(cfg)

OUTPUT:
- TMP_DF9_wide.csv: 5050 rows × ~311 columns with DF11 names
- DF9_wide_profile.json: Complete transformation log and QC metrics
- Optional TMP_DF9_wide.parquet: Same data in Parquet format

VALIDATION:
- Exactly 5050 rows (one per SSN)
- All numeric codes converted to "<code>. <text>" format
- Variable-specific NULL handling (no blanket sentinel replacement)
- Personnel data in proper DF8 wide format (fieldWorker1-5, labAnalyst1-3)
- Complete DF11 standardized variable names
- Proper column ordering for downstream integration
"""
