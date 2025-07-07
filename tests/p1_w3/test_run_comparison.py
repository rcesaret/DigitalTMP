# -*- coding: utf-8 -*-
"""
Tests for the 04_run_comparison.py aggregation script.

These tests verify the functionality of the script that aggregates and compares
results from the database profiling pipeline. The tests cover loading metrics,
calculating summaries, handling errors, and generating reports.
"""

import configparser
import importlib.util
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add the project root to the path to import the script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Dynamically import module from file with importlib (since it starts with a number)
spec = importlib.util.spec_from_file_location(
    "run_comparison",
    str(
        Path(__file__).parent.parent.parent
        / "phases"
        / "01_LegacyDB"
        / "src"
        / "04_run_comparison.py"
    ),
)
run_comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_comparison)


# --- Fixtures ---


@pytest.fixture
def temp_metrics_dir():
    """Create a temporary directory for metrics files."""
    with TemporaryDirectory() as temp_dir:
        metrics_dir = Path(temp_dir)
        yield metrics_dir


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        yield output_dir


@pytest.fixture
def mock_config_file(temp_metrics_dir, temp_output_dir):
    """Creates a mock config.ini file for testing."""
    config = configparser.ConfigParser()
    config["paths"] = {
        "output_metrics": str(temp_metrics_dir),
        "output_reports": str(temp_output_dir),
    }

    with NamedTemporaryFile("w", suffix=".ini", delete=False) as f:
        config.write(f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    if config_path.exists():
        os.unlink(config_path)


@pytest.fixture
def sample_metrics(temp_metrics_dir):
    """Creates sample metric files for testing."""
    # Sample table metrics
    db1_table_metrics = pd.DataFrame({
        "table_name": ["table1", "table2"],
        "row_count": [100, 200],
        "index_count": [1, 2],
        "total_size_kb": [50, 100],
        "row_estimate": [110, 220],
    })
    db1_table_metrics.to_csv(temp_metrics_dir / "db1_table_metrics.csv", index=False)

    # Sample schema counts
    db1_schema_counts = pd.DataFrame({
        "table_count": [10],
        "view_count": [5],
        "function_count": [3],
        "total_objects": [18],
    })
    db1_schema_counts.to_csv(temp_metrics_dir / "db1_schema_counts.csv", index=False)

    # Sample performance benchmarks with correct format for current implementation
    # The script expects 'query_name' column and creates 'query_id' from it
    db1_performance = pd.DataFrame({
        "query_name": [
            "SELECT - query1",
            "SELECT - query2",
            "INSERT - query3",
            "SELECT - query4",
            "UPDATE - query5",
        ],
        "latency_ms": [100, 200, 150, 80, 90],
        "status": ["Success", "Success", "Failed", "Success", "Success"],
        "database": ["db1", "db1", "db1", "db1", "db1"],
        "rows_returned": [10, 20, 0, 15, 25],
    })
    db1_performance.to_csv(
        temp_metrics_dir / "db1_performance_benchmarks.csv", index=False
    )

    # Benchmark database with matching query_names
    db2_performance = pd.DataFrame({
        "query_name": [
            "SELECT - query1",
            "SELECT - query2",
            "INSERT - query3",
            "SELECT - query4",
            "UPDATE - query5",
        ],
        "latency_ms": [120, 180, 300, 85, 95],
        "status": ["Success", "Success", "Success", "Success", "Success"],
        "database": [
            "tmp_benchmark_db",
            "tmp_benchmark_db",
            "tmp_benchmark_db",
            "tmp_benchmark_db",
            "tmp_benchmark_db",
        ],
        "rows_returned": [10, 20, 30, 15, 25],
    })
    db2_performance.to_csv(
        temp_metrics_dir / "tmp_benchmark_db_performance_benchmarks.csv", index=False
    )

    # Second database (benchmark)
    db2_table_metrics = pd.DataFrame({
        "table_name": ["table1", "table2"],
        "row_count": [110, 210],
        "index_count": [2, 3],
        "total_size_kb": [55, 110],
        "row_estimate": [120, 230],
    })
    db2_table_metrics.to_csv(
        temp_metrics_dir / "tmp_benchmark_db_table_metrics.csv", index=False
    )

    return temp_metrics_dir


# --- Tests ---


def test_load_all_metrics(sample_metrics):
    """Test loading metrics from files."""
    all_data = run_comparison.load_all_metrics(sample_metrics)

    # Verify databases were loaded
    assert "db1" in all_data
    assert "tmp_benchmark_db" in all_data

    # Verify new data structure with is_benchmark flag
    assert all_data["db1"]["is_benchmark"] is False
    assert all_data["tmp_benchmark_db"]["is_benchmark"] is True

    # Verify metrics were loaded
    assert "table_metrics" in all_data["db1"]["metrics"]
    assert "schema_counts" in all_data["db1"]["metrics"]
    assert "performance_benchmarks" in all_data["db1"]["metrics"]


def test_load_all_metrics_empty_dir(temp_metrics_dir):
    """Test handling of empty metrics directory."""
    all_data = run_comparison.load_all_metrics(temp_metrics_dir)
    assert all_data == {}, "Empty directory should return empty dict"


def test_load_all_metrics_nonexistent_dir():
    """Test handling of non-existent metrics directory."""
    nonexistent_dir = Path("/nonexistent/directory")
    all_data = run_comparison.load_all_metrics(nonexistent_dir)
    assert all_data == {}, "Non-existent directory should return empty dict"


def test_calculate_summary_metrics(sample_metrics):
    """Test calculating summary metrics for a database."""
    all_data = run_comparison.load_all_metrics(sample_metrics)
    db_name = "db1"
    db_metrics = all_data[db_name]["metrics"]

    summary = run_comparison.calculate_summary_metrics(db_name, db_metrics)

    # Verify summary contains expected metrics
    assert summary["Database"] == "db1"
    assert "Table Count" in summary
    assert "Total Estimated Rows" in summary
    assert "Total Index Count" in summary


def test_calculate_comparative_performance_metrics(sample_metrics):
    """Test calculating comparative performance metrics."""
    all_data = run_comparison.load_all_metrics(sample_metrics)

    perf_summary = run_comparison.calculate_comparative_performance_metrics(all_data)

    # Verify performance metrics were calculated
    assert not perf_summary.empty
    assert "database" in perf_summary.columns
    assert "category" in perf_summary.columns
    assert "query_id" in perf_summary.columns
    assert "latency_ms" in perf_summary.columns
    assert "schema_efficiency_factor" in perf_summary.columns


def test_generate_markdown_report(temp_output_dir):
    """Test generation of markdown report."""
    # Create sample summary dataframe for report
    summary_df = pd.DataFrame({
        "Database": ["db1", "tmp_benchmark_db"],
        "Database Size (MB)": [25, 30],
        "Table Count": [10, 12],
        "Total Estimated Rows": [300, 320],
        "JDI (Join Dependency Index)": [2.5, 2.7],
        "NF (Normalization Factor)": [3.0, 3.1],
    })

    # Create sample performance dataframe
    perf_df = pd.DataFrame({
        "database": ["db1", "tmp_benchmark_db"],
        "category": ["SELECT", "SELECT"],
        "query_id": ["query1", "query1"],
        "latency_ms": [10.5, 9.8],
        "schema_efficiency_factor": [1.0, 1.07],
    })

    report_path = temp_output_dir / "test_report.md"
    run_comparison.generate_markdown_report(summary_df, perf_df, report_path)

    # Verify report was created
    assert report_path.exists()

    # Verify report content
    report_content = report_path.read_text()
    assert "# Database Comparison Report" in report_content
    assert "db1" in report_content
    assert "tmp_benchmark_db" in report_content


def test_main_function(temp_metrics_dir, temp_output_dir, mock_config_file):
    """Test that the main function runs without errors."""
    # Mock the argument parser to return required arguments
    mock_args = MagicMock()
    mock_args.config = mock_config_file

    # Mock the functions called by main
    with (
        patch.object(run_comparison, "parse_arguments", return_value=mock_args),
        patch.object(run_comparison, "load_all_metrics") as mock_load,
        patch.object(
            run_comparison,
            "calculate_summary_metrics",
            return_value={"Database": "test_db", "metric1": 1, "metric2": 2},
        ) as mock_calc_summary,
        patch.object(
            run_comparison, "calculate_comparative_performance_metrics"
        ) as mock_calc_perf,
        patch.object(run_comparison, "generate_markdown_report") as mock_report,
        patch.object(run_comparison, "setup_logging") as mock_setup_logging,
    ):
        # Set up mock return values with proper structure
        mock_load.return_value = {
            "db1": {
                "metrics": {"table_metrics": pd.DataFrame()},
                "is_benchmark": False,
            },
            "db2": {"metrics": {"table_metrics": pd.DataFrame()}, "is_benchmark": True},
        }
        # Create a DataFrame for the performance summary
        mock_calc_perf.return_value = pd.DataFrame({"mockcolumn": [1, 2]})
        mock_setup_logging.return_value = None

        # Call the main function
        run_comparison.main()

        # Assert all required functions were called
        mock_load.assert_called_once()
        assert mock_calc_summary.call_count == 2  # Once for each database
        mock_calc_perf.assert_called_once()
        mock_report.assert_called_once()
        mock_setup_logging.assert_called_once()


def test_setup_logging(temp_output_dir):
    """Test that logging is set up correctly."""
    log_dir = temp_output_dir

    # Call setup_logging function
    run_comparison.setup_logging(log_dir)

    # Verify log file was created
    log_file = log_dir / run_comparison.LOG_FILE_NAME
    assert log_file.exists()


def test_parse_arguments():
    """Test argument parsing."""
    with patch("sys.argv", ["04_run_comparison.py", "--config", "/path/to/config.ini"]):
        args = run_comparison.parse_arguments()
        assert args.config == Path("/path/to/config.ini")


@pytest.mark.parametrize(
    "missing_file",
    ["table_metrics.csv", "schema_counts.csv", "performance_benchmarks.csv"],
)
def test_missing_metric_files(temp_metrics_dir, missing_file):
    """Test handling of missing metric files."""
    # Create a file that doesn't match the expected pattern
    with open(temp_metrics_dir / "some_other_file.txt", "w") as f:
        f.write("This is not a metric file")

    all_data = run_comparison.load_all_metrics(temp_metrics_dir)
    # Should return empty dict since no valid metric files were found
    assert all_data == {}


def test_performance_metrics_with_benchmark_identification(sample_metrics):
    """Test that benchmark databases are correctly identified and used."""
    all_data = run_comparison.load_all_metrics(sample_metrics)

    # Verify benchmark identification
    assert all_data["tmp_benchmark_db"]["is_benchmark"] is True
    assert all_data["db1"]["is_benchmark"] is False

    # Test performance calculation
    perf_summary = run_comparison.calculate_comparative_performance_metrics(all_data)

    # Verify benchmark databases are used for baseline calculations
    assert not perf_summary.empty
    assert "baseline_latency_ms" in perf_summary.columns
    assert "schema_efficiency_factor" in perf_summary.columns


def test_calculate_summary_metrics_with_missing_data():
    """Test summary calculation when some metrics are missing."""
    db_name = "test_db"
    db_data = {
        "table_metrics": pd.DataFrame({
            "row_estimate": [100, 200],
            "index_count": [1, 2],
        }),
        # Missing basic_metrics, schema_counts, interop_metrics
    }

    summary = run_comparison.calculate_summary_metrics(db_name, db_data)

    # Should handle missing data gracefully
    assert summary["Database"] == "test_db"
    assert summary["Total Estimated Rows"] == 300
    assert summary["Total Index Count"] == 3
    assert summary["Database Size (MB)"] is None  # Missing basic_metrics


def test_performance_metrics_empty_data():
    """Test performance calculation with no performance data."""
    all_data = {
        "db1": {"metrics": {"table_metrics": pd.DataFrame()}, "is_benchmark": False},
    }

    perf_summary = run_comparison.calculate_comparative_performance_metrics(all_data)

    # Should return empty DataFrame when no performance data
    assert perf_summary.empty
