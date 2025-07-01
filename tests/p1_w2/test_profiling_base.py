# -*- coding: utf-8 -*-
"""Unit tests for the base profiling module."""

import importlib
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory of 'profiling_modules' to the system path
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
module_src_path = project_root / "phases" / "01_LegacyDB" / "src"
sys.path.insert(0, str(module_src_path))

# Import the module using its package path
try:
    profiling_base = importlib.import_module("profiling_modules.base")
except ImportError as e:
    pytest.fail(f"Failed to import test subject module: {e}", pytrace=False)


@pytest.fixture
def mock_engine():
    """Provides a mock SQLAlchemy Engine and its connection."""
    engine = MagicMock()
    mock_connection = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_connection
    return engine, mock_connection


class TestGetTableNames:
    """Tests for the get_table_names function."""

    def test_success(self, mock_engine):
        """Test it returns a list of tables on success."""
        engine, mock_connection = mock_engine
        schema_name = "public"
        expected_tables = ["table1", "table2"]
        mock_connection.execute.return_value = [(t,) for t in expected_tables]

        tables = profiling_base.get_table_names(engine, schema_name)

        assert tables == expected_tables
        mock_connection.execute.assert_called_once()

    def test_empty_result(self, mock_engine):
        """Test it returns an empty list when no tables are found."""
        engine, mock_connection = mock_engine
        mock_connection.execute.return_value = []
        tables = profiling_base.get_table_names(engine, "public")
        assert tables == []

    def test_db_error(self, mock_engine, caplog):
        """Test it returns an empty list and logs an error on DB exception."""
        engine, mock_connection = mock_engine
        mock_connection.execute.side_effect = SQLAlchemyError("Connection failed")
        with caplog.at_level(logging.ERROR):
            tables = profiling_base.get_table_names(engine, "public")

        assert tables == []
        assert "Failed to get table names" in caplog.text


class TestGetViewNames:
    """Tests for the get_view_names function."""

    def test_success(self, mock_engine):
        """Test it returns a list of views on success."""
        engine, mock_connection = mock_engine
        schema_name = "public"
        expected_views = ["view1", "view2"]
        mock_connection.execute.return_value = [(v,) for v in expected_views]

        views = profiling_base.get_view_names(engine, schema_name)

        assert views == expected_views
        mock_connection.execute.assert_called_once()

    def test_db_error(self, mock_engine, caplog):
        """Test it returns an empty list and logs an error on DB exception."""
        engine, mock_connection = mock_engine
        mock_connection.execute.side_effect = SQLAlchemyError("Connection failed")
        with caplog.at_level(logging.ERROR):
            views = profiling_base.get_view_names(engine, "public")

        assert views == []
        assert "Failed to get view names" in caplog.text
