#!/usr/bin/env python3
"""
REAN DF2 Wide Flattening — Python Translation

Transforms TMP_REAN_DF2 extracted CSV tables into a single wide-format DataFrame
and CSV, mirroring the provided R script.

Standards:
- Python 3.11+, pathlib.Path, ruff/Black formatting (88 cols)
- Full typing + Google-style docstrings
- Centralized constants (no magic values)
- Robust I/O and structural validation
- Pure, testable transformation helpers

flatten_rean_df2_v2.py — REAN DF2 Wide Flattening (Integrated)

This version synthesizes 2 alternative drafts (Version A and Version B) and brings over proven ideas
from the flatten DF8/DF9/DF10 python scripts:
- Robust CSV reading (multi-encoding attempts, explicit dtype=str at the edge)
- Consistent key handling (string join key to avoid inadvertent coercion loss)
- Collision-safe joins with warnings (from DF9.safe_left_join pattern)
- Metadata-driven rename/reorder identical to the R semantics
- Clean post-processing: personnel boolean mapping; time normalization;
  NA-sentinel handling; meta_has_rean_data flag
- Optional outputs: Parquet and a small QC profile JSON
- Logging & CLI parity with other TMP flatteners
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

# ================================ CONSTANTS ==================================

# Encodings to try for legacy CSVs; fall back to latin1 semantics used in prior versions
ENCODINGS_TRY: Tuple[str, ...] = ("latin1", "utf-8", "cp1252")

# Expected input CSVs in --input-dir (basenames without .csv)
REAN_TABLE_BASENAMES: Tuple[str, ...] = (
    "REAN_00",
    "REAN_01",
    "REAN_02",
    "REAN_03",
    "REAN_04",
    "REAN_05",
    "REAN_06",
    "REAN_07",
    "REAN_08",
    "REAN_09",
    "REAN_10",
    "REAN_aux_obs",
    "REAN_fc_adds",
)

# Metadata in --metadata-dir
FNAME_REAN_DF2_METADATA: str = "REAN_DF2_metadata.csv"

# Output filenames
FNAME_REAN_DF2_WIDE_OUT: str = "TMP_REAN_DF2_wide.csv"
FNAME_REAN_DF2_PROFILE_JSON: str = "TMP_REAN_DF2_wide.profile.json"

# Join key
JOIN_KEY: str = "ssn"

# Sentinels / labels
NEG_ONE_SENTINEL: int = -1
REAN_PCT_NA_DENOMINATOR: int = 230  # aligned with R semantics

# Personnel and time columns (namespace)
PERS_PREFIX: str = "meta_pers_"
COL_TIME_YEAR: str = "meta_time_year"
COL_TIME_YEARMON: str = "meta_time_yearmon"
COL_TIME_MONTH: str = "meta_time_month"


# ================================ CONFIG =====================================


@dataclass(frozen=True)
class IOConfig:
    """I/O configuration for REAN DF2 flattening.

    Attributes:
        input_dir: Directory containing REAN extracted tables as CSV.
        metadata_dir: Directory containing REAN_DF2_metadata.csv.
        output_dir: Directory where outputs will be written.
        out_parquet: Optional Parquet file path.
        out_profile_json: Optional profile JSON path (defaults next to CSV).
    """

    input_dir: Path
    metadata_dir: Path
    output_dir: Path
    out_parquet: Optional[Path] = None
    out_profile_json: Optional[Path] = None

    def resolve_input(self, base_name: str) -> Path:
        return self.input_dir / f"{base_name}.csv"

    def resolve_metadata(self, name: str) -> Path:
        return self.metadata_dir / name

    def resolve_output(self, name: str) -> Path:
        return self.output_dir / name


# =============================== LOGGING =====================================

logger = logging.getLogger(__name__)


def _read_csv_any_encoding(path: Path) -> pd.DataFrame:
    """Read CSV trying several encodings, preferring legacy latin1 semantics."""
    last_err: Optional[Exception] = None
    for enc in ENCODINGS_TRY:
        try:
            # dtype=str at the boundary to keep raw values for later coercions
            return pd.read_csv(path, encoding=enc, dtype=str, low_memory=False)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise ValueError(
        f"Failed reading CSV {path} with encodings {ENCODINGS_TRY}: {last_err}"
    )


def _read_csv_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required CSV not found: {path}")
    df = _read_csv_any_encoding(path)
    if df.shape[0] == 0 and df.shape[1] == 0:
        raise ValueError(f"CSV appears empty or malformed: {path}")
    return df


# ============================= TRANSFORMS ====================================


def _to_numeric(series: pd.Series) -> pd.Series:
    """Safely coerce a Series to numeric, keeping non-numerics as NaN."""
    return pd.to_numeric(series, errors="coerce")


def _read_rean_tables(config: IOConfig) -> Dict[str, pd.DataFrame]:
    """Load all required REAN_* CSVs into a dict keyed by base name."""
    tables: Dict[str, pd.DataFrame] = {}
    for base in REAN_TABLE_BASENAMES:
        path = config.resolve_input(base)
        df = _read_csv_required(path)
        if JOIN_KEY not in df.columns:
            raise ValueError(f"{path.name} is missing required column '{JOIN_KEY}'.")
        # Normalize key to string for robust, lossless joins (B's behavior)
        df[JOIN_KEY] = df[JOIN_KEY].astype(str)
        tables[base] = df
    return tables


def _safe_left_join(
    left: pd.DataFrame, right: pd.DataFrame, on: str, tag: str
) -> pd.DataFrame:
    """Collision-safe left join with warning-based suffixing (inspired by DF9)."""
    if on not in right.columns:
        logger.warning("Skipping join for %s: key '%s' not present in RHS", tag, on)
        return left
    collisions = [c for c in right.columns if c != on and c in left.columns]
    if collisions:
        logger.warning(
            "Column collisions while joining %s: %s -> suffixing _%s",
            tag,
            collisions,
            tag,
        )
        right = right.rename(columns={c: f"{c}_{tag}" for c in collisions})
    return left.merge(right, on=on, how="left")


def _join_rean_tables(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Left-join all REAN_* tables on JOIN_KEY starting from REAN_00."""
    base = tables["REAN_00"].drop_duplicates(subset=[JOIN_KEY]).copy()
    join_order = [n for n in REAN_TABLE_BASENAMES if n != "REAN_00"]
    for name in join_order:
        base = _safe_left_join(base, tables[name], on=JOIN_KEY, tag=name)
    return base


