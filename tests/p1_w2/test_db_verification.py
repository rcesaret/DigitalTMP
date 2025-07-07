# -*- coding: utf-8 -*-
"""
Tests for the db_verification.py module.

This test suite validates the functionality of the database verification utilities
that ensure pipeline idempotency and robust execution.
"""

import importlib.util
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import exc
from sqlalchemy.engine import Engine

# --- Dynamic import of the script to be tested ---
try:
    TEST_DIR = Path(__file__).parent
    PROJECT_ROOT = TEST_DIR.parent.parent
    SRC_FILE = PROJECT_ROOT / "phases" / "01_LegacyDB" / "src" / "db_verification.py"

    spec = importlib.util.spec_from_file_location("db_verification", SRC_FILE)
    db_verification = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_verification)

    # Import the functions we need to test
    verify_database_exists = db_verification.verify_database_exists
    verify_schema_populated = db_verification.verify_schema_populated
    verify_benchmark_database_ready = db_verification.verify_benchmark_database_ready
    check_pipeline_prerequisites = db_verification.check_pipeline_prerequisites
    verify_full_pipeline_state = db_verification.verify_full_pipeline_state

except Exception as e:
    print(f"Failed to import script: {e}")
    raise ImportError(f"Cannot import script from {SRC_FILE}") from e


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_engine() -> Engine:
    """Return a mock SQLAlchemy Engine."""
    engine = MagicMock(spec=Engine)
    engine.url = MagicMock()
    engine.url.__str__ = MagicMock(return_value="postgresql://user:pass@host:5432/db")
    return engine


@pytest.fixture
def mock_connection():
    """Return a mock SQLAlchemy Connection."""
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=None)
    return conn


@pytest.fixture
def mock_config():
    """Return a mock configuration object."""
    config = MagicMock()
    config.user = "test_user"
    config.password = "test_password"  # pragma: allowlist secret
    config.host = "localhost"
    config.port = "5432"
    config.root_db = "postgres"
    config.source_db = "tmp_df9"
    config.legacy_dbs = ["tmp_df8", "tmp_df9", "tmp_df10", "tmp_rean_df2"]
    config.benchmark_dbs = [
        "tmp_benchmark_wide_numeric",
        "tmp_benchmark_wide_text_nulls",
    ]
    config.sql_dir = Path("/fake/sql/dir")
    return config


# ---------------------------------------------------------------------------
# Tests for verify_database_exists
# ---------------------------------------------------------------------------


class TestVerifyDatabaseExists:
    """Tests for the verify_database_exists function."""

    def test_database_exists_returns_true(self, mock_engine, mock_connection):
        """Test that function returns True when database exists and is accessible."""
        # Mock database existence query
        mock_connection.execute.return_value.scalar.return_value = 1
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        # Mock test connection to the database
        with patch.object(db_verification, "create_engine") as mock_create_engine:
            mock_test_engine = MagicMock()
            mock_create_engine.return_value = mock_test_engine
            mock_test_conn = (
                mock_test_engine.connect.return_value.__enter__.return_value
            )
            mock_test_conn.execute.return_value = None

            result = verify_database_exists(mock_engine, "test_db")

            assert result is True
            mock_connection.execute.assert_called_once()
            mock_create_engine.assert_called_once()

    def test_database_does_not_exist(self, mock_engine, mock_connection):
        """Test that function returns False when database does not exist."""
        mock_connection.execute.return_value.scalar.return_value = None
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        result = verify_database_exists(mock_engine, "nonexistent_db")

        assert result is False
        mock_connection.execute.assert_called_once()

    def test_database_connection_error(self, mock_engine, mock_connection, caplog):
        """Test that function handles connection errors gracefully."""
        mock_connection.execute.side_effect = exc.SQLAlchemyError("Connection failed")
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with caplog.at_level(logging.ERROR):
            result = verify_database_exists(mock_engine, "test_db")

        assert result is False
        assert "Failed to verify database" in caplog.text


# ---------------------------------------------------------------------------
# Tests for verify_schema_populated
# ---------------------------------------------------------------------------


