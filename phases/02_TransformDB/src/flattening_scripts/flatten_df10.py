#!/usr/bin/env python3
"""
flatten_df10.py - DF10 Wide Format Transformation Script

Transforms TMP_DF10's Entity-Attribute-Value (EAV) structure into a single
wide-format DataFrame compatible with DF8 and DF9 outputs for Phase 2 integration.

This script implements the complete core operations from the R reference script
while conforming to all project Python coding standards and integrating with
the Phase 2 ELT pipeline architecture.

Key Operations:
1. Load all DF10 CSV tables with latin1 encoding
2. Clean provTable (handle subsite values)
3. Pivot codeTable with code-to-text mapping
4. Pivot interpTable with code-to-text mapping
5. Process totalsTable (already wide format)
6. Pivot artifactTable with 3-level hierarchy
7. Left join all tables to provTable on SSN
8. Apply metadata-driven rename and reorder

Usage:
    python flatten_df10.py \
        --input-dir phases/02_TransformDB/data/db_extracted_tables/TMP_DF10 \
        --metadata-path phases/02_TransformDB/metadata/DF10_metadata.csv \
        --output-path phases/02_TransformDB/data/dbs_wide/TMP_DF10_wide.csv
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ================================ CONSTANTS ==================================
# REASON: Centralize all magic values to avoid hardcoded literals throughout code

# File encoding for legacy data
ENCODING_LATIN1: str = "latin1"

# Input CSV filenames expected in input directory
FNAME_PROV_TABLE: str = "provTable.csv"
FNAME_CODE_TABLE: str = "codeTable.csv"
FNAME_CODE_CODES: str = "codeCodes.csv"
FNAME_INTERP_TABLE: str = "interpTable.csv"
FNAME_INTERP_CODES: str = "interpCodes.csv"
FNAME_TOTALS_TABLE: str = "totalsTable.csv"
FNAME_ARTIFACT_TABLE: str = "artifactTable.csv"
FNAME_ARTIFACT_CODES: str = "artifactCodes.csv"

# Output filename
FNAME_DF10_WIDE_OUT: str = "TMP_DF10_wide.csv"

# Sentinel values and special labels
MISSING_SENTINEL_NEG9999: int = -9999
MISSING_WHERE_LABEL: str = "Missing"
MISSING_TEXT_LABEL: str = "missing data"
ABSENT_TEXT_LABEL: str = "absent"
NONE_SUBSITE_LABEL: str = "NONE"

# Special-case artifact per R script logic
ARTIFACT_SPECIAL_CODE2: int = 12
ARTIFACT_SPECIAL_CODE3: int = 46
ARTIFACT_SPECIAL_NAME: str = "figAzte"

# Columns requiring absent→NA conversion per R script
CODES_ABSENT_TO_NA_COLS: Tuple[str, ...] = (
    "workLab1",
    "workLab2",
    "workLab3",
    "workFie1",
    "workFie2",
    "workFie3",
    "workFie4",
    "workFie5",
)

# Expected row count for validation
EXPECTED_ROW_COUNT: int = 5050

# Logging configuration
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ================================ CONFIGURATION ===============================


@dataclass
class DF10Config:
    """Configuration for DF10 flattening pipeline.

    Attributes:
        input_dir: Directory containing DF10 extracted CSV tables
        metadata_path: Path to DF10_metadata.csv file
        output_path: Path for output TMP_DF10_wide.csv
        emit_code_labels: Whether to expand codes to "code. description" format
        validate_rows: Whether to validate against expected row count
        generate_profile: Whether to generate data profile JSON
    """

    input_dir: Path
    metadata_path: Path
    output_path: Path
    emit_code_labels: bool = True
    validate_rows: bool = True
    generate_profile: bool = True

    def __post_init__(self) -> None:
        """Validate and convert paths to Path objects."""
        self.input_dir = Path(self.input_dir)
        self.metadata_path = Path(self.metadata_path)
        self.output_path = Path(self.output_path)

        # Validate input directory exists
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")

        # Validate metadata file exists
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)


# ================================ LOGGING =====================================

logger = logging.getLogger(__name__)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging for the script.

    Args:
        level: Logging level (default INFO)
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )


# ================================ I/O OPERATIONS ==============================


def read_csv_safe(
    filepath: Path,
    encoding: str = ENCODING_LATIN1,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read CSV file with robust error handling.

    Args:
        filepath: Path to CSV file
        encoding: File encoding (default latin1 for legacy data)
        **kwargs: Additional pandas read_csv arguments

    Returns:
        DataFrame from CSV file

    Raises:
        FileNotFoundError: If file doesn't exist
        pd.errors.ParserError: If CSV parsing fails
    """
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    try:
        df = pd.read_csv(filepath, encoding=encoding, **kwargs)
        logger.debug(f"Loaded {filepath.name}: {df.shape[0]} rows × {df.shape[1]} cols")
        return df
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse CSV {filepath}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error reading {filepath}: {e}")
        logger.info("Attempting fallback to UTF-8 encoding...")
        return pd.read_csv(filepath, encoding="utf-8", **kwargs)


