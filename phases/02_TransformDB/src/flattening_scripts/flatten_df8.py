#!/usr/bin/env python3
"""
DF8 Master Wide Flattening (Workflow 2.1 / Task 2)

Reconstructs and transforms the fragmented DF8 dataset into a single, wide-format
table ready for DF11 integration. This script performs the following key steps:

1.  **Multi-File Assembly**: Merges all 27 source CSVs from the DF8 extracted
    data directory into a single DataFrame.
2.  **Code Expansion**: Translates numeric codes to human-readable text in the
    format "<code>. <text>" using mappings from an external JSON file.
3.  **NULL Normalization**: Converts legacy sentinel values (-1 and -999) into
    proper NULL values based on variable-specific rules from metadata.
4.  **Special Transformations**: Applies DF8-specific logic, such as scaling
    coordinate values and cleaning site identifiers.
5.  **Schema Standardization**: Renames all variables to their final DF11-standardized
    names and reorders all columns to match the final DF11 layout, driven by a
    comprehensive metadata file.

This script is designed to be called by the master wrapper script:
`phases/02_TransformDB/src/01_db_tables_flatten.py`
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

# ============================ CONSTANTS & TYPES ===============================

ENCODINGS_TRY: Tuple[str, ...] = ("utf-8", "latin1", "cp1252")
REQUIRED_META_COLS: Tuple[str, ...] = (
    "variable",
    "is_coded",
    "coded_na_values",
    "order_index",
    "var_df11",
)

JsonDict = Dict[str, Any]
CodeMap = Dict[str, Dict[int, str]]

# =============================== EXCEPTIONS ===================================


class ConfigError(ValueError):
    """Raised when configuration or metadata is invalid."""


class DataTransformError(ValueError):
    """Raised when a data transformation step fails."""


# ================================ CONFIG ======================================


@dataclass(frozen=True)
class DF8Config:
    """Configuration for the DF8 flattening pipeline."""

    df8_dir: Path
    metadata_csv: Path
    code_map_json: Path
    out_wide_csv: Path
    out_profile_json: Path
    out_parquet: Optional[Path] = None
    key: str = "ssn"  # Key after cleaning column names
    expected_rows: Optional[int] = 5050
    log_level: str = "INFO"
    tier0_fixes: bool = False


# =============================== LOGGING ======================================


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger for console output.

    Args:
        level: The logging level to set (e.g., logging.INFO).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger("flatten_df8")


# ============================== I/O & METADATA ================================


def _read_csv_any_encoding(path: Path) -> pd.DataFrame:
    """
    Read a CSV file, trying multiple common encodings.

    Args:
        path: The path to the CSV file.

    Returns:
        A pandas DataFrame with the content of the file.

    Raises:
        ConfigError: If the file cannot be read with any of the attempted encodings.
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


def load_metadata(path: Path) -> pd.DataFrame:
    """
    Load and validate the DF8 metadata file.

    Args:
        path: The path to the metadata CSV file.

    Returns:
        A validated and type-corrected pandas DataFrame of the metadata.

    Raises:
        ConfigError: If the metadata is missing required columns.
    """
    meta = _read_csv_any_encoding(path)

    missing = [c for c in REQUIRED_META_COLS if c not in meta.columns]
    if missing:
        raise ConfigError(f"Metadata is missing required columns: {missing}")

    # Note: default parsing leaves as provided; normalization occurs under --tier0-fixes
    meta["is_coded"] = meta["is_coded"].astype(str)
    meta["coded_na_values"] = meta["coded_na_values"].astype(str).fillna("")
    meta["order_index"] = pd.to_numeric(meta["order_index"], errors="coerce").astype(
        "Int64"
    )
    meta["var_df11"] = meta["var_df11"].astype(str)

    return meta


def _normalize_bool_series(s: pd.Series) -> pd.Series:
    """Normalize a heterogeneous boolean-like series (strings/ints/bools) to True/False.

    Accepts case-insensitive tokens: true/1/yes/y/t -> True; false/0/no/n/f/""/nan -> False.
    """
    true_set = {"true", "1", "yes", "y", "t"}
    false_set = {"false", "0", "no", "n", "f", "", "nan"}

    def _coerce(v: Any) -> bool:
        if pd.isna(v):
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            try:
                return bool(int(v))
            except Exception:  # noqa: BLE001
                return False
        sval = str(v).strip().lower()
        if sval in true_set:
            return True
        if sval in false_set:
            return False
        # default safe fallback
        return False

    return s.map(_coerce)


