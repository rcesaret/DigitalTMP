# -*- coding: utf-8 -*-
"""Unit tests for the interoperability metrics profiling module."""

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
    metrics_interop = importlib.import_module("profiling_modules.metrics_interop")
except ImportError as e:
    pytest.fail(f"Failed to import test subject module: {e}", pytrace=False)


@pytest.fixture
def mock_engine():
    """Provides a mock SQLAlchemy Engine and its connection."""
    engine = MagicMock()
    mock_connection = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_connection
    return engine, mock_connection


class TestCalculateInteroperabilityMetrics:
    """Tests for the calculate_interoperability_metrics function."""

    def test_success(self, mock_engine):
        """Test successful calculation of all interoperability metrics."""
        engine, mock_connection = mock_engine
        schema_name = "public"

        # Mock return values: fk_count, table_count, lif_count
        mock_connection.execute.return_value.scalar_one.side_effect = [10, 5, 8]

        metrics = metrics_interop.calculate_interoperability_metrics(
            engine, schema_name
        )

        assert metrics["jdi"] == 1.0
        assert metrics["lif"] == 8
        assert metrics["nf"] == 0.73

    def test_single_table_schema(self, mock_engine):
        """Test JDI is 0 for a schema with only one table."""
        engine, mock_connection = mock_engine
        mock_connection.execute.return_value.scalar_one.side_effect = [0, 1, 0]
        metrics = metrics_interop.calculate_interoperability_metrics(engine, "public")
        assert metrics["jdi"] == 0.0

    def test_jdi_db_error(self, mock_engine, caplog):
        """Test it logs an error if JDI calculation fails."""
        engine, mock_connection = mock_engine
        mock_connection.execute.side_effect = SQLAlchemyError("JDI query failed")
        with caplog.at_level(logging.ERROR):
            metrics = metrics_interop.calculate_interoperability_metrics(
                engine, "public"
            )
        assert metrics["jdi"] is None
        assert "Failed to calculate JDI" in caplog.text

    def test_lif_db_error(self, mock_engine, caplog):
        """Test it logs an error if LIF calculation fails."""
        engine, mock_connection = mock_engine
        mock_connection.execute.return_value.scalar_one.side_effect = [
            10,
            5,
            SQLAlchemyError("LIF query failed"),
        ]
        with caplog.at_level(logging.ERROR):
            metrics = metrics_interop.calculate_interoperability_metrics(
                engine, "public"
            )
        assert metrics["lif"] is None
        assert "Failed to calculate LIF" in caplog.text
