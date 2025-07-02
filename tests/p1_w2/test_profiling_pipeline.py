# -*- coding: utf-8 -*-
"""
Integration tests for profiling pipeline orchestrator (02_run_profiling_pipeline.py).

This test suite verifies that the profiling pipeline orchestrator script correctly:
1. Processes all configured databases
2. Generates expected metric files
3. Handles errors gracefully

All external dependencies (database connections, file system operations) are mocked
to ensure tests can run in isolation without actual database connections.
"""

import configparser
import importlib.util
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Determine paths for importing
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_PATH = PROJECT_ROOT / "phases" / "01_LegacyDB" / "src"

# Load the orchestrator script module
script_path = SRC_PATH / "02_run_profiling_pipeline.py"
spec = importlib.util.spec_from_file_location("orchestrator", script_path)
orchestrator = importlib.util.module_from_spec(spec)

# Temporarily add src directory to sys.path for module's internal imports
sys.path.insert(0, str(SRC_PATH))
try:
    spec.loader.exec_module(orchestrator)
except ModuleNotFoundError:
    # If we hit import issues, just continue - we'll mock the dependencies anyway
    pass
finally:
    # Remove the added path
    if str(SRC_PATH) in sys.path:
        sys.path.remove(str(SRC_PATH))

# Path constants for tests
TEST_CONFIG_PATH = Path("phases/01_LegacyDB/src/config.ini")
TEST_OUTPUT_DIR = Path("test_outputs/metrics")