def load_code_mappings_from_json(path: Path) -> CodeMap:
    """
    Load and process code mappings from the external JSON file.

    Args:
        path: The path to the code mapping JSON file.

    Returns:
        A dictionary mapping variable names to their code translation dictionaries,
        with numeric codes correctly cast as integers.

    Raises:
        ConfigError: If the JSON file cannot be found, read, or parsed.
    """
    logger.info("Stage 2: Loading code mappings from JSON: %s", path)
    try:
        with path.open("r", encoding="utf-8") as f:
            raw_maps = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ConfigError(f"Failed to load or parse code map JSON: {e}") from e

    processed_maps: CodeMap = {}
    for var, mapping in raw_maps.items():
        try:
            # Convert string keys from JSON to integers for mapping
            processed_maps[var] = {int(k): v for k, v in mapping.items()}
        except ValueError:
            logger.warning(
                "Could not convert all keys to int for var '%s'. Keeping as string.",
                var,
            )
            processed_maps[var] = mapping  # Fallback for non-integer codes

    logger.info("Loaded and processed mappings for %d variables.", len(processed_maps))
    return processed_maps


# ============================ PIPELINE STEPS ==================================


def assemble_df8_tables(cfg: DF8Config) -> pd.DataFrame:
    """
    Stage 1: Discover and merge all DF8 source CSVs into a single DataFrame.

    This function replicates the logic from the `DF8_wide.Rmd` script, which
    involves loading all tables and performing a sequential outer merge to
    reconstruct the full dataset. It also cleans column names for consistency.

    Args:
        cfg: The configuration object specifying the input directory and merge key.

    Returns:
        A single pandas DataFrame containing the merged and cleaned data.
    """
    logger.info("Stage 1: Assembling DF8 from source CSVs...")
    csv_files = sorted(list(cfg.df8_dir.glob("*.csv")))
    if not csv_files:
        raise ConfigError(f"No source CSVs found in directory: {cfg.df8_dir}")

    logger.info(f"Found {len(csv_files)} source files to assemble.")
    dataframes = {p.stem: _read_csv_any_encoding(p) for p in csv_files}

    # Use 'ssn_master' as the base if it exists, otherwise use a stable sort order
    file_order = sorted(dataframes.keys())
    if "ssn_master" in file_order:
        base_table_name = "ssn_master"
    else:
        # Fallback to a predictable base if ssn_master is missing
        base_table_name = file_order[0]

    file_order.remove(base_table_name)
    file_order.insert(0, base_table_name)

    logger.info(f"Using '{base_table_name}' as the base for merging.")
    # The primary key must be consistent for merging (match actual CSV column names)
    merge_key_original_case = "ssn"
    merged_df = dataframes[base_table_name]

    for table_name in file_order[1:]:
        if merge_key_original_case in dataframes[table_name].columns:
            merged_df = pd.merge(
                merged_df,
                dataframes[table_name],
                on=merge_key_original_case,
                how="outer",
                suffixes=(None, f"_{table_name}"),
            )
        else:
            logger.warning(
                "Table '%s' is missing the merge key '%s' and was skipped.",
                table_name,
                merge_key_original_case,
            )

    # Clean column names to lowercase for matching with metadata `variable` field
    merged_df.columns = merged_df.columns.str.lower()

    if cfg.expected_rows and len(merged_df) != cfg.expected_rows:
        logger.warning(
            "Assembled table has %d rows, but expected %d.",
            len(merged_df),
            cfg.expected_rows,
        )

    logger.info("Assembly complete. Resulting DataFrame shape: %s", merged_df.shape)
    return merged_df