class TestVerifySchemaPopulated:
    """Tests for the verify_schema_populated function."""

    def test_schema_properly_populated(self, mock_engine, mock_connection):
        """Test that function returns True for properly populated schema."""
        # Set up the mock to handle the sequence of queries:
        # 1. Schema existence check
        # 2. Table listing query
        # 3. Row count queries for each table

        # Mock the execute method to return different results
        def mock_execute(query, params=None):
            query_str = str(query)
            mock_result = MagicMock()

            if "information_schema.schemata" in query_str:
                # Schema existence check
                mock_result.scalar.return_value = 1
            elif "information_schema.tables" in query_str:
                # Table listing query - make result iterable
                mock_result.__iter__ = lambda self: iter([
                    ("table1",),
                    ("table2",),
                    ("table3",),
                ])
            elif "COUNT(*)" in query_str:
                # Row count queries - return different counts for each table
                if "table1" in query_str:
                    mock_result.scalar.return_value = 100
                elif "table2" in query_str:
                    mock_result.scalar.return_value = 200
                elif "table3" in query_str:
                    mock_result.scalar.return_value = 150
                else:
                    mock_result.scalar.return_value = 100  # Default

            return mock_result

        mock_connection.execute.side_effect = mock_execute
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        is_populated, table_stats = verify_schema_populated(
            mock_engine, "test_schema", min_tables=2
        )

        assert is_populated is True
        assert len(table_stats) == 3
        assert table_stats["table1"] == 100
        assert table_stats["table2"] == 200
        assert table_stats["table3"] == 150

    def test_schema_does_not_exist(self, mock_engine, mock_connection, caplog):
        """Test that function returns False when schema does not exist."""

        def mock_execute(query, params=None):
            mock_result = MagicMock()
            mock_result.scalar.return_value = None  # Schema doesn't exist
            return mock_result

        mock_connection.execute.side_effect = mock_execute
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with caplog.at_level(logging.ERROR):
            is_populated, table_stats = verify_schema_populated(
                mock_engine, "nonexistent_schema"
            )

        assert is_populated is False
        assert table_stats == {}
        assert "does not exist" in caplog.text

    def test_schema_insufficient_tables(self, mock_engine, mock_connection, caplog):
        """Test that function returns False with insufficient tables."""

        def mock_execute(query, params=None):
            query_str = str(query)
            mock_result = MagicMock()

            if "information_schema.schemata" in query_str:
                # Schema exists
                mock_result.scalar.return_value = 1
            elif "information_schema.tables" in query_str:
                # Only one table when 3 are required - make iterable
                mock_result.__iter__ = lambda self: iter([("table1",)])

            return mock_result

        mock_connection.execute.side_effect = mock_execute
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with caplog.at_level(logging.ERROR):
            is_populated, table_stats = verify_schema_populated(
                mock_engine, "test_schema", min_tables=3
            )

        assert is_populated is False
        assert "has 1 tables, expected at least 3" in caplog.text

    def test_schema_connection_error(self, mock_engine, mock_connection, caplog):
        """Test that function handles connection errors gracefully."""
        mock_connection.execute.side_effect = exc.SQLAlchemyError("Connection failed")
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with caplog.at_level(logging.ERROR):
            is_populated, table_stats = verify_schema_populated(
                mock_engine, "test_schema"
            )

        assert is_populated is False
        assert table_stats == {}
        assert "Failed to verify schema" in caplog.text


# ---------------------------------------------------------------------------
# Tests for verify_benchmark_database_ready
# ---------------------------------------------------------------------------


