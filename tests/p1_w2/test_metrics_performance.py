# -*- coding: utf-8 -*-
"""Unit tests for the performance metrics profiling module."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

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


class TestLoadQueryMetadata:
    """Tests for load_query_metadata."""

    @patch("pathlib.Path.exists", return_value=True)
    def test_success(self, mock_exists):
        """Test successful loading of metadata JSON."""
        json_data = '{"categories": {"cat1": "Category 1"}}'
        with patch("builtins.open", mock_open(read_data=json_data)):
            metadata = metrics_performance.load_query_metadata(Path("/fake/dir"))
            assert metadata["categories"]["cat1"] == "Category 1"


class TestParseCategorizedQueries:
    """Tests for parse_categorized_queries."""

    def test_parsing(self):
        """Test correct parsing of a categorized SQL string."""
        sql_content = """-- CATEGORY: baseline\n-- QUERY: 1.1\nSELECT * FROM table1;"""
        queries = metrics_performance.parse_categorized_queries(sql_content)
        assert queries == [("baseline", "1.1", "SELECT * FROM table1")]


class TestRunPerformanceBenchmarks:
    """Tests for run_performance_benchmarks."""

    @patch("profiling_modules.metrics_performance.parse_categorized_queries")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("profiling_modules.metrics_performance.load_query_metadata")
    def test_success(self, mock_load_meta, mock_exists, mock_parse, mock_engine):
        """Test a successful benchmark run."""
        engine, _ = mock_engine
        mock_load_meta.return_value = {
            "database_mappings": {"test_db": "test_queries.sql"},
            "categories": {"cat1": {"name": "Category One"}},
        }
        mock_parse.return_value = [("cat1", "q1", "SELECT 1")]

        with patch("builtins.open", mock_open(read_data="-- QUERY: q1\nSELECT 1;")):
            results = metrics_performance.run_performance_benchmarks(
                engine, "test_db", "public", Path("/fake/dir")
            )

        assert len(results) == 1
        assert results[0]["status"] == "Success"

    @patch("profiling_modules.metrics_performance.run_legacy_benchmarks")
    @patch("profiling_modules.metrics_performance.load_query_metadata")
    def test_fallback_to_legacy(self, mock_load_meta, mock_legacy, mock_engine):
        """Test it falls back to legacy benchmarks if no mapping is found."""
        engine, _ = mock_engine
        mock_load_meta.return_value = {"database_mappings": {}}
        mock_legacy.return_value = [{"status": "Success"}]

        with patch("pathlib.Path.exists", return_value=True):
            _ = metrics_performance.run_performance_benchmarks(
                engine, "other_db", "public", Path("/fake/dir")
            )

        mock_legacy.assert_called_once()
