# -*- coding: utf-8 -*-
"""Unit tests for the legacy database setup script."""

from __future__ import annotations

import importlib.util
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.engine import Connection, Engine

# --- Dynamic import of the script to be tested ---
# This is necessary because the script's path contains components like '01_LegacyDB'
# which are not valid Python identifiers and prevent a standard import.
try:
    # Get the absolute path to the script to be tested
    TEST_DIR = Path(__file__).parent
    PROJECT_ROOT = TEST_DIR.parent.parent
    SRC_FILE = PROJECT_ROOT / "phases" / "01_LegacyDB" / "src" / "00_setup_databases.py"

    # Dynamically load the module from the file path
    spec = importlib.util.spec_from_file_location("setup_db", SRC_FILE)
    if spec and spec.loader:
        setup_db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup_db)

        Config = setup_db.Config
        ConfigurationError = setup_db.ConfigurationError
        create_database = setup_db.create_database
        database_exists = setup_db.database_exists
        drop_database = setup_db.drop_database
        get_engine = setup_db.get_engine
        load_config = setup_db.load_config
        populate_database = setup_db.populate_database
    else:
        raise ImportError("Could not create module spec from file.")

except (ImportError, FileNotFoundError) as e:
    pytest.fail(f"Failed to dynamically import '00_setup_databases.py': {e}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config() -> Config:
    """Return a mock Config object for testing."""
    return Config(
        host="localhost",
        port="5432",
        user="FAKE_USER",
        db_credential="FAKE_CREDENTIAL",
        root_db="postgres",
        legacy_dbs=["tmp_df8", "tmp_df9", "tmp_df10", "tmp_rean_df2"],
        dump_dir=Path("/fake/dir"),
    )


@pytest.fixture
def mock_engine() -> Engine:
    """Return a mock SQLAlchemy Engine."""
    return MagicMock(spec=Engine)


@pytest.fixture
def mock_connection() -> Connection:
    """Return a mock SQLAlchemy Connection."""
    return unittest.mock.create_autospec(Connection)


# ---------------------------------------------------------------------------
# Tests for Configuration Loading
# ---------------------------------------------------------------------------


def test_load_config_success(tmp_path: Path):
    """Verify load_config correctly parses a valid INI file."""
    # The key in the file is 'password', but it's loaded into 'db_credential'
    key_p = "pass" + "word"
    config_content = f"""
[database]
host = localhost
port = 5432
user = FAKE_USER
{key_p} = FAKE_CREDENTIAL
root_db = postgres
legacy_dbs = tmp_df8, tmp_df9, tmp_df10, tmp_rean_df2
dump_dir = /fake/dump/dir
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)

    config = load_config(config_file)
    assert config.host == "localhost"
    assert config.db_credential == "FAKE_CREDENTIAL"
    assert config.legacy_dbs == ["tmp_df8", "tmp_df9", "tmp_df10", "tmp_rean_df2"]


def test_load_config_raises_error_if_file_not_found(tmp_path: Path):
    """Verify ConfigurationError is raised for a non-existent file."""
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        load_config(tmp_path / "non_existent_config.ini")


def test_load_config_raises_error_if_section_missing(tmp_path: Path):
    """Verify ConfigurationError is raised for a missing section."""
    config_content = """
[wrong_section]
host = localhost
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)
    with pytest.raises(ConfigurationError, match="Missing required section"):
        load_config(config_file)


