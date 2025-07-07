# -*- coding: utf-8 -*-
"""Unit tests for the benchmark database creation script."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy.engine import Engine

# --- Dynamic import of the script to be tested ---
try:
    TEST_DIR = Path(__file__).parent
    PROJECT_ROOT = TEST_DIR.parent.parent
    SRC_FILE = (
        PROJECT_ROOT / "phases" / "01_LegacyDB" / "src" / "01_create_benchmark_dbs.py"
    )

    spec = importlib.util.spec_from_file_location("create_benchmark_dbs", SRC_FILE)
    create_benchmark_dbs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(create_benchmark_dbs)

    # Import the functions we need to test
    Config = create_benchmark_dbs.Config

except Exception as e:
    print(f"Failed to import script: {e}")
    raise ImportError(f"Cannot import script from {SRC_FILE}") from e


@pytest.fixture
def mock_db_connection() -> MagicMock:
    """Provides a mock SQLAlchemy Connection object."""
    mock_conn = MagicMock(spec=Engine)
    mock_conn.execute.return_value = None
    # For context manager (`with engine.connect() as conn:`)
    mock_conn.__enter__.return_value = mock_conn
    return mock_conn


@pytest.fixture
def mock_create_engine(mock_db_connection: MagicMock) -> MagicMock:
    """Provides a mock SQLAlchemy create_engine function."""
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_db_connection
    return MagicMock(return_value=mock_engine)


@pytest.fixture
def mock_config() -> Config:
    """Provides a mock ConfigParser object with necessary test data."""
    return Config(
        host="localhost",
        port="5432",
        user="test_user",
        password="test_password",  # pragma: allowlist secret
        root_db="postgres",
        source_db="tmp_df9",
        benchmark_dbs=["tmp_benchmark_wide_numeric", "tmp_benchmark_wide_text_nulls"],
        sql_dir=Path("/fake/sql/dir"),
    )


class TestBenchmarkDBCreation:
    """Test suite for the benchmark database creation script."""

    @patch.object(create_benchmark_dbs, "check_pipeline_prerequisites")
    @patch.object(create_benchmark_dbs, "setup_logging")
    @patch.object(create_benchmark_dbs, "load_config")
    @patch.object(create_benchmark_dbs, "get_engine")
    @patch.object(create_benchmark_dbs, "verify_benchmark_database")
    @patch.object(create_benchmark_dbs, "parse_arguments")
    @patch("pathlib.Path.read_text")
    @patch("pandas.read_sql_query")
    def test_main_orchestration(
        self,
        mock_read_sql: MagicMock,
        mock_read_text: MagicMock,
        mock_parse_args: MagicMock,
        mock_verify_benchmark: MagicMock,
        mock_get_engine: MagicMock,
        mock_load_config: MagicMock,
        mock_setup_logging: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_config: Config,
    ) -> None:
        """
        Test the main orchestration function with all necessary mocks.
        """
        # Arrange
        mock_read_text.return_value = "SELECT 1;"
        mock_read_sql.return_value = pd.DataFrame({"col1": [1, 2]})
        mock_check_prereqs.return_value = (True, [])

        # Mock the engine and connection separately to handle multiple calls
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        # Mock verification functions
        with (
            patch("create_benchmark_dbs.verify_database_exists", return_value=False),
            patch("create_benchmark_dbs.create_database"),
            patch("create_benchmark_dbs.write_to_database", return_value=True),
            patch("create_benchmark_dbs.verify_benchmark_database", return_value=True),
            patch("create_benchmark_dbs.load_config", return_value=mock_config),
            patch("create_benchmark_dbs.parse_arguments") as mock_parse_args,
        ):
            mock_args = MagicMock()
            mock_args.verify_only = False
            mock_args.force_recreate = False
            mock_args.config = Path("config.ini")
            mock_parse_args.return_value = mock_args

            # Act
            create_benchmark_dbs.main()

            # Assert
            # Verify logging was set up
            mock_setup_logging.assert_called_once()

            # Verify prerequisites were checked
            mock_check_prereqs.assert_called_once()

            # Verify both SQL files were read
            assert mock_read_text.call_count == 2

            # Verify both transformation queries were executed
            assert mock_read_sql.call_count == 2

    @patch("create_benchmark_dbs.get_engine")
    def test_extract_transform_data_executes_query(
        self,
        mock_get_engine: MagicMock,
    ) -> None:
        """
        Tests that extract_transform_data executes the provided SQL query.

        Verifies that the function establishes a database connection using the
        engine and executes the given SQL query using pandas.read_sql_query.
        """
        # Arrange
        query_path = Path("/fake/query.sql")
        expected_df = pd.DataFrame({"id": [1], "data": ["test"]})

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        with (
            patch("pathlib.Path.read_text", return_value="SELECT * FROM test;"),
            patch("pandas.read_sql_query", return_value=expected_df) as mock_read_sql,
        ):
            # Act
            result_df = create_benchmark_dbs.extract_transform_data(
                mock_engine, query_path
            )

            # Assert
            mock_read_sql.assert_called_once_with("SELECT * FROM test;", mock_conn)
            pd.testing.assert_frame_equal(result_df, expected_df)

    @patch("create_benchmark_dbs.create_database")
    @patch("create_benchmark_dbs.get_engine")
    def test_write_to_database(
        self,
        mock_get_engine: MagicMock,
        mock_create_db: MagicMock,
    ) -> None:
        """
        Tests the write_to_database function.

        Verifies that the function uses pandas.DataFrame.to_sql to load the data
        and creates comprehensive indexes.
        """
        # Arrange
        test_df = pd.DataFrame({"id": [1, 2, 3]})
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
            # Act
            result = create_benchmark_dbs.write_to_database(test_df, mock_engine)

            # Assert
            assert result is True
            mock_to_sql.assert_called_once_with(
                "wide_format_data",
                mock_engine,
                if_exists="replace",
                index=False,
                chunksize=1000,
            )
            # Verify indexing SQL was executed
            assert mock_conn.execute.call_count >= 2  # Indexing + ANALYZE

    def test_map_db_to_sql_file(self):
        """Test the database to SQL file mapping function."""
        # Test numeric database mapping
        result = create_benchmark_dbs._map_db_to_sql_file("tmp_benchmark_wide_numeric")
        assert result == "flatten_df9.sql"

        # Test text_nulls database mapping
        result = create_benchmark_dbs._map_db_to_sql_file(
            "tmp_benchmark_wide_text_nulls"
        )
        assert result == "flatten_df9_text_nulls.sql"

        # Test invalid database name
        with pytest.raises(ValueError):
            create_benchmark_dbs._map_db_to_sql_file("invalid_db_name")

    @patch("create_benchmark_dbs.get_engine")
    @patch("create_benchmark_dbs.verify_benchmark_database_ready")
    def test_verify_benchmark_database_success(
        self,
        mock_verify_ready: MagicMock,
        mock_get_engine: MagicMock,
        mock_config: Config,
    ):
        """Test successful benchmark database verification."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_verify_ready.return_value = True

        result = create_benchmark_dbs.verify_benchmark_database(mock_config, "test_db")

        assert result is True
        mock_get_engine.assert_called_once_with(mock_config, dbname="test_db")
        mock_verify_ready.assert_called_once_with(mock_engine)

    @patch("create_benchmark_dbs.get_engine")
    @patch("create_benchmark_dbs.verify_benchmark_database_ready")
    def test_verify_benchmark_database_failure(
        self,
        mock_verify_ready: MagicMock,
        mock_get_engine: MagicMock,
        mock_config: Config,
    ):
        """Test benchmark database verification failure."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_verify_ready.return_value = False

        result = create_benchmark_dbs.verify_benchmark_database(mock_config, "test_db")

        assert result is False

    def test_load_config_success(self, tmp_path: Path):
        """Verify load_config correctly parses a valid INI file."""
        config_content = """