def _apply_metadata_renames_and_order(
    df: pd.DataFrame, metadata: pd.DataFrame
) -> pd.DataFrame:
    """Rename to REAN DF3 names, add missing vars, and reorder per order_index."""
    meta = metadata.copy()

    if not {"variable", "var_rean_df3"}.issubset(meta.columns):
        raise ValueError("Metadata must contain 'variable' and 'var_rean_df3'.")

    # Rename
    rename_df = (
        meta.loc[
            meta["variable"].notna() & meta["var_rean_df3"].notna(),
            ["variable", "var_rean_df3"],
        ]
        .drop_duplicates()
        .query("variable in @df.columns")
    )
    rename_map: Dict[str, str] = dict(
        zip(rename_df["variable"], rename_df["var_rean_df3"], strict=False)
    )
    out = df.rename(columns=rename_map)

    dupes = out.columns[out.columns.duplicated()].unique()
    if len(dupes) > 0:
        raise ValueError(f"Duplicate column names after renaming: {', '.join(dupes)}")

    # Add variables missing in REAN DF2 (var_in_rean_df2 == FALSE)
    if "var_in_rean_df2" in meta.columns:
        norm = (
            meta["var_in_rean_df2"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": True, "false": False, "1": True, "0": False})
        )
        meta = meta.assign(var_in_rean_df2_norm=norm)
        to_add = (
            meta.loc[
                meta["var_in_rean_df2_norm"].isin([False])
                & meta["var_rean_df3"].notna(),
                "var_rean_df3",
            ]
            .astype(str)
            .tolist()
        )
        add_set = [c for c in to_add if c not in out.columns]
        for col in add_set:
            out[col] = np.nan

    # Reorder by order_index (0..n first; NA last), ties by var_rean_df3
    if "order_index" in meta.columns:
        order_meta = (
            meta.loc[meta["var_rean_df3"].notna(), ["var_rean_df3", "order_index"]]
            .drop_duplicates(subset=["var_rean_df3"])
            .assign(
                order_idx_num=lambda d: pd.to_numeric(
                    d["order_index"], errors="coerce"
                ),
                is_nan=lambda d: d["order_index"].isna(),
            )
            .sort_values(
                by=["is_nan", "order_idx_num", "var_rean_df3"], kind="mergesort"
            )
        )
        desired_order = [
            c
            for c in order_meta["var_rean_df3"].astype(str).tolist()
            if c in out.columns
        ]
        others = [c for c in out.columns if c not in desired_order]
        out = out.loc[:, desired_order + others]

    return out


def _cap_personnel_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """Cap `meta_pers_avilaand` to at most 1, if present."""
    out = df.copy()
    col = f"{PERS_PREFIX}avilaand"
    if col in out.columns:
        out[col] = _to_numeric(out[col])
        out[col] = out[col].where(out[col].isna() | (out[col] <= 1), 1)
    return out


def _map_personnel_booleans(df: pd.DataFrame) -> pd.DataFrame:
    """Map all `meta_pers_*` to booleans per R logic (-1→NA, 0→False, 1→True)."""
    out = df.copy()
    pers_cols = [c for c in out.columns if c.startswith(PERS_PREFIX)]
    if not pers_cols:
        return out
    vals = out[pers_cols].apply(_to_numeric, errors="ignore")
    vals = vals.replace(NEG_ONE_SENTINEL, np.nan)
    vals = vals.replace({0.0: False, 1.0: True})
    out[pers_cols] = vals
    return out


def _derive_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Parse, transform, and populate the meta_time_* fields per R logic."""
    out = df.copy()

    # Month from encoded yearmon
    if COL_TIME_YEARMON in out.columns:
        ym_chr = out[COL_TIME_YEARMON].astype(str)
        ym_chr = ym_chr.where(~ym_chr.isin(["-1", "nan", "NaN", "None"]), np.nan)
        month_vals = np.where(
            ym_chr.str.len() == 3,
            pd.to_numeric(ym_chr.str.slice(0, 1), errors="coerce"),
            np.where(
                ym_chr.str.len() == 4,
                pd.to_numeric(ym_chr.str.slice(0, 2), errors="coerce"),
                np.nan,
            ),
        )
        out[COL_TIME_MONTH] = pd.Series(month_vals, index=out.index).astype("Float64")

    # Year: two-digit -> four-digit (+1900), NA/-1 respected
    if COL_TIME_YEAR in out.columns:
        y = pd.to_numeric(out[COL_TIME_YEAR], errors="coerce")
        y = y.where(y != NEG_ONE_SENTINEL, np.nan)
        out[COL_TIME_YEAR] = (y + 1900).astype("Float64")

    # Normalized YYYY-MM
    if {COL_TIME_YEAR, COL_TIME_MONTH}.issubset(out.columns):
        year_i = pd.to_numeric(out[COL_TIME_YEAR], errors="coerce")
        month_i = pd.to_numeric(out[COL_TIME_MONTH], errors="coerce")
        mask_valid = year_i.notna() & month_i.notna()
        norm = pd.Series(np.nan, index=out.index, dtype="object")
        norm.loc[mask_valid] = [
            f"{int(y):04d}-{int(m):02d}"
            for y, m in zip(year_i[mask_valid], month_i[mask_valid], strict=False)
        ]
        out[COL_TIME_YEARMON] = norm

    return out


def _add_meta_has_rean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Compute `meta_has_rean_data`: pct NA < 0.5 using denominator 230 (R script)."""
    out = df.copy()
    na_count = out.isna().sum(axis=1)
    pct_na = na_count / float(REAN_PCT_NA_DENOMINATOR)
    out["meta_has_rean_data"] = pct_na < 0.5
    return out


def _replace_neg1_with_na_in_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Replace -1 values with NA across numeric columns (post-transform)."""
    out = df.copy()
    # Attempt to coerce plausible numeric cols (A's robustness)
    for col in out.columns:
        coerced = _to_numeric(out[col])
        if coerced.notna().any():
            out[col] = coerced
    num_cols = out.select_dtypes(include=["number", "Float64", "Int64"]).columns
    for col in num_cols:
        mask = pd.to_numeric(out[col], errors="coerce") == NEG_ONE_SENTINEL
        out.loc[mask, col] = np.nan
    return out


def _qc_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Tiny QC profile inspired by DF8/DF9/DF10 logs."""
    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "key_unique": bool(df[JOIN_KEY].is_unique) if JOIN_KEY in df.columns else None,
        "missing_cells": int(df.isna().sum().sum()),
    }


