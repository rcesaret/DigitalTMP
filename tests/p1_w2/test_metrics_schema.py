# -*- coding: utf-8 -*-
"""Unit tests for the schema metrics profiling module."""

import importlib
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory of 'profiling_modules' to the system path
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
module_src_path = project_root / "phases" / "01_LegacyDB" / "src"
sys.path.insert(0, str(module_src_path))

# Import the module using its package path
try:
    metrics_schema = importlib.import_module("profiling_modules.metrics_schema")
except ImportError as e:
    pytest.fail(f"Failed to import test subject module: {e}", pytrace=False)


@pytest.fixture
def mock_engine():
    """Provides a mock SQLAlchemy Engine."""
    return MagicMock()


@pytest.fixture
def mock_pandas_read_sql():
    """Patches pandas.read_sql_query where it is used in the module."""
    with patch("profiling_modules.metrics_schema.pd.read_sql_query") as mock_read:
        yield mock_read


class TestGetTableLevelMetrics:
    """Tests for the get_table_level_metrics function."""

    @patch("profiling_modules.metrics_schema.get_table_names")
    def test_success(self, mock_get_tables, mock_engine, mock_pandas_read_sql):
        """Test successful retrieval of table-level metrics."""
        schema_name = "public"
        mock_get_tables.return_value = ["table1"]
        # Create a mock DataFrame with all required columns for the calculations
        mock_df = pd.DataFrame({
            "table_name": ["table1"],
            "total_size_mb": [0.20],
            "bloat_ratio_estimate": [0.05],
            "expected_size_b": [1000],
            "actual_size_b": [1200],
        })
        mock_pandas_read_sql.return_value = mock_df

        metrics = metrics_schema.get_table_level_metrics(mock_engine, schema_name)

        assert len(metrics) == 1
        assert metrics[0]["table_name"] == "table1"
        mock_pandas_read_sql.assert_called_once()

    @patch("profiling_modules.metrics_schema.get_table_names", return_value=[])
    def test_no_tables(self, mock_get_tables, mock_engine):
        """Test it returns an empty list if no tables are found."""
        metrics = metrics_schema.get_table_level_metrics(mock_engine, "public")
        assert metrics == []

    @patch("profiling_modules.metrics_schema.get_table_names", return_value=["table1"])
    def test_db_error(self, mock_get_tables, mock_engine, mock_pandas_read_sql, caplog):
        """Test it returns an empty list and logs on DB error."""
        mock_pandas_read_sql.side_effect = SQLAlchemyError("Query failed")
        with caplog.at_level(logging.ERROR):
            metrics = metrics_schema.get_table_level_metrics(mock_engine, "public")

        assert metrics == []
        assert "Failed to get table-level metrics" in caplog.text


class TestGetColumnStructuralMetrics:
    """Tests for the get_column_structural_metrics function."""

    def test_success(self, mock_engine, mock_pandas_read_sql):
        """Test successful retrieval of column structural metrics."""
        schema_name = "public"
        mock_df = pd.DataFrame({
            "table_name": ["users"],
            "column_name": ["id"],
            "data_type": ["integer"],
        })
        mock_pandas_read_sql.return_value = mock_df

        metrics = metrics_schema.get_column_structural_metrics(mock_engine, schema_name)

        assert len(metrics) == 1
        assert metrics[0]["column_name"] == "id"
        mock_pandas_read_sql.assert_called_once()

    def test_db_error(self, mock_engine, mock_pandas_read_sql, caplog):
        """Test it returns an empty list and logs on DB error."""
        mock_pandas_read_sql.side_effect = SQLAlchemyError("Query failed")
        with caplog.at_level(logging.ERROR):
            metrics = metrics_schema.get_column_structural_metrics(
                mock_engine, "public"
            )

        assert metrics == []
        assert "Failed to get column structural metrics" in caplog.text