@pytest.fixture
def mock_config():
    """Create a mock configuration object with test settings."""
    config = configparser.ConfigParser()
    config["postgresql"] = {
        "host": "localhost",
        "port": "5432",
        "user": "test_user",
        "password": "test_password",  # pragma: allowlist-secret
    }
    config["databases"] = {
        "legacy_dbs": "tmp_df8, tmp_df9",
        "benchmark_dbs": "tmp_df10",
    }
    config["output"] = {"metrics_dir": str(TEST_OUTPUT_DIR)}
    # Add paths section required by the orchestrator
    config["paths"] = {"sql_queries_dir": "../sql/canonical_queries"}
    return config


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine that supports context manager protocol."""
    engine = MagicMock()

    # Mock context manager protocol for the engine
    engine.__enter__ = MagicMock(return_value=engine)
    engine.__exit__ = MagicMock(return_value=None)

    # Mock connect method that returns the engine itself
    engine.connect = MagicMock(return_value=engine)

    # Add execute method for queries
    engine.execute = MagicMock(return_value=[])

    return engine


@pytest.fixture
def temp_output_dir(tmpdir):
    """Create a temporary directory for test outputs."""
    output_dir = tmpdir.mkdir("metrics")
    return Path(output_dir)


def test_pipeline_completes_without_error(mock_config, mock_engine, temp_output_dir):
    """Test that the profiling pipeline executes completely without errors."""
    # Create mock for argument parser
    mock_args = MagicMock()
    mock_args.config = str(TEST_CONFIG_PATH)

    # Create mock functions with realistic return values based on actual
    # function names from orchestrator code
    basic_db_metrics_mock = MagicMock(
        return_value={"database_name": "test_db", "database_size_mb": 120.5}
    )

    schema_object_counts_mock = MagicMock(
        return_value={
            "schema_name": "public",
            "table_count": 10,
            "view_count": 2,
            "function_count": 5,
        }
    )

    table_level_metrics_mock = MagicMock(
        return_value=[{"table_name": "users", "row_estimate": 1000, "column_count": 5}]
    )

    column_structural_metrics_mock = MagicMock(
        return_value=[
            {"table_name": "users", "column_name": "id", "data_type": "integer"},
            {"table_name": "users", "column_name": "name", "data_type": "varchar"},
        ]
    )

    column_profiles_mock = MagicMock(
        return_value=pd.DataFrame({
            "table": ["users"],
            "column": ["name"],
            "row_count_exact": [1000],
        })
    )

    interop_metrics_mock = MagicMock(return_value={"score": 0.85})

    perf_benchmarks_mock = MagicMock(
        return_value=pd.DataFrame({"query_id": ["q1"], "time_ms": [15]})
    )

    # Define patched get_sqlalchemy_engine function
    def patched_get_sqlalchemy_engine(*args, **kwargs):
        db_name = args[1] if len(args) > 1 else "unknown db"
        print(f"Creating mock engine for: {db_name}")
        return mock_engine

    # Define patched save_results function
    def patched_save_results(data, db_name, metric_name, output_dir):
        print(f"Saving {metric_name} for {db_name}")
        return

    # Apply necessary patches for the test
    # Using EXACT function names from the orchestrator code
    # NOTE: For metrics_profile, the orchestrator calls get_column_profiles but
    # the actual function is get_all_column_profiles
    with (
        patch(
            "profiling_modules.metrics_basic.get_basic_db_metrics",
            basic_db_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_basic.get_schema_object_counts",
            schema_object_counts_mock,
        ),
        patch(
            "profiling_modules.metrics_schema.get_table_level_metrics",
            table_level_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_schema.get_column_structural_metrics",
            column_structural_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_profile.get_all_column_profiles",
            column_profiles_mock,
        ),
        patch(
            "profiling_modules.metrics_interop.calculate_interoperability_metrics",
            interop_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_performance.run_performance_benchmarks",
            perf_benchmarks_mock,
        ),
        patch("configparser.ConfigParser", return_value=mock_config),
        patch.object(
            orchestrator,
            "get_sqlalchemy_engine",
            side_effect=patched_get_sqlalchemy_engine,
        ),
        patch.object(orchestrator, "save_results", side_effect=patched_save_results),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=True),
        patch.object(orchestrator, "parse_arguments", return_value=mock_args),
        patch("pandas.DataFrame.to_csv"),
        patch("json.dump"),
    ):
        # Configure logging to see debug output
        root_logger = logging.getLogger()
        old_level = root_logger.level
        root_logger.setLevel(logging.DEBUG)

        # Execute the pipeline
        orchestrator.main()

        # Restore logging level
        root_logger.setLevel(old_level)

        # Check mock call counts
        print("\nCall counts:")
        print(f"basic_db_metrics calls: {basic_db_metrics_mock.call_count}")
        print(f"schema_object_counts calls: {schema_object_counts_mock.call_count}")
        print(f"table_level_metrics calls: {table_level_metrics_mock.call_count}")
        print(
            f"column_structural_metrics calls: "
            f"{column_structural_metrics_mock.call_count}"
        )
        print(f"column_profiles calls: {column_profiles_mock.call_count}")
        print(f"interop_metrics calls: {interop_metrics_mock.call_count}")
        print(f"performance_benchmarks calls: {perf_benchmarks_mock.call_count}")

        # Verify all mock functions were called at least once
        assert (
            basic_db_metrics_mock.call_count >= 1
        ), "basic_db_metrics function was not called"
        assert (
            schema_object_counts_mock.call_count >= 1
        ), "schema_object_counts function was not called"
        assert (
            table_level_metrics_mock.call_count >= 1
        ), "table_level_metrics function was not called"
        assert (
            column_structural_metrics_mock.call_count >= 1
        ), "column_structural_metrics function was not called"
        assert (
            column_profiles_mock.call_count >= 1
        ), "column_profiles function was not called"
        assert (
            interop_metrics_mock.call_count >= 1
        ), "interop_metrics function was not called"
        assert (
            perf_benchmarks_mock.call_count >= 1
        ), "performance_benchmarks function was not called"


def test_pipeline_creates_expected_metric_files(
    mock_config, mock_engine, temp_output_dir
):
    """Test that the profiling pipeline creates the expected metric files."""
    # Create mock for argument parser
    mock_args = MagicMock()
    mock_args.config = str(TEST_CONFIG_PATH)

    # Create mock functions with realistic return values based on actual
    # function names
    basic_db_metrics_mock = MagicMock(
        return_value={"database_name": "test_db", "database_size_mb": 120.5}
    )

    schema_object_counts_mock = MagicMock(
        return_value={
            "schema_name": "public",
            "table_count": 10,
            "view_count": 2,
            "function_count": 5,
        }
    )

    table_level_metrics_mock = MagicMock(
        return_value=[{"table_name": "users", "row_estimate": 1000, "column_count": 5}]
    )

    column_structural_metrics_mock = MagicMock(
        return_value=[
            {"table_name": "users", "column_name": "id", "data_type": "integer"},
            {"table_name": "users", "column_name": "name", "data_type": "varchar"},
        ]
    )

    column_profiles_mock = MagicMock(
        return_value=[
            {
                "table_name": "users",
                "column_name": "id",
                "null_percent": 0,
                "row_count_exact": 1000,
            }
        ]
    )

    interop_metrics_mock = MagicMock(return_value={"score": 0.85})

    perf_benchmarks_mock = MagicMock(
        return_value=pd.DataFrame({"query_id": ["q1"], "time_ms": [15]})
    )

    # Mock file operations for performance module
    mock_metadata = {"basic": {"name": "Basic Queries"}}

    def mock_open_file(*args, **kwargs):
        from io import StringIO

        file_obj = StringIO()
        # Convert path to string before checking
        path_str = str(args[0])
        if "_categories.json" in path_str:
            import json

            json.dump(mock_metadata, file_obj)
        file_obj.seek(0)
        file_obj.name = path_str  # Add name attribute as string
        return file_obj

    # Track saved files
    saved_csv_files = []
    saved_json_files = []

    # Replace save_results instead of patching to_csv, which is more reliable
    def patched_save_results(data, db_name, metric_name, output_dir):
        nonlocal saved_csv_files, saved_json_files
        filename = f"{db_name}_{metric_name}"
        if isinstance(data, pd.DataFrame) or isinstance(data, list):
            saved_csv_files.append(f"{filename}.csv")
        else:
            saved_json_files.append(f"{filename}.json")
        print(f"Saving {metric_name} for {db_name} -> {filename}")
        return

    # Apply necessary patches for the test
    with (
        patch(
            "profiling_modules.metrics_basic.get_basic_db_metrics",
            basic_db_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_basic.get_schema_object_counts",
            schema_object_counts_mock,
        ),
        patch(
            "profiling_modules.metrics_schema.get_table_level_metrics",
            table_level_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_schema.get_column_structural_metrics",
            column_structural_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_profile.get_all_column_profiles",
            column_profiles_mock,
        ),
        patch(
            "profiling_modules.metrics_interop.calculate_interoperability_metrics",
            interop_metrics_mock,
        ),
        patch(
            "profiling_modules.metrics_performance.run_performance_benchmarks",
            perf_benchmarks_mock,
        ),
        patch("configparser.ConfigParser", return_value=mock_config),
        patch("builtins.open", mock_open_file),
        patch.object(orchestrator, "get_sqlalchemy_engine", return_value=mock_engine),
        patch.object(orchestrator, "save_results", side_effect=patched_save_results),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=True),
        patch.object(orchestrator, "parse_arguments", return_value=mock_args),
        patch("pandas.DataFrame.to_csv"),
        patch("json.dump"),
    ):
        # Execute the pipeline
        orchestrator.main()

        # Print tracked files for debugging
        print(f"\nCSV files: {saved_csv_files}")
        print(f"JSON files: {saved_json_files}")

        # Verify that metric files were created for each database
        for db_name in ["tmp_df8", "tmp_df9", "tmp_df10"]:
            # Check that we have at least one file for this database
            db_files = [f for f in saved_csv_files if db_name.lower() in f.lower()]

            # Verify we have at least some files for this database
            assert (
                len(db_files) > 0
            ), f"No files found for database {db_name} in {saved_csv_files}"

            # Check for specific metrics we know should exist
            assert any(
                "table_metrics" in f.lower() for f in db_files
            ), f"No table_metrics file found for {db_name}"

            assert any(
                "column_structure" in f.lower() for f in db_files
            ), f"No column_structure file found for {db_name}"

            assert any(
                "performance" in f.lower() for f in db_files
            ), f"No performance file found for {db_name}"


def test_pipeline_handles_module_failure_gracefully(
    mock_config, mock_engine, temp_output_dir
):
    """Test that the pipeline continues execution even if one module fails."""
    # Create mock for argument parser
    mock_args = MagicMock()
    mock_args.config = str(TEST_CONFIG_PATH)

    # Create mock functions with realistic return values
    basic_db_metrics_mock = MagicMock(
        return_value={"database_name": "test_db", "database_size_mb": 120.5}
    )

    schema_object_counts_mock = MagicMock(
        return_value={
            "schema_name": "public",
            "table_count": 10,
            "view_count": 2,
            "function_count": 5,
        }
    )

    table_level_metrics_mock = MagicMock(
        return_value=[{"table_name": "users", "row_estimate": 1000, "column_count": 5}]
    )

    # Configure profile mock to raise an exception
    column_profiles_mock = MagicMock(side_effect=Exception("Test failure"))

    # Other mocks function normally
    column_structural_metrics_mock = MagicMock(
        return_value=[
            {"table_name": "users", "column_name": "id", "data_type": "integer"}
        ]
    )

    interop_metrics_mock = MagicMock(return_value={"score": 0.85})

    perf_benchmarks_mock = MagicMock(
        return_value=pd.DataFrame({"query_id": ["q1"], "time_ms": [15]})
    )

    # Mock file operations for performance module
    mock_metadata = {"basic": {"name": "Basic Queries"}}

    def mock_open_file(*args, **kwargs):
        from io import StringIO

        file_obj = StringIO()
        # Convert path to string before checking
        path_str = str(args[0])
        if "_categories.json" in path_str:
            import json

            json.dump(mock_metadata, file_obj)
        file_obj.seek(0)
        file_obj.name = path_str  # Add name attribute as string
        return file_obj

    # Setup logging capture
    log_records = []

    class TestLogHandler(logging.Handler):
        def emit(self, record):
            nonlocal log_records
            log_records.append(record)

    logger = logging.getLogger()
    handler = TestLogHandler()
    logger.addHandler(handler)

    try:
        # Apply necessary patches for the test
        with (
            patch(
                "profiling_modules.metrics_basic.get_basic_db_metrics",
                basic_db_metrics_mock,
            ),
            patch(
                "profiling_modules.metrics_basic.get_schema_object_counts",
                schema_object_counts_mock,
            ),
            patch(
                "profiling_modules.metrics_schema.get_table_level_metrics",
                table_level_metrics_mock,
            ),
            patch(
                "profiling_modules.metrics_schema.get_column_structural_metrics",
                column_structural_metrics_mock,
            ),
            patch(
                "profiling_modules.metrics_profile.get_all_column_profiles",
                column_profiles_mock,
            ),
            patch(
                "profiling_modules.metrics_interop."
                "calculate_interoperability_metrics",
                interop_metrics_mock,
            ),
            patch(
                "profiling_modules.metrics_performance.run_performance_benchmarks",
                perf_benchmarks_mock,
            ),
            patch("configparser.ConfigParser", return_value=mock_config),
            patch("builtins.open", mock_open_file),
            patch.object(
                orchestrator, "get_sqlalchemy_engine", return_value=mock_engine
            ),
            patch.object(orchestrator, "save_results"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch.object(orchestrator, "parse_arguments", return_value=mock_args),
            patch("pandas.DataFrame.to_csv"),
            patch("json.dump"),
        ):
            # Execute the pipeline
            orchestrator.main()

            # Verify other functions were still called despite
            # column_profiles_mock failing
            assert (
                basic_db_metrics_mock.call_count >= 1
            ), "basic_db_metrics function was not called"
            assert (
                schema_object_counts_mock.call_count >= 1
            ), "schema_object_counts function was not called"

            # Verify that error was logged properly
            error_logs = [
                record for record in log_records if record.levelno == logging.ERROR
            ]
            assert any(
                "Test failure" in str(record.getMessage()) for record in error_logs
            ), "Error message not found in logs"

    finally:
        # Clean up logging handler
        logger.removeHandler(handler)