# ================================ PIPELINE ===================================


def build_rean_df2_wide(config: IOConfig) -> pd.DataFrame:
    """Run the REAN DF2 flattening pipeline."""
    logger.info("Reading REAN_* input tables...")
    tables = _read_rean_tables(config)

    logger.info("Joining tables by '%s'...", JOIN_KEY)
    wide = _join_rean_tables(tables)

    logger.info("Reading metadata for renaming and ordering...")
    metadata = _read_csv_required(config.resolve_metadata(FNAME_REAN_DF2_METADATA))

    logger.info("Applying metadata-driven renames and ordering...")
    wide = _apply_metadata_renames_and_order(wide, metadata)

    logger.info("Capping personnel indicator...")
    wide = _cap_personnel_indicator(wide)

    logger.info("Mapping personnel columns to booleans...")
    wide = _map_personnel_booleans(wide)

    logger.info("Deriving time fields...")
    wide = _derive_time_fields(wide)

    logger.info("Computing meta_has_rean_data...")
    wide = _add_meta_has_rean_data(wide)

    logger.info("Replacing -1 with NA in numeric columns...")
    wide = _replace_neg1_with_na_in_numeric(wide)

    return wide


def write_outputs(df_wide: pd.DataFrame, config: IOConfig) -> Dict[str, str]:
    """Write main CSV and optional artifacts (parquet, profile json)."""
    outputs: Dict[str, str] = {}
    csv_path = config.resolve_output(FNAME_REAN_DF2_WIDE_OUT)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_wide.to_csv(csv_path, index=False)
    outputs["csv"] = str(csv_path)

    if config.out_parquet:
        config.out_parquet.parent.mkdir(parents=True, exist_ok=True)
        df_wide.to_parquet(config.out_parquet, index=False)
        outputs["parquet"] = str(config.out_parquet)

    profile_path = config.out_profile_json or csv_path.with_suffix(".profile.json")
    profile = _qc_profile(df_wide)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with profile_path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    outputs["profile"] = str(profile_path)

    return outputs