def load_input_tables(config: DF10Config) -> Dict[str, pd.DataFrame]:
    """Load all required input CSV tables.

    Args:
        config: Configuration object

    Returns:
        Dictionary mapping table names to DataFrames
    """
    logger.info("Loading input tables from %s", config.input_dir)

    tables = {}

    # Define required tables and their filenames
    required_tables = {
        "prov": FNAME_PROV_TABLE,
        "code_table": FNAME_CODE_TABLE,
        "code_codes": FNAME_CODE_CODES,
        "interp_table": FNAME_INTERP_TABLE,
        "interp_codes": FNAME_INTERP_CODES,
        "totals_table": FNAME_TOTALS_TABLE,
        "artifact_table": FNAME_ARTIFACT_TABLE,
        "artifact_codes": FNAME_ARTIFACT_CODES,
    }

    # Load each table
    for name, filename in required_tables.items():
        filepath = config.input_dir / filename
        tables[name] = read_csv_safe(filepath)

    # Load metadata
    tables["metadata"] = read_csv_safe(config.metadata_path)

    logger.info("Successfully loaded %d tables", len(tables))
    return tables


# ================================ DATA CLEANING ===============================


def clean_prov_table(prov: pd.DataFrame) -> pd.DataFrame:
    """Clean provTable per R script specifications.

    Specifically handles Subsite "NONE" values.

    Args:
        prov: Raw provTable DataFrame

    Returns:
        Cleaned provTable DataFrame
    """
    logger.info("Cleaning provTable...")

    # Create copy to avoid modifying original
    prov_clean = prov.copy()

    # Handle "NONE" subsite values per R script
    if "Subsite" in prov_clean.columns:
        mask = prov_clean["Subsite"] == NONE_SUBSITE_LABEL
        prov_clean.loc[mask, "Subsite"] = np.nan
        logger.debug(f"Converted {mask.sum()} 'NONE' Subsite values to NaN")

    # Ensure SSN is numeric
    prov_clean["SSN"] = pd.to_numeric(prov_clean["SSN"], errors="coerce")

    # Check for duplicate SSNs
    if prov_clean["SSN"].duplicated().any():
        dup_count = prov_clean["SSN"].duplicated().sum()
        logger.warning(f"Found {dup_count} duplicate SSN values in provTable")

    return prov_clean


# ================================ CODE EXPANSION ==============================


def build_code_lookup(
    codes_df: pd.DataFrame,
    code_col: str = "Code",
    desc_col: str = "Description",
) -> Dict[int, str]:
    """Build lookup dictionary for code to description mapping.

    Args:
        codes_df: DataFrame with code definitions
        code_col: Name of code column
        desc_col: Name of description column

    Returns:
        Dictionary mapping codes to "code. description" format
    """
    lookup = {}

    for _, row in codes_df.iterrows():
        code = row[code_col]
        desc = row[desc_col]

        # Format as "code. description"
        if pd.notna(desc):
            lookup[code] = f"{code}. {desc}"
        else:
            lookup[code] = str(code)

    return lookup