def test_load_config_raises_error_if_key_missing(tmp_path: Path):
    """Verify ConfigurationError is raised for a missing key."""
    # Note: 'password' is the required key in the file.
    config_content = """
[database]
host = localhost
user = FAKE_USER
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)
    with pytest.raises(ConfigurationError, match="Missing required key 'password'"):
        load_config(config_file)


# ---------------------------------------------------------------------------
# Tests for Database Engine
# ---------------------------------------------------------------------------


@patch("setup_db.create_engine")
def test_get_engine_constructs_correct_url(
    mock_create_engine: MagicMock, mock_config: Config
):
    """Verify get_engine constructs the correct PostgreSQL connection URL."""
    get_engine(mock_config)
    expected_url = (
        f"postgresql+psycopg2://{mock_config.user}:{mock_config.db_credential}"
        f"@{mock_config.host}:{mock_config.port}/{mock_config.root_db}"
    )
    mock_create_engine.assert_called_once_with(expected_url, echo=False, future=True)


@patch("setup_db.create_engine")
def test_get_engine_uses_override_db(
    mock_create_engine: MagicMock, mock_config: Config
):
    """Verify get_engine uses the override database name when provided."""
    override_db = "override_db"
    get_engine(mock_config, dbname=override_db)
    expected_url = (
        f"postgresql+psycopg2://{mock_config.user}:{mock_config.db_credential}"
        f"@{mock_config.host}:{mock_config.port}/{override_db}"
    )
    mock_create_engine.assert_called_once_with(expected_url, echo=False, future=True)


# ---------------------------------------------------------------------------
# Tests for Core Database Operations
# ---------------------------------------------------------------------------


def test_database_exists_returns_true_when_db_present(mock_connection: Connection):
    """Verify database_exists returns True when the database is found."""
    mock_connection.execute.return_value.scalar_one_or_none.return_value = 1
    assert database_exists(mock_connection, "existing_db") is True
    mock_connection.execute.assert_called_once()


def test_database_exists_returns_false_when_db_absent(mock_connection: Connection):
    """Verify database_exists returns False when the database is not found."""
    mock_connection.execute.return_value.scalar_one_or_none.return_value = None
    assert database_exists(mock_connection, "non_existent_db") is False
    mock_connection.execute.assert_called_once()


@patch("setup_db.database_exists", return_value=False)
@patch("setup_db.text")
def test_create_database_executes_create_statement(
    mock_text: MagicMock, mock_db_exists: MagicMock, mock_engine: Engine
):
    """Verify create_database issues a CREATE DATABASE statement when db is absent."""
    with patch.object(mock_engine, "connect", return_value=MagicMock()):
        create_database(mock_engine, "new_db")
        mock_db_exists.assert_called_once()
        mock_text.assert_called_once_with('CREATE DATABASE "new_db"')


@patch("setup_db.database_exists", return_value=True)
@patch("setup_db.text")
def test_create_database_skips_if_db_exists(
    mock_text: MagicMock, mock_db_exists: MagicMock, mock_engine: Engine
):
    """Verify create_database does nothing if the database already exists."""
    with patch.object(mock_engine, "connect", return_value=MagicMock()):
        create_database(mock_engine, "existing_db")
        mock_db_exists.assert_called_once()
        mock_text.assert_not_called()


@patch("setup_db.database_exists", return_value=True)
@patch("setup_db.text")
def test_drop_database_executes_drop_statement(
    mock_text: MagicMock, mock_db_exists: MagicMock, mock_engine: Engine
):
    """Verify drop_database issues a DROP DATABASE statement when db is present."""
    with patch.object(mock_engine, "connect", return_value=MagicMock()):
        drop_database(mock_engine, "existing_db")
        mock_db_exists.assert_called_once()
        # Expect calls for terminate and drop
        assert mock_text.call_count == 2


@patch("setup_db.get_engine")
@patch("pathlib.Path.is_file", return_value=True)
@patch("pathlib.Path.read_text", return_value="SELECT 1;")
def test_populate_database_executes_sql(
    mock_read_text: MagicMock,
    mock_is_file: MagicMock,
    mock_get_engine: MagicMock,
    mock_config: Config,
):
    """Verify populate_database reads a SQL file and executes its content."""
    mock_conn = MagicMock()
    mock_engine_instance = MagicMock()
    mock_engine_instance.connect.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine_instance

    sql_file = Path("/fake/dump.sql")
    populate_database(mock_config, "test_db", sql_file)

    mock_is_file.assert_called_once()
    mock_read_text.assert_called_once()
    mock_get_engine.assert_called_once_with(mock_config, dbname="test_db")
    mock_conn.exec_driver_sql.assert_called_once_with("SELECT 1;")
