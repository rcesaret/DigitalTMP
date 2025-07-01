# -*- coding: utf-8 -*-
"""Unit tests for the column profile metrics module."""

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
    metrics_profile = importlib.import_module("profiling_modules.metrics_profile")
except ImportError as e:
    pytest.fail(f"Failed to import test subject module: {e}", pytrace=False)


@pytest.fixture
def mock_engine():
    """Provides a mock SQLAlchemy Engine and its connection."""
    engine = MagicMock()
    mock_connection = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_connection
    return engine, mock_connection


@pytest.fixture
def mock_pandas_read_sql():
    """Patches pandas.read_sql_query where it is used in the module."""
    with patch("profiling_modules.metrics_profile.pd.read_sql_query") as mock_read:
        yield mock_read


class TestGetAllColumnProfiles:
    """Tests for the get_all_column_profiles function."""

    @patch("profiling_modules.metrics_profile.get_table_names")
    def test_success(self, mock_get_tables, mock_engine, mock_pandas_read_sql):
        """Test successful retrieval of column profiles."""
        engine, mock_connection = mock_engine
        schema_name = "public"
        mock_get_tables.return_value = ["users"]

        mock_df = pd.DataFrame({
            "table_name": ["users"],
            "column_name": ["email"],
            "null_frac": [0.1],
            "n_distinct": [100.0],
            "most_common_vals": ["{'a@a.com', 'b@b.com'}"],
            "most_common_freqs": ["[0.1, 0.05]"],
            "histogram_bounds": ["[1, 10, 20]"],
            "correlation": [0.5],
        })
        mock_pandas_read_sql.return_value = mock_df

        mock_connection.execute.return_value.scalar_one.return_value = 1000

        profiles = metrics_profile.get_all_column_profiles(engine, schema_name)

        assert len(profiles) == 1
        assert profiles[0]["row_count_exact"] == 1000
        assert profiles[0]["null_count_estimate"] == 100

    @patch("profiling_modules.metrics_profile.get_table_names", return_value=[])
    def test_no_tables(self, mock_get_tables, mock_engine):
        """Test it returns an empty list if no tables are found."""
        profiles = metrics_profile.get_all_column_profiles(mock_engine, "public")
        assert profiles == []

    @patch("profiling_modules.metrics_profile.get_table_names", return_value=["users"])
    def test_db_error(self, mock_get_tables, mock_engine, mock_pandas_read_sql, caplog):
        """Test it returns an empty list and logs on DB error."""
        mock_pandas_read_sql.side_effect = SQLAlchemyError("Query failed")
        with caplog.at_level(logging.ERROR):
            profiles = metrics_profile.get_all_column_profiles(mock_engine, "public")

        assert profiles == []
        assert "Failed to get column profiles for schema" in caplog.text
