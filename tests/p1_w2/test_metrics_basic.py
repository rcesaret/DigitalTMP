# -*- coding: utf-8 -*-
"""Unit tests for the basic metrics profiling module."""

import importlib
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory of 'profiling_modules' to the system path
# to allow for package-based imports
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
module_src_path = project_root / "phases" / "01_LegacyDB" / "src"
sys.path.insert(0, str(module_src_path))

# Import the module using its package path
try:
    metrics_basic = importlib.import_module("profiling_modules.metrics_basic")
except ImportError as e:
    pytest.fail(f"Failed to import test subject module: {e}", pytrace=False)


@pytest.fixture
def mock_engine():
    """Provides a mock SQLAlchemy Engine and its connection."""
    engine = MagicMock()
    mock_connection = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_connection
    return engine, mock_connection


class TestGetBasicDbMetrics:
    """Tests for the get_basic_db_metrics function."""

    def test_success(self, mock_engine):
        """Test successful retrieval of basic DB metrics."""
        engine, mock_connection = mock_engine
        db_name = "test_db"
        db_size = 123.45

        mock_connection.execute.return_value.scalar_one.side_effect = [db_name, db_size]

        metrics = metrics_basic.get_basic_db_metrics(engine)

        assert metrics["database_name"] == db_name
        assert metrics["database_size_mb"] == db_size
        assert mock_connection.execute.call_count == 2

    def test_db_error(self, mock_engine, caplog):
        """Test it returns defaults and logs on DB exception."""
        engine, mock_connection = mock_engine
        mock_connection.execute.side_effect = SQLAlchemyError("DB connection failed")

        with caplog.at_level(logging.ERROR):
            metrics = metrics_basic.get_basic_db_metrics(engine)

        assert metrics["database_name"] is None
        assert metrics["database_size_mb"] is None
        assert "Failed to retrieve basic DB metrics" in caplog.text


class TestGetSchemaObjectCounts:
    """Tests for the get_schema_object_counts function."""

    @patch("profiling_modules.metrics_basic.get_view_names")
    @patch("profiling_modules.metrics_basic.get_table_names")
    def test_success(self, mock_get_tables, mock_get_views, mock_engine):
        """Test successful retrieval of schema object counts."""
        engine, mock_connection = mock_engine
        schema_name = "public"

        mock_get_tables.return_value = ["table1", "table2"]
        mock_get_views.return_value = ["view1"]
        mock_connection.execute.return_value.scalar_one.side_effect = [20, 2]

        counts = metrics_basic.get_schema_object_counts(engine, schema_name)

        assert counts["table_count"] == 2
        assert counts["view_count"] == 1
        assert counts["function_count"] == 20
        assert counts["sequence_count"] == 2

    @patch(
        "profiling_modules.metrics_basic.get_table_names",
        side_effect=SQLAlchemyError("Query failed"),
    )
    def test_db_error(self, mock_get_tables, mock_engine, caplog):
        """Test it returns defaults and logs on DB exception."""
        engine, _ = mock_engine
        schema_name = "public"

        with caplog.at_level(logging.ERROR):
            counts = metrics_basic.get_schema_object_counts(engine, schema_name)

        assert counts["table_count"] == 0
        assert "Failed to retrieve object counts" in caplog.text