def expand_codes(
    series: pd.Series,
    code_lookup: Dict[int, str],
) -> pd.Series:
    """Expand numeric codes to "code. description" format.

    Args:
        series: Series with numeric codes
        code_lookup: Dictionary mapping codes to descriptions

    Returns:
        Series with expanded code descriptions
    """
    # Map codes preserving NaN values
    return series.map(lambda x: code_lookup.get(x, str(x)) if pd.notna(x) else np.nan)


# ================================ PIVOTING OPERATIONS =========================


def format_codes(
    code_table: pd.DataFrame,
    code_codes: pd.DataFrame,
    config: DF10Config,
) -> pd.DataFrame:
    """Format codeTable from EAV to wide format.

    Implements the R script's codeTable processing including:
    - Pivot Variable column to wide format
    - Expand codes to descriptions if configured
    - Handle "absent" values for specific columns

    Args:
        code_table: EAV format codeTable
        code_codes: Code definitions
        config: Configuration object

    Returns:
        Wide format DataFrame
    """
    logger.info("Formatting codeTable...")

    # Build code lookup if needed
    if config.emit_code_labels:
        code_lookup = build_code_lookup(code_codes)
        code_table = code_table.copy()
        code_table["Code"] = expand_codes(code_table["Code"], code_lookup)
        default_fill = "0. absent"
    else:
        default_fill = 0

    # Check for Where = "Missing" entries and handle sentinel values
    missing_mask = code_table["Where"] == MISSING_WHERE_LABEL
    if missing_mask.any():
        code_table.loc[missing_mask, "Code"] = np.nan

    # Pivot to wide format
    codes_wide = code_table.pivot_table(
        index="SSN",
        columns="Variable",
        values="Code",
        aggfunc="first",  # Take first if duplicates
        fill_value=default_fill,
    ).reset_index()

    # Handle specific columns where "absent" should be NA per R script
    for col in CODES_ABSENT_TO_NA_COLS:
        if col in codes_wide.columns:
            if config.emit_code_labels:
                codes_wide[col] = codes_wide[col].replace("0. absent", np.nan)
            else:
                codes_wide[col] = codes_wide[col].replace(0, np.nan)

    logger.info(f"Created {len(codes_wide.columns) - 1} code columns")
    return codes_wide


def format_interps(
    interp_table: pd.DataFrame,
    interp_codes: pd.DataFrame,
    config: DF10Config,
) -> pd.DataFrame:
    """Format interpTable from EAV to wide format.

    Args:
        interp_table: EAV format interpTable
        interp_codes: Interpretation code definitions
        config: Configuration object

    Returns:
        Wide format DataFrame
    """
    logger.info("Formatting interpTable...")

    # Handle column name variation (interpVar vs Variable)
    var_col = "interpVar" if "interpVar" in interp_table.columns else "Variable"

    # Build code lookup if needed
    if config.emit_code_labels:
        code_lookup = build_code_lookup(interp_codes)
        interp_table = interp_table.copy()
        interp_table["Code"] = expand_codes(interp_table["Code"], code_lookup)

    # Check for Where = "Missing" entries
    if "Where" in interp_table.columns:
        missing_mask = interp_table["Where"] == MISSING_WHERE_LABEL
        if missing_mask.any():
            interp_table.loc[missing_mask, "Code"] = np.nan

    # Pivot to wide format (no fill_value per R script)
    interps_wide = interp_table.pivot_table(
        index="SSN",
        columns=var_col,
        values="Code",
        aggfunc="first",
    ).reset_index()

    logger.info(f"Created {len(interps_wide.columns) - 1} interpretation columns")
    return interps_wide


