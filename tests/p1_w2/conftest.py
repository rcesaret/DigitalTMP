import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

# Add the root directory to the Python path to enable imports
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))


# Create mock objects for modules that we'll patch
class MockModule:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def mock_pipeline_modules():
    """Create mock objects for all
    profiling modules with realistic return values."""
    metrics_basic_mock = Mock()
    metrics_schema_mock = Mock()
    metrics_profile_mock = Mock()
    metrics_interop_mock = Mock()
    metrics_performance_mock = Mock()

    # Configure mock returns with realistic DataFrame/dict structures
    # For basic metrics - return a DataFrame with database statistics
    metrics_basic_mock.get_basic_database_metrics.return_value = pd.DataFrame({
        "database": ["test_db"],
        "schema_count": [5],
        "table_count": [20],
        "total_size_mb": [150.5],
    })

    # For schema metrics - return a DataFrame with schema information
    metrics_schema_mock.get_schema_metrics.return_value = pd.DataFrame({
        "schema": ["public", "private"],
        "table_count": [10, 5],
        "total_columns": [50, 25],
        "avg_columns_per_table": [5, 5],
    })

    # For profile metrics - return a DataFrame with column profiles
    metrics_profile_mock.get_column_profiles.return_value = pd.DataFrame({
        "table": ["users", "orders"],
        "column": ["name", "amount"],
        "data_type": ["text", "numeric"],
        "distinct_count": [1000, 500],
        "null_count": [10, 5],
        "row_count_exact": [1010, 505],
    })

    # For interoperability metrics - return a dictionary with scores
    metrics_interop_mock.calculate_interoperability_metrics.return_value = {
        "standard_compliance_score": 0.85,
        "data_quality_score": 0.92,
        "schema_stability_score": 0.78,
        "overall_score": 0.85,
    }

    # For performance metrics - return a DataFrame with benchmark results
    metrics_performance_mock.run_performance_benchmarks.return_value = pd.DataFrame({
        "query_id": ["q1", "q2", "q3"],
        "query_category": ["basic", "filtering", "joining"],
        "execution_time_ms": [15.2, 45.7, 120.3],
        "rows_returned": [1000, 500, 200],
    })

    return {
        "metrics_basic": metrics_basic_mock,
        "metrics_schema": metrics_schema_mock,
        "metrics_profile": metrics_profile_mock,
        "metrics_interop": metrics_interop_mock,
        "metrics_performance": metrics_performance_mock,
    }


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    import configparser

    config = configparser.ConfigParser()
    config["databases"] = {
        "legacy": "tmp_df8,tmp_df9,tmp_df10,tmp_rean_df2",
        "benchmark": ("tmp_benchmark_wide_numeric,tmp_benchmark_wide_text_nulls"),
    }
    config["database_tmp_df8"] = {
        "host": "localhost",
        "port": "5432",
        "user": "testuser",
        "password": "testpassword",  # pragma: allowlist-secret
    }
    config["database_tmp_df9"] = {
        "host": "localhost",
        "port": "5432",
        "user": "testuser",
        "password": "testpassword",  # pragma: allowlist-secret
    }
    config["database_tmp_df10"] = {
        "host": "localhost",
        "port": "5432",
        "user": "testuser",
        "password": "testpassword",  # pragma: allowlist-secret
    }
    config["database_tmp_rean_df2"] = {
        "host": "localhost",
        "port": "5432",
        "user": "testuser",
        "password": "testpassword",  # pragma: allowlist-secret
    }
    config["database_tmp_benchmark_wide_numeric"] = {
        "host": "localhost",
        "port": "5432",
        "user": "testuser",
        "password": "testpassword",  # pragma: allowlist-secret
    }
    config["database_tmp_benchmark_wide_text_nulls"] = {
        "host": "localhost",
        "port": "5432",
        "user": "testuser",
        "password": "testpassword",  # pragma: allowlist-secret
    }
    return config


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine with context manager support."""
    mock_engine = Mock()
    mock_connection = Mock()

    # Configure the engine to work as a context manager
    mock_engine.__enter__ = Mock(return_value=mock_connection)
    mock_engine.__exit__ = Mock(return_value=None)

    # Mock connection.execute to return a result set
    mock_result = Mock()
    mock_result.fetchall.return_value = [(1, "test")]  # Sample result
    mock_connection.execute.return_value = mock_result

    return mock_engine


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create metrics subdirectory
        output_dir = Path(tmpdirname) / "outputs" / "metrics"
        output_dir.mkdir(parents=True, exist_ok=True)
        yield output_dir


class TestLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)