class TestVerifyBenchmarkDatabaseReady:
    """Tests for the verify_benchmark_database_ready function."""

    def test_benchmark_database_ready(self, mock_engine, mock_connection):
        """Test that function returns True for ready benchmark database."""
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        # Mock the sequence of queries: table exists, row count, index count, stats
        mock_connection.execute.return_value.scalar.side_effect = [
            1,  # Table exists
            1000,  # Row count
            10,  # Index count
        ]

        # Mock stats query
        mock_connection.execute.return_value.fetchone.return_value = (
            "2024-01-01 12:00:00",  # last_analyze
            "2024-01-01 11:00:00",  # last_autoanalyze
        )

        result = verify_benchmark_database_ready(mock_engine, "wide_format_data")

        assert result is True

    def test_benchmark_table_does_not_exist(self, mock_engine, mock_connection, caplog):
        """Test that function returns False when benchmark table does not exist."""
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value.scalar.return_value = (
            None  # Table doesn't exist
        )

        with caplog.at_level(logging.ERROR):
            result = verify_benchmark_database_ready(mock_engine, "nonexistent_table")

        assert result is False
        assert "does not exist" in caplog.text

    def test_benchmark_table_empty(self, mock_engine, mock_connection, caplog):
        """Test that function returns False when benchmark table is empty."""
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value.scalar.side_effect = [
            1,  # Table exists
            0,  # Row count is 0
        ]

        with caplog.at_level(logging.ERROR):
            result = verify_benchmark_database_ready(mock_engine, "empty_table")

        assert result is False
        assert "is empty" in caplog.text

    def test_benchmark_few_indexes_warning(self, mock_engine, mock_connection, caplog):
        """Test that function warns about insufficient indexes but returns True."""
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value.scalar.side_effect = [
            1,  # Table exists
            1000,  # Row count
            2,  # Few indexes
        ]

        # Mock stats query - no stats available
        mock_connection.execute.return_value.fetchone.return_value = (None, None)

        with caplog.at_level(logging.WARNING):
            result = verify_benchmark_database_ready(mock_engine, "test_table")

        assert result is True
        assert "has only 2 indexes" in caplog.text
        assert "statistics may be outdated" in caplog.text

    def test_benchmark_database_connection_error(
        self, mock_engine, mock_connection, caplog
    ):
        """Test that function handles connection errors gracefully."""
        mock_connection.execute.side_effect = exc.SQLAlchemyError("Connection failed")
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with caplog.at_level(logging.ERROR):
            result = verify_benchmark_database_ready(mock_engine, "test_table")

        assert result is False
        assert "Failed to verify benchmark database" in caplog.text


# ---------------------------------------------------------------------------
# Tests for check_pipeline_prerequisites
# ---------------------------------------------------------------------------


class TestCheckPipelinePrerequisites:
    """Tests for the check_pipeline_prerequisites function."""

    @patch.object(db_verification, "create_engine")
    @patch.object(db_verification, "verify_database_exists")
    @patch.object(db_verification, "verify_schema_populated")
    def test_prerequisites_met_for_benchmark_creation(
        self,
        mock_verify_schema: MagicMock,
        mock_verify_db: MagicMock,
        mock_create_engine: MagicMock,
        mock_config,
    ):
        """Test prerequisites check for benchmark database creation script."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_verify_db.return_value = True
        mock_verify_schema.return_value = (True, {"table1": 100, "table2": 200})

        prereqs_met, errors = check_pipeline_prerequisites(
            mock_config, "01_create_benchmark_dbs.py"
        )

        assert prereqs_met is True
        assert len(errors) == 0
        mock_verify_db.assert_called_once()
        mock_verify_schema.assert_called_once()

    @patch.object(db_verification, "create_engine")
    @patch.object(db_verification, "verify_database_exists")
    def test_prerequisites_not_met_missing_database(
        self,
        mock_verify_db: MagicMock,
        mock_create_engine: MagicMock,
        mock_config,
        caplog,
    ):
        """Test prerequisites check when source database is missing."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_verify_db.return_value = False

        with caplog.at_level(logging.ERROR):
            prereqs_met, errors = check_pipeline_prerequisites(
                mock_config, "01_create_benchmark_dbs.py"
            )

        assert prereqs_met is False
        assert len(errors) > 0
        assert "does not exist or is not accessible" in errors[0]

    @patch.object(db_verification, "create_engine")
    @patch.object(db_verification, "verify_database_exists")
    def test_prerequisites_profiling_pipeline(
        self,
        mock_verify_db: MagicMock,
        mock_create_engine: MagicMock,
        mock_config,
    ):
        """Test prerequisites check for profiling pipeline script."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_verify_db.return_value = True

        prereqs_met, errors = check_pipeline_prerequisites(
            mock_config, "02_run_profiling_pipeline.py"
        )

        assert prereqs_met is True
        assert len(errors) == 0
        # Should check all databases (legacy + benchmark)
        expected_calls = len(mock_config.legacy_dbs) + len(mock_config.benchmark_dbs)
        assert mock_verify_db.call_count == expected_calls

    @patch.object(db_verification, "create_engine")
    @patch("pathlib.Path.exists")
    def test_prerequisites_comparison_script_missing_metrics(
        self,
        mock_path_exists: MagicMock,
        mock_create_engine: MagicMock,
        mock_config,
    ):
        """Test prerequisites check for comparison script when metrics are missing."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_path_exists.return_value = False

        prereqs_met, errors = check_pipeline_prerequisites(
            mock_config, "04_run_comparison.py"
        )

        assert prereqs_met is False
        assert len(errors) > 0
        assert "Metrics directory does not exist" in errors[0]

    def test_prerequisites_unknown_script(self, mock_config):
        """Test prerequisites check for unknown script name."""
        prereqs_met, errors = check_pipeline_prerequisites(
            mock_config, "unknown_script.py"
        )

        # Should pass since no specific checks are defined for unknown scripts
        assert prereqs_met is True
        assert len(errors) == 0

    @patch.object(db_verification, "create_engine")
    def test_prerequisites_connection_error(
        self,
        mock_create_engine: MagicMock,
        mock_config,
    ):
        """Test prerequisites check when database connection fails."""
        mock_create_engine.side_effect = Exception("Connection failed")

        prereqs_met, errors = check_pipeline_prerequisites(
            mock_config, "01_create_benchmark_dbs.py"
        )

        assert prereqs_met is False
        assert len(errors) > 0
        assert "Failed to check prerequisites" in errors[0]