# ================================ CLI ENTRY ==================================


def _parse_cli() -> IOConfig:
    import argparse

    parser = argparse.ArgumentParser(
        description="Flatten TMP_REAN_DF2 tables into TMP_REAN_DF2_wide.csv."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing REAN_* extracted CSV tables.",
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        required=True,
        help="Directory containing REAN_DF2_metadata.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination directory for TMP_REAN_DF2_wide.csv and artifacts.",
    )
    parser.add_argument(
        "--out-parquet",
        type=Path,
        default=None,
        help="Optional Parquet output path.",
    )
    parser.add_argument(
        "--out-profile-json",
        type=Path,
        default=None,
        help="Optional profile JSON output path.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    args = parser.parse_args()
    return IOConfig(
        input_dir=args.input_dir,
        metadata_dir=args.metadata_dir,
        output_dir=args.output_dir,
        out_parquet=args.out_parquet,
        out_profile_json=args.out_profile_json,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    cfg = _parse_cli()
    # Reset level if provided via CLI
    logger.setLevel(logging.getLevelName("INFO"))
    logger.info("Starting REAN DF2 flattening pipeline...")
    df_wide = build_rean_df2_wide(cfg)
    outputs = write_outputs(df_wide, cfg)
    logger.info("REAN DF2 wide written: %s", outputs.get("csv"))
    if "parquet" in outputs:
        logger.info("Parquet written: %s", outputs["parquet"])
    logger.info("Profile written: %s", outputs.get("profile"))


if __name__ == "__main__":
    main()
