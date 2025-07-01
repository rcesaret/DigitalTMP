# -*- coding: utf-8 -*-
"""
Integration tests for the 01_create_benchmark_dbs.py script.

This test suite validates the functionality of the benchmark database creation
script, ensuring that it correctly connects to the database, executes SQL
transformation queries, and populates the target benchmark databases with the
expected data structure and content. Mocks are used to isolate the script from
live database dependencies, allowing for controlled and repeatable testing.
"""

import configparser
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy.engine import Connection

# Define the absolute path to the script under test
# This makes the test runner location-independent
SCRIPT_PATH = (
    Path(__file__).parent.parent.parent
    / "phases"
    / "01_LegacyDB"
    / "src"
    / "01_create_benchmark_dbs.py"
).resolve()


# Dynamically import the script to be tested
# This allows testing functions within the script as a module
try:
    spec = importlib.util.spec_from_file_location("create_benchmark_dbs", SCRIPT_PATH)
    if spec and spec.loader:
        create_benchmark_dbs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(create_benchmark_dbs)
    else:
        raise ImportError(f"Could not load spec for module at {SCRIPT_PATH}")
except FileNotFoundError:
    pytest.fail(
        f"The script under test was not found at the expected path: {SCRIPT_PATH}"
    )


@pytest.fixture
def mock_db_connection() -> MagicMock:
    """Provides a mock SQLAlchemy Connection object."""
    mock_conn = MagicMock(spec=Connection)
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
def mock_config() -> configparser.ConfigParser:
    """Provides a mock ConfigParser object with necessary test data."""
    config = configparser.ConfigParser()
    config["postgres"] = {
        "host": "localhost",
        "port": "5432",
        "user": "test_user",
        "db_credential": "test_password",  # Using non-sensitive key name
        "db_name": "tmp_df9",
    }
    config["benchmark_dbs"] = {
        "numeric_db_name": "tmp_benchmark_wide_numeric",
        "text_nulls_db_name": "tmp_benchmark_wide_text_nulls",
    }
    config["sql_paths"] = {
        "flatten_numeric": "path/to/fake_flatten_df9.sql",
        "flatten_text_nulls": "path/to/fake_flatten_df9_text_nulls.sql",
    }
    return config


class TestBenchmarkDBCreation:
    """Test suite for the benchmark database creation script."""

    @patch("create_benchmark_dbs.create_engine")
    @patch("create_benchmark_dbs.pd.read_sql_query")
    @patch("create_benchmark_dbs.Path.read_text")
    @patch("create_benchmark_dbs.setup_logging")
    def test_main_orchestration(
        self,
        mock_setup_logging: MagicMock,
        mock_read_text: MagicMock,
        mock_read_sql: MagicMock,
        mock_create_engine_func: MagicMock,
        mock_config: configparser.ConfigParser,
    ) -> None:
        """
        Tests the main function's orchestration logic.

        Verifies that the main function correctly parses the config, reads the
        SQL files, connects to the database, executes the queries, and calls
        the data loading function for both benchmark databases. It also checks
        that the row count of the transformed data is consistent.
        """
        # Arrange
        mock_read_text.return_value = "SELECT 1;"
        mock_read_sql.return_value = pd.DataFrame({"col1": [1, 2]})

        # Mock the engine and connection separately to handle multiple calls
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn
        mock_create_engine_func.return_value = mock_engine

        # Mock the function that loads data into the new DBs
        with patch("create_benchmark_dbs.load_data_to_db") as mock_load_data:
            # Act
            create_benchmark_dbs.main(mock_config)

            # Assert
            # Verify logging was set up
            mock_setup_logging.assert_called_once()

            # Verify both SQL files were read
            assert mock_read_text.call_count == 2

            # Verify both transformation queries were executed
            assert mock_read_sql.call_count == 2

            # Verify data was loaded into both benchmark databases
            assert mock_load_data.call_count == 2
            numeric_db_name = mock_config["benchmark_dbs"]["numeric_db_name"]
            text_db_name = mock_config["benchmark_dbs"]["text_nulls_db_name"]

            # Check that load_data_to_db was called for the numeric DB
            mock_load_data.assert_any_call(
                mock_read_sql.return_value, numeric_db_name, mock_config
            )
            # Check that load_data_to_db was called for the text/nulls DB
            mock_load_data.assert_any_call(
                mock_read_sql.return_value, text_db_name, mock_config
            )

            # Verify row count consistency
            call_args_list = mock_load_data.call_args_list
            for call in call_args_list:
                df_arg = call.args[0]
                assert len(df_arg) == len(mock_read_sql.return_value)

    @patch("create_benchmark_dbs.create_engine")
    def test_transform_data_executes_query(
        self,
        mock_create_engine_func: MagicMock,
        mock_config: configparser.ConfigParser,
    ) -> None:
        """
        Tests that transform_data executes the provided SQL query.

        Verifies that the function establishes a database connection using the
        config and executes the given SQL query using pandas.read_sql_query.
        """
        # Arrange
        sql_query = "SELECT * FROM test_table;"
        expected_df = pd.DataFrame({"id": [1], "data": ["test"]})

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn
        mock_create_engine_func.return_value = mock_engine

        with patch(
            "create_benchmark_dbs.pd.read_sql_query", return_value=expected_df
        ) as mock_read_sql:
            # Act
            result_df = create_benchmark_dbs.transform_data(sql_query, mock_config)

            # Assert
            conn_str = create_benchmark_dbs.get_db_connection_string(
                mock_config, "postgres"
            )
            mock_create_engine_func.assert_called_once_with(conn_str)
            mock_read_sql.assert_called_once_with(sql_query, mock_engine.connect())
            pd.testing.assert_frame_equal(result_df, expected_df)

    @patch("create_benchmark_dbs.create_database_if_not_exists")
    @patch("create_benchmark_dbs.create_engine")
    def test_load_data_to_db(
        self,
        mock_create_engine_func: MagicMock,
        mock_create_db: MagicMock,
        mock_config: configparser.ConfigParser,
    ) -> None:
        """
        Tests the load_data_to_db function.

        Verifies that the function creates the target database, establishes a
        connection, and uses pandas.DataFrame.to_sql to load the data.
        """
        # Arrange
        test_df = pd.DataFrame({"id": [1, 2, 3]})
        db_name = "test_target_db"
        mock_engine = MagicMock()
        mock_create_engine_func.return_value = mock_engine

        with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
            # Act
            create_benchmark_dbs.load_data_to_db(test_df, db_name, mock_config)

            # Assert
            mock_create_db.assert_called_once_with(db_name, mock_config)
            target_conn_str = create_benchmark_dbs.get_db_connection_string(
                mock_config, "postgres", db_name=db_name
            )
            mock_create_engine_func.assert_called_with(target_conn_str)
            mock_to_sql.assert_called_once_with(
                name=db_name,
                con=mock_engine,
                if_exists="replace",
                index=False,
                method="multi",
            )
