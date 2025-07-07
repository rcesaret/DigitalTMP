# -*- coding: utf-8 -*-
"""Unit tests for the performance metrics profiling module."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

# Add the parent directory of 'profiling_modules' to the system path
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
module_src_path = project_root / "phases" / "01_LegacyDB" / "src"
sys.path.insert(0, str(module_src_path))

# Import the module using its package path
try:
    metrics_performance = importlib.import_module(
        "profiling_modules.metrics_performance"
    )
except ImportError as e:
    pytest.fail(f"Failed to import test subject module: {e}", pytrace=False)


@pytest.fixture
def mock_engine():
    """Provides a mock SQLAlchemy Engine and its connection."""
    engine = MagicMock()
    mock_connection = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_connection
    return engine, mock_connection


class TestRunPerformanceBenchmarks:
    """Tests for run_performance_benchmarks."""

    @patch("pathlib.Path.exists", return_value=True)
    def test_success(self, mock_exists, mock_engine):
        """Test a successful benchmark run."""
        engine, mock_connection = mock_engine

        # Mock file content with proper SQL format
        sql_content = """-- CATEGORY: baseline
-- QUERY: 1.1
SELECT COUNT(*) FROM ${schema}.test_table;
-- END Query

-- CATEGORY: performance
-- QUERY: 2.1
SELECT * FROM ${schema}.users WHERE id = 1;
-- END Query"""

        with patch("builtins.open", mock_open(read_data=sql_content)):
            # Mock the connection execute to return successful results
            mock_result = MagicMock()
            mock_result.returns_rows = True
            mock_result.fetchall.return_value = [(100,)]
            mock_connection.execute.return_value = mock_result

            # Mock transaction
            mock_trans = MagicMock()
            mock_connection.begin.return_value = mock_trans

            results = metrics_performance.run_performance_benchmarks(
                engine, "test_db", "public", Path("/fake/dir/test_queries.sql")
            )

        # Should have results for both queries
        assert len(results) == 2
        assert all(results["status"] == "Success")
        assert all(results["latency_ms"].notna())

    @patch("pathlib.Path.exists", return_value=False)
    def test_file_not_found(self, mock_exists, mock_engine):
        """Test behavior when query file doesn't exist."""
        engine, _ = mock_engine

        results = metrics_performance.run_performance_benchmarks(
            engine, "test_db", "public", Path("/nonexistent/file.sql")
        )

        # Should return empty DataFrame when file doesn't exist
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 0

    def test_query_execution_failure(self, mock_engine):
        """Test handling of query execution failures."""
        engine, mock_connection = mock_engine

        sql_content = """-- CATEGORY: baseline
-- QUERY: 1.1
SELECT * FROM nonexistent_table;
-- END Query"""

        with patch("builtins.open", mock_open(read_data=sql_content)):
            with patch("pathlib.Path.exists", return_value=True):
                # Mock the connection execute to raise an exception
                mock_connection.execute.side_effect = Exception("Table not found")

                # Mock transaction
                mock_trans = MagicMock()
                mock_connection.begin.return_value = mock_trans

                results = metrics_performance.run_performance_benchmarks(
                    engine, "test_db", "public", Path("/fake/dir/test_queries.sql")
                )

        # Should have one failed result
        assert len(results) == 1
        assert results.iloc[0]["status"] == "Failed"
        assert "Table not found" in results.iloc[0]["error_message"]