def replace_sentinels_with_na(
    df: pd.DataFrame, meta: pd.DataFrame
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Stage 3: Replace sentinel values with NA using variable-specific rules.

    Args:
        df: The DataFrame to process.
        meta: The metadata defining sentinel values for each variable.

    Returns:
        A tuple containing the transformed DataFrame and a list of all
        sentinel values that were processed.
    """
    logger.info("Stage 3: Normalizing missing values (sentinels -> NA)...")
    df = df.copy()
    all_sentinels = set()

    for _, row in meta.iterrows():
        var = row["variable"]
        if var not in df.columns:
            continue

        sentinels_str = row["coded_na_values"]
        if not sentinels_str or pd.isna(sentinels_str):
            continue

        sentinels = [s.strip() for s in sentinels_str.split("|")]
        all_sentinels.update(sentinels)

        numeric_sents = (
            pd.to_numeric(pd.Series(sentinels), errors="coerce").dropna().tolist()
        )
        df[var] = df[var].replace(numeric_sents, pd.NA)

    logger.info("Processed sentinels: %s", sorted(list(all_sentinels)))
    return df, sorted(list(all_sentinels))


def expand_coded_values(
    df: pd.DataFrame,
    meta: pd.DataFrame,
    code_maps: CodeMap,
    *,
    format_code_text: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Stage 4: Apply code mappings to transform numeric codes into text.

    Args:
        df: The DataFrame to transform.
        meta: Metadata identifying which variables are coded.
        code_maps: The dictionary of code mappings.

    Returns:
        The transformed DataFrame with human-readable text in coded columns.
    """
    logger.info("Stage 4: Expanding coded variables to text...")
    df = df.copy()
    coded_vars_count = 0
    unmapped_counts: Dict[str, int] = {}
    for _, row in meta.iterrows():
        if bool(row["is_coded"]) and row["variable"] in df.columns:
            var = row["variable"]
            if var in code_maps:
                if format_code_text:
                    mapping = code_maps[var]

                    # Build "<code>. <text>" with fallback to raw code when unmapped
                    def _fmt(val: Any, _mapping=mapping) -> Any:
                        if pd.isna(val):
                            return pd.NA
                        try:
                            ival = int(val)
                        except Exception:  # noqa: BLE001
                            # non-integer code, attempt direct lookup
                            txt = _mapping.get(val)
                            if txt is not None:
                                # Check if mapping already includes code prefix
                                return (
                                    txt
                                    if txt.startswith(f"{val}. ")
                                    else f"{val}. {txt}"
                                )
                            return str(val)
                        txt = _mapping.get(ival)
                        if txt is not None:
                            # Check if mapping already includes code prefix
                            return (
                                txt if txt.startswith(f"{ival}. ") else f"{ival}. {txt}"
                            )
                        return str(ival)

                    ser = df[var].apply(_fmt).astype("string")
                    # Count unmapped: values without the literal ". " delimiter and non-NA
                    unmapped = ser.notna() & (~ser.str.contains(". ", regex=False))
                    unmapped_counts[var] = int(unmapped.sum())
                    df[var] = ser
                else:
                    # Use .map() for efficient replacement on the series
                    df[var] = df[var].map(code_maps[var]).astype("string")
                coded_vars_count += 1
            else:
                logger.debug("No code map found for coded variable: %s", var)

    logger.info("Applied code mappings for %d variables.", coded_vars_count)
    return df, unmapped_counts


def apply_special_transformations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 5: Apply DF8-specific data transformations like coordinate scaling.

    Args:
        df: The DataFrame to transform.

    Returns:
        The transformed DataFrame.
    """
    logger.info("Stage 5: Applying DF8-specific transformations...")
    df = df.copy()

    if "northing" in df.columns:
        df["northing"] *= 10
    if "easting" in df.columns:
        df["easting"] *= 10
    logger.info("Applied x10 scaling to coordinate variables.")

    if "site" in df.columns:
        df["site"] = df["site"].str.replace(" ", "", regex=False).astype("string")
        logger.info("Removed spaces from SITE identifier column.")

    return df


def rename_and_reorder_df11(
    df: pd.DataFrame,
    meta: pd.DataFrame,
    key_col: str,
    *,
    inject_placeholders: bool = False,
) -> Tuple[pd.DataFrame, int]:
    """
    Stage 6: Rename and reorder columns to match the DF11 specification.

    Args:
        df: The DataFrame to finalize.
        meta: Metadata containing the `var_df11` names and `order_index`.
        key_col: The name of the primary key column after cleaning.

    Returns:
        The finalized DataFrame with standardized names and order.
    """
    logger.info("Stage 6: Renaming and reordering columns for DF11 compliance...")
    rename_map = (
        meta.dropna(subset=["var_df11"]).set_index("variable")["var_df11"].to_dict()
    )
    df = df.rename(columns=rename_map)
    logger.info("Renamed %d columns to DF11 standard.", len(rename_map))

    meta_ordered = meta.dropna(subset=["order_index", "var_df11"]).sort_values(
        "order_index"
    )

    def _unique_preserve(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in seq:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    all_df11_unique = _unique_preserve([str(v) for v in meta_ordered["var_df11"]])
    ordered_vars = [v for v in all_df11_unique if v in df.columns]

    injected_count = 0
    if inject_placeholders:
        # Ensure all DF11 variables from metadata exist; add as NA if missing, vectorized
        missing = [v for v in all_df11_unique if v not in df.columns]
        if missing:
            na_frame = pd.DataFrame(
                {v: pd.Series(pd.NA, index=df.index) for v in missing}
            )
            df = pd.concat([df, na_frame], axis=1)
        injected_count = len(missing)
        # After injection, refresh ordered_vars from unique set
        ordered_vars = [v for v in all_df11_unique if v in df.columns]

    key_col_df11 = rename_map.get(key_col, key_col)

    # Avoid duplicating the key in the ordered_vars list
    ordered_vars = [v for v in ordered_vars if v != key_col_df11]

    # Filter out original variable names that have been renamed to prevent duplicates
    renamed_originals = set(rename_map.keys())  # Original DF8 names that were renamed

    # Also filter out unmapped columns that don't follow DF11 naming patterns
    # These are likely intermediate artifacts that shouldn't be in final output
    def is_valid_df11_column(col_name: str) -> bool:
        """Check if column follows DF11 naming pattern or is a legitimate unmapped column."""
        # DF11 pattern columns
        if col_name.startswith(("meta_", "arch_", "art_", "env_")):
            return True
        # Modern variables that follow expected naming (start with 'mod_')
        if col_name.startswith("mod_"):
            return True
        return False

    other_cols = sorted(
        [
            c
            for c in df.columns
            if c not in set(ordered_vars + [key_col_df11])
            and c not in renamed_originals
            and is_valid_df11_column(c)
        ]
    )

    # Build final order and de-duplicate defensively while preserving order
    tmp_order = [key_col_df11] + ordered_vars + other_cols
    seen_order = set()
    final_order: List[str] = []
    for c in tmp_order:
        if c not in seen_order:
            seen_order.add(c)
            final_order.append(c)
    final_order_existing = [c for c in final_order if c in df.columns]

    logger.info("Reordered columns based on DF11 specification.")
    return df[final_order_existing], injected_count


def qc_profile(
    cfg: DF8Config,
    df: pd.DataFrame,
    sentinels: List[str],
    *,
    placeholders_injected: int = 0,
    unmapped_code_counts: Optional[Dict[str, int]] = None,
) -> JsonDict:
    """
    Generate a QC and validation summary for the transformation log.

    Args:
        cfg: The configuration object.
        df: The final transformed DataFrame.
        sentinels: The list of processed sentinel values.

    Returns:
        A dictionary containing key quality control metrics.
    """
    key_col_df11 = "meta_id_ssn"
    if key_col_df11 not in df.columns:
        key_col_df11 = cfg.key  # Fallback if rename failed

    # Robust key uniqueness: handle potential duplicate column labels by selecting as DataFrame
    # and checking row-level duplicates on the key column.
    if key_col_df11 in df.columns:
        key_frame = df.loc[:, [key_col_df11]]  # always a DataFrame
        dup_count = int(key_frame.duplicated(subset=[key_col_df11], keep=False).sum())
        key_unique = dup_count == 0
    else:
        dup_count = 0
        key_unique = False

    # Header duplicate metrics
    name_counts = Counter(df.columns)
    header_dupes = {k: int(v) for k, v in name_counts.items() if v > 1}
    header_dupe_names_count = len(header_dupes)
    # All-NA columns count (helps identify placeholder-only columns)
    all_na_columns_count = int(df.isna().all(axis=0).sum())

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "key_unique": key_unique,
        "expected_rows_match": (
            None if cfg.expected_rows is None else int(df.shape[0]) == cfg.expected_rows
        ),
        "sentinels_processed": sentinels,
        "key_duplicate_count": int(dup_count),
        "placeholders_injected": int(placeholders_injected),
        "unmapped_code_total": int(sum((unmapped_code_counts or {}).values())),
        "unmapped_code_counts": (unmapped_code_counts or {}),
        "header_duplicate_names_count": int(header_dupe_names_count),
        "header_duplicate_name_counts": header_dupes,
        "all_na_columns_count": int(all_na_columns_count),
    }


def run_pipeline(cfg: DF8Config) -> Dict[str, Any]:
    """
    Execute the complete DF8 flattening and transformation pipeline.

    Args:
        cfg: The configuration object for the pipeline.

    Returns:
        A dictionary containing QC results and output file paths.
    """
    df = assemble_df8_tables(cfg)
    code_maps = load_code_mappings_from_json(cfg.code_map_json)
    meta = load_metadata(cfg.metadata_csv)
    if cfg.tier0_fixes:
        # Normalize is_coded only under gated Phase B
        meta["is_coded"] = _normalize_bool_series(meta["is_coded"]).astype(bool)

    df, sentinels = replace_sentinels_with_na(df, meta)
    df, unmapped = expand_coded_values(
        df, meta, code_maps, format_code_text=cfg.tier0_fixes
    )
    df = apply_special_transformations(df)
    df, injected_count = rename_and_reorder_df11(
        df, meta, cfg.key, inject_placeholders=cfg.tier0_fixes
    )

    qc = qc_profile(
        cfg,
        df,
        sentinels,
        placeholders_injected=injected_count,
        unmapped_code_counts=unmapped,
    )
    log_payload: JsonDict = {
        "inputs": {
            "df8_dir": str(cfg.df8_dir),
            "metadata_csv": str(cfg.metadata_csv),
            "code_map_json": str(cfg.code_map_json),
        },
        "qc": qc,
    }

    logger.info("Writing output files...")
    cfg.out_wide_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.out_wide_csv, index=False, na_rep="")
    logger.info("Successfully wrote wide CSV to: %s", cfg.out_wide_csv)

    if cfg.out_parquet:
        cfg.out_parquet.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cfg.out_parquet, index=False)
        logger.info("Successfully wrote Parquet to: %s", cfg.out_parquet)

    cfg.out_profile_json.parent.mkdir(parents=True, exist_ok=True)
    with cfg.out_profile_json.open("w", encoding="utf-8") as f:
        json.dump(log_payload, f, ensure_ascii=False, indent=2)
    logger.info("Successfully wrote profile JSON to: %s", cfg.out_profile_json)

    logger.info("DF8 flattening pipeline complete.")
    return {"qc": qc, "outputs": {"csv": str(cfg.out_wide_csv)}}


def parse_args(argv: Optional[Sequence[str]] = None) -> DF8Config:
    """
    Parse command-line arguments and construct the DF8Config object.

    Args:
        argv: A sequence of string arguments (e.g., from sys.argv).

    Returns:
        A validated DF8Config object.
    """
    parser = argparse.ArgumentParser(description="DF8 wide flattener.")
    parser.add_argument(
        "--df8-dir",
        type=Path,
        default=Path("phases/02_TransformDB/data/db_extracted_tables/TMP_DF8/"),
        help="Directory with all 27 DF8 source CSVs.",
    )
    parser.add_argument(
        "--metadata-csv",
        type=Path,
        required=True,
        help="Metadata CSV for DF8 variables.",
    )
    parser.add_argument(
        "--code-map-json",
        type=Path,
        default=Path("phases/02_TransformDB/metadata/df8_code_mapping_dict.json"),
        help="JSON file with DF8 code-to-text mappings.",
    )
    parser.add_argument(
        "--out-wide-csv",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/TMP_DF8_wide.csv"),
        help="Output path for the flattened CSV.",
    )
    parser.add_argument(
        "--out-profile-json",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/DF8_wide_profile.json"),
        help="Output path for the QC and profile log.",
    )
    parser.add_argument(
        "--out-parquet", type=Path, default=None, help="Optional Parquet output path."
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        default=5050,
        help="Expected total rows (set to 0 to disable check).",
    )
    parser.add_argument(
        "--tier0-fixes",
        action="store_true",
        help="Enable Tier 0 Phase B gated fixes: is_coded normalization, DF11 placeholder injection, code expansion format",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    args = parser.parse_args(argv)

    return DF8Config(
        df8_dir=args.df8_dir,
        metadata_csv=args.metadata_csv,
        code_map_json=args.code_map_json,
        out_wide_csv=args.out_wide_csv,
        out_profile_json=args.out_profile_json,
        out_parquet=args.out_parquet,
        expected_rows=None if args.expected_rows == 0 else args.expected_rows,
        log_level=args.log_level,
        tier0_fixes=bool(args.tier0_fixes),
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    CLI entrypoint for the script.

    Args:
        argv: Command-line arguments, defaults to sys.argv[1:].
    """
    cfg = parse_args(argv)
    log_level = getattr(logging, cfg.__dict__.get("log_level", "INFO").upper())
    configure_logging(level=log_level)
    try:
        run_pipeline(cfg)
    except (ConfigError, DataTransformError, FileNotFoundError) as e:
        logger.critical("Pipeline failed with a critical error: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.critical("An unexpected error occurred: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