def format_totals(totals_table: pd.DataFrame) -> pd.DataFrame:
    """Format totalsTable from long to wide format.

    Implements the R script's NewCount calculation and pivoting.

    Args:
        totals_table: Long format totalsTable

    Returns:
        Wide format DataFrame with numeric counts
    """
    logger.info("Formatting totalsTable...")

    totals = totals_table.copy()

    # Calculate NewCount per R script logic
    # If Where == "Missing", use -9999, else use Where value, else use Count
    totals["NewCount"] = totals.apply(
        lambda row: (
            MISSING_SENTINEL_NEG9999
            if row["Where"] == MISSING_WHERE_LABEL
            else pd.to_numeric(row["Where"], errors="coerce")
            if pd.notna(row["Where"]) and row["Where"] != MISSING_WHERE_LABEL
            else row["Count"]
        ),
        axis=1,
    )

    # Replace -9999 with NaN
    totals["NewCount"] = totals["NewCount"].replace(MISSING_SENTINEL_NEG9999, np.nan)

    # Pivot to wide format with 0 fill
    totals_wide = totals.pivot_table(
        index="SSN",
        columns="Variable",
        values="NewCount",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Ensure all count columns are numeric
    for col in totals_wide.columns:
        if col != "SSN":
            totals_wide[col] = pd.to_numeric(totals_wide[col], errors="coerce").fillna(
                0
            )

    logger.info(f"Created {len(totals_wide.columns) - 1} total count columns")
    return totals_wide


def format_artifacts(
    artifact_table: pd.DataFrame,
    artifact_codes: pd.DataFrame,
    config: DF10Config,
) -> pd.DataFrame:
    """Format artifactTable from EAV to wide format.

    Implements the complex artifact hierarchy processing from R script:
    - Join with artifact codes
    - Handle special case artifact (figAzte)
    - Create hierarchical column names
    - Pivot with numeric counts

    Args:
        artifact_table: EAV format artifactTable
        artifact_codes: Artifact code definitions
        config: Configuration object

    Returns:
        Wide format DataFrame with artifact counts
    """
    logger.info("Formatting artifactTable...")

    artifacts = artifact_table.copy()

    # Join with artifact codes to get descriptions
    artifacts = artifacts.merge(
        artifact_codes[["Code", "Description"]],
        left_on="ArtCode3",
        right_on="Code",
        how="left",
    )

    # Handle special case: ArtCode2=12 & ArtCode3=46 -> "figAzte"
    special_mask = (artifacts["ArtCode2"] == ARTIFACT_SPECIAL_CODE2) & (
        artifacts["ArtCode3"] == ARTIFACT_SPECIAL_CODE3
    )
    artifacts.loc[special_mask, "Description"] = ARTIFACT_SPECIAL_NAME

    # Create artifact name from description
    artifacts["ArtifactName"] = artifacts["Description"].apply(
        lambda x: (
            str(x).lower().replace(" ", "_").replace("-", "_")
            if pd.notna(x)
            else f"artifact_{x}"
        )
    )

    # Handle Where = "Missing" -> Count = NaN
    missing_mask = artifacts["Where"] == MISSING_WHERE_LABEL
    artifacts.loc[missing_mask, "Count"] = np.nan

    # Pivot to wide format with 0 fill
    artifacts_wide = artifacts.pivot_table(
        index="SSN",
        columns="ArtifactName",
        values="Count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Ensure all count columns are numeric
    for col in artifacts_wide.columns:
        if col != "SSN":
            artifacts_wide[col] = pd.to_numeric(
                artifacts_wide[col], errors="coerce"
            ).fillna(0)

    logger.info(f"Created {len(artifacts_wide.columns) - 1} artifact count columns")
    return artifacts_wide


# ================================ METADATA OPERATIONS =========================


def apply_metadata_renames_and_order(
    df: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    """Apply metadata-driven column renaming and reordering.

    Implements the three-step process from R script:
    1. Rename columns based on variable -> var_df11 mapping
    2. Add missing DF11 variables as NA columns
    3. Reorder columns based on order_index

    Args:
        df: Wide format DataFrame to process
        metadata: DF10_metadata DataFrame

    Returns:
        DataFrame with renamed and reordered columns
    """
    logger.info("Applying metadata-driven renames and ordering...")

    result = df.copy()

    # Step 1: Rename columns
    # Build rename mapping from metadata where variable exists in df
    rename_map = {}
    for _, row in metadata.iterrows():
        if pd.notna(row.get("variable")) and pd.notna(row.get("var_df11")):
            if row["variable"] in result.columns:
                rename_map[row["variable"]] = row["var_df11"]

    if rename_map:
        result = result.rename(columns=rename_map)
        logger.info(f"Renamed {len(rename_map)} columns")

    # Check for duplicate column names
    if result.columns.duplicated().any():
        duplicates = result.columns[result.columns.duplicated()].unique()
        raise ValueError(
            f"Duplicate column names after renaming: {', '.join(duplicates)}"
        )

    # Step 2: Add missing DF11 variables
    # Find variables where var_in_df10 == FALSE
    if "var_in_df10" in metadata.columns:
        # Normalize boolean values
        metadata["var_in_df10_bool"] = metadata["var_in_df10"].apply(
            lambda x: (
                False
                if str(x).upper() in ["FALSE", "0", "F"]
                else True
                if str(x).upper() in ["TRUE", "1", "T"]
                else None
            )
        )

        # Select rows where the normalized flag is exactly False (avoid E712 and handle None safely)
        missing_vars = metadata[
            metadata["var_in_df10_bool"].isin([False]) & metadata["var_df11"].notna()
        ]["var_df11"].tolist()

        # Add missing columns with NA values
        for var in missing_vars:
            if var not in result.columns:
                result[var] = np.nan

        if missing_vars:
            logger.info(f"Added {len(missing_vars)} missing DF11 variables")

    # Step 3: Reorder columns based on order_index
    if "order_index" in metadata.columns:
        # Create ordering dataframe
        order_df = metadata[metadata["var_df11"].notna()][
            ["var_df11", "order_index"]
        ].drop_duplicates(subset=["var_df11"])

        # Convert order_index to numeric, handling NaN
        order_df["order_idx_num"] = pd.to_numeric(
            order_df["order_index"], errors="coerce"
        )

        # Sort by order_index (NaN last), then by var_df11
        order_df = order_df.sort_values(
            by=["order_idx_num", "var_df11"],
            na_position="last",
        )

        # Get desired column order
        desired_order = [
            col for col in order_df["var_df11"].tolist() if col in result.columns
        ]

        # Add any remaining columns not in metadata
        remaining_cols = [col for col in result.columns if col not in desired_order]

        # Reorder columns
        result = result[desired_order + remaining_cols]

        logger.info("Reordered columns based on metadata")

    return result


# ================================ MAIN PIPELINE ===============================


def build_df10_wide(config: DF10Config) -> pd.DataFrame:
    """Execute the complete DF10 flattening pipeline.

    Orchestrates all transformation steps matching the R script:
    1. Load input tables
    2. Clean provTable
    3. Format each table (codes, interps, totals, artifacts)
    4. Join all tables to provTable
    5. Apply metadata renames and ordering

    Args:
        config: Configuration object

    Returns:
        Final wide format DataFrame
    """
    logger.info("=" * 60)
    logger.info("Starting DF10 EAV Flattening Pipeline")
    logger.info("=" * 60)

    # Load all input tables
    tables = load_input_tables(config)

    # Clean provTable
    prov_clean = clean_prov_table(tables["prov"])

    # Format each table
    codes_wide = format_codes(tables["code_table"], tables["code_codes"], config)
    interps_wide = format_interps(
        tables["interp_table"], tables["interp_codes"], config
    )
    totals_wide = format_totals(tables["totals_table"])
    artifacts_wide = format_artifacts(
        tables["artifact_table"], tables["artifact_codes"], config
    )

    # Join all tables to provTable
    logger.info("Joining all wide tables to provTable...")

    result = prov_clean

    # Left join each formatted table
    for table, name in [
        (codes_wide, "codes"),
        (interps_wide, "interps"),
        (totals_wide, "totals"),
        (artifacts_wide, "artifacts"),
    ]:
        logger.info(f"Joining {name} table...")
        result = result.merge(table, on="SSN", how="left")

    logger.info(f"Joined result: {result.shape[0]} rows × {result.shape[1]} columns")

    # Apply metadata-driven renames and ordering
    result = apply_metadata_renames_and_order(result, tables["metadata"])

    # Validate row count if configured
    if config.validate_rows and result.shape[0] != EXPECTED_ROW_COUNT:
        logger.warning(
            f"Row count mismatch: expected {EXPECTED_ROW_COUNT}, got {result.shape[0]}"
        )

    logger.info("=" * 60)
    logger.info("DF10 Flattening Complete")
    logger.info(f"Final shape: {result.shape[0]} rows × {result.shape[1]} columns")
    logger.info("=" * 60)

    return result


def generate_profile(df: pd.DataFrame, config: DF10Config) -> Dict[str, Any]:
    """Generate data profile for the wide DataFrame.

    Args:
        df: Wide format DataFrame
        config: Configuration object

    Returns:
        Dictionary with profile metrics
    """
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024**2),
        "ssn_unique": df["SSN"].is_unique if "SSN" in df.columns else None,
        "column_types": {
            "numeric": len(df.select_dtypes(include=[np.number]).columns),
            "object": len(df.select_dtypes(include=["object"]).columns),
        },
        "missing_data": {
            "total_cells": df.size,
            "missing_cells": df.isna().sum().sum(),
            "missing_percentage": (df.isna().sum().sum() / df.size * 100)
            if df.size > 0
            else 0,
        },
        "column_name_patterns": {
            "code_": len([c for c in df.columns if c.startswith("code_")]),
            "interp_": len([c for c in df.columns if c.startswith("interp_")]),
            "artifact_": len([c for c in df.columns if "artifact" in c.lower()]),
            "total_": len([c for c in df.columns if "total" in c.lower()]),
        },
        "sample_ssn": {
            "first_5": df["SSN"].head(5).tolist() if "SSN" in df.columns else [],
            "last_5": df["SSN"].tail(5).tolist() if "SSN" in df.columns else [],
        },
    }

    return profile


def write_output(df: pd.DataFrame, config: DF10Config) -> None:
    """Write output files and generate profile.

    Args:
        df: Wide format DataFrame to write
        config: Configuration object
    """
    logger.info("Writing output files...")

    # Write main CSV output
    try:
        df.to_csv(config.output_path, index=False)
        logger.info(f"Wrote {config.output_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV: {e}")
        raise

    # Generate and write profile if configured
    if config.generate_profile:
        profile = generate_profile(df, config)
        profile_path = config.output_path.with_suffix(".profile.json")

        try:
            with open(profile_path, "w") as f:
                json.dump(profile, f, indent=2, default=str)
            logger.info(f"Wrote profile to {profile_path}")
        except Exception as e:
            logger.warning(f"Failed to write profile: {e}")

    # Optional: Write parquet for faster subsequent reads
    parquet_path = config.output_path.with_suffix(".parquet")
    try:
        df.to_parquet(parquet_path, index=False, compression="snappy")
        logger.info(f"Wrote parquet to {parquet_path}")
    except Exception as e:
        logger.debug(f"Parquet write skipped: {e}")


# ================================ CLI INTERFACE ===============================


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Command-line arguments (None uses sys.argv)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Flatten TMP_DF10 EAV structure to wide format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default paths
  python flatten_df10.py

  # Custom input/output paths
  python flatten_df10.py \\
    --input-dir /path/to/DF10/tables \\
    --output-path /path/to/output.csv

  # Disable code expansion for numeric-only output
  python flatten_df10.py --no-code-labels

  # Enable debug logging
  python flatten_df10.py --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("phases/02_TransformDB/data/db_extracted_tables/TMP_DF10"),
        help="Directory containing DF10 extracted CSV tables",
    )

    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=Path("phases/02_TransformDB/metadata/DF10_metadata.csv"),
        help="Path to DF10_metadata.csv file",
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("phases/02_TransformDB/data/dbs_wide/TMP_DF10_wide.csv"),
        help="Output path for wide format CSV",
    )

    parser.add_argument(
        "--no-code-labels",
        action="store_true",
        help="Disable code expansion to 'code. description' format",
    )

    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip row count validation",
    )

    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Skip generation of data profile JSON",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point for the script.

    Args:
        argv: Command-line arguments (None uses sys.argv)
    """
    # Parse arguments
    args = parse_args(argv)

    # Configure logging
    configure_logging(level=getattr(logging, args.log_level))

    # Create configuration
    config = DF10Config(
        input_dir=args.input_dir,
        metadata_path=args.metadata_path,
        output_path=args.output_path,
        emit_code_labels=not args.no_code_labels,
        validate_rows=not args.no_validation,
        generate_profile=not args.no_profile,
    )

    try:
        # Run pipeline
        df10_wide = build_df10_wide(config)

        # Write outputs
        write_output(df10_wide, config)

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