# ---------------------------------------------------------------------------
# Tests for verify_full_pipeline_state
# ---------------------------------------------------------------------------


class TestVerifyFullPipelineState:
    """Tests for the verify_full_pipeline_state function."""

    @patch.object(db_verification, "create_engine")
    @patch.object(db_verification, "verify_database_exists")
    @patch.object(db_verification, "verify_schema_populated")
    @patch.object(db_verification, "verify_benchmark_database_ready")
    def test_full_pipeline_state_all_complete(
        self,
        mock_verify_benchmark: MagicMock,
        mock_verify_schema: MagicMock,
        mock_verify_db: MagicMock,
        mock_create_engine: MagicMock,
        mock_config,
    ):
        """Test full pipeline state when all stages are complete."""
        # Mock database operations
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_verify_db.return_value = True
        mock_verify_schema.return_value = (True, {"table1": 100})
        mock_verify_benchmark.return_value = True

        # Create mock directory objects
        mock_metrics_dir = MagicMock()
        mock_metrics_dir.exists.return_value = True
        mock_metrics_dir.glob.side_effect = (
            lambda pattern: [f"file{i}.csv" for i in range(6)]
            if pattern == "*.csv"
            else [f"file{i}.json" for i in range(6)]
        )

        mock_erds_dir = MagicMock()
        mock_erds_dir.exists.return_value = True
        mock_erds_dir.glob.return_value = ["erd1.svg", "erd2.svg"]

        mock_reports_dir = MagicMock()
        mock_reports_dir.exists.return_value = True
        mock_reports_dir.glob.side_effect = (
            lambda pattern: ["report.csv"] if pattern == "*.csv" else ["report.md"]
        )

        # Mock the parent directory structure
        mock_parent = MagicMock()
        mock_outputs = MagicMock()

        # Set up directory navigation
        mock_outputs.__truediv__ = lambda _, subdir: {
            "metrics": mock_metrics_dir,
            "erds": mock_erds_dir,
            "reports": mock_reports_dir,
        }.get(str(subdir), MagicMock())

        mock_parent.__truediv__ = (
            lambda _, subdir: mock_outputs if str(subdir) == "outputs" else MagicMock()
        )

        # Replace the config's sql_dir.parent with our mock
        mock_config.sql_dir = MagicMock()
        mock_config.sql_dir.parent = mock_parent

        state = verify_full_pipeline_state(mock_config)

        assert state["00_setup_databases"] is True
        assert state["01_create_benchmark_dbs"] is True
        assert state["02_run_profiling_pipeline"] is True
        assert state["03_generate_erds"] is True
        assert state["04_run_comparison"] is True

    @patch.object(db_verification, "create_engine")
    @patch.object(db_verification, "verify_database_exists")
    def test_full_pipeline_state_legacy_incomplete(
        self,
        mock_verify_db: MagicMock,
        mock_create_engine: MagicMock,
        mock_config,
    ):
        """Test full pipeline state when legacy databases are incomplete."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_verify_db.return_value = False  # Legacy databases don't exist

        state = verify_full_pipeline_state(mock_config)

        assert state["00_setup_databases"] is False
        # Other stages should still be checked but may also fail

    @patch.object(db_verification, "create_engine")
    def test_full_pipeline_state_connection_error(
        self,
        mock_create_engine: MagicMock,
        mock_config,
        caplog,
    ):
        """Test full pipeline state when connection fails."""
        mock_create_engine.side_effect = Exception("Connection failed")

        with caplog.at_level(logging.ERROR):
            state = verify_full_pipeline_state(mock_config)

        # Should return partial state
        assert isinstance(state, dict)
        assert "Failed to verify pipeline state" in caplog.text