[postgresql]
host = localhost
port = 5432
user = test_user
password = test_password
root_db = postgres

[databases]
benchmark_dbs = tmp_benchmark_wide_numeric, tmp_benchmark_wide_text_nulls
benchmark_source_db = tmp_df9

[paths]
sql_queries_dir = ../sql/canonical_queries
"""  # pragma: allowlist secret
        config_file = tmp_path / "config.ini"
        config_file.write_text(config_content)

        config = create_benchmark_dbs.load_config(config_file)
        assert config.host == "localhost"
        assert config.password == "test_password"  # pragma: allowlist secret
        assert config.source_db == "tmp_df9"
        assert len(config.benchmark_dbs) == 2
        assert "tmp_benchmark_wide_numeric" in config.benchmark_dbs

    def test_parse_arguments_defaults(self):
        """Test that parse_arguments returns correct defaults."""
        with patch("sys.argv", ["01_create_benchmark_dbs.py"]):
            args = create_benchmark_dbs.parse_arguments()
            assert args.config == Path("config.ini")
            assert args.force_recreate is False
            assert args.verify_only is False

    def test_parse_arguments_custom(self):
        """Test that parse_arguments handles custom arguments."""
        with patch(
            "sys.argv",
            [
                "01_create_benchmark_dbs.py",
                "--config",
                "/custom/config.ini",
                "--force-recreate",
                "--verify-only",
            ],
        ):
            args = create_benchmark_dbs.parse_arguments()
            assert args.config == Path("/custom/config.ini")
            assert args.force_recreate is True
            assert args.verify_only is True

    @patch("create_benchmark_dbs.setup_logging")
    @patch("create_benchmark_dbs.load_config")
    @patch("create_benchmark_dbs.get_engine")
    @patch("create_benchmark_dbs.verify_database_exists")
    @patch("create_benchmark_dbs.verify_benchmark_database")
    @patch("create_benchmark_dbs.parse_arguments")
    def test_main_verify_only_mode(
        self,
        mock_parse_args: MagicMock,
        mock_verify_benchmark: MagicMock,
        mock_verify_exists: MagicMock,
        mock_get_engine: MagicMock,
        mock_load_config: MagicMock,
        mock_setup_logging: MagicMock,
        mock_config: Config,
    ):
        """Test main function in verify-only mode."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.verify_only = True
        mock_args.force_recreate = False
        mock_args.config = Path("config.ini")
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_verify_exists.return_value = True
        mock_verify_benchmark.return_value = True

        # Execute
        create_benchmark_dbs.main()

        # Verify
        mock_setup_logging.assert_called_once()
        mock_load_config.assert_called_once_with(mock_args.config)
        mock_get_engine.assert_called_once_with(mock_config)
        assert mock_verify_exists.call_count == len(mock_config.benchmark_dbs)
        assert mock_verify_benchmark.call_count == len(mock_config.benchmark_dbs)

    @patch("create_benchmark_dbs.setup_logging")
    @patch("create_benchmark_dbs.load_config")
    @patch("create_benchmark_dbs.get_engine")
    @patch.object(create_benchmark_dbs, "check_pipeline_prerequisites")
    @patch.object(create_benchmark_dbs, "verify_database_exists")
    @patch.object(create_benchmark_dbs, "create_database")
    @patch.object(create_benchmark_dbs, "extract_transform_data")
    @patch.object(create_benchmark_dbs, "write_to_database")
    @patch.object(create_benchmark_dbs, "verify_benchmark_database")
    @patch.object(create_benchmark_dbs, "parse_arguments")
    def test_main_create_mode(
        self,
        mock_parse_args: MagicMock,
        mock_verify_benchmark: MagicMock,
        mock_write_to_db: MagicMock,
        mock_extract_transform: MagicMock,
        mock_create: MagicMock,
        mock_verify_exists: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_get_engine: MagicMock,
        mock_load_config: MagicMock,
        mock_setup_logging: MagicMock,
        mock_config: Config,
    ):
        """Test main function in create mode."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.verify_only = False
        mock_args.force_recreate = False
        mock_args.config = Path("config.ini")
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_check_prereqs.return_value = (True, [])
        mock_verify_exists.return_value = False  # Database doesn't exist
        mock_extract_transform.return_value = pd.DataFrame({"col": [1, 2, 3]})
        mock_write_to_db.return_value = True  # Write succeeds
        mock_verify_benchmark.return_value = True  # Verification succeeds

        # Execute
        create_benchmark_dbs.main()

        # Verify
        mock_setup_logging.assert_called_once()
        mock_load_config.assert_called_once_with(mock_args.config)
        mock_check_prereqs.assert_called_once()
        assert mock_create.call_count == len(mock_config.benchmark_dbs)
        assert mock_extract_transform.call_count == len(mock_config.benchmark_dbs)
        assert mock_write_to_db.call_count == len(mock_config.benchmark_dbs)
        assert mock_verify_benchmark.call_count == len(mock_config.benchmark_dbs)
