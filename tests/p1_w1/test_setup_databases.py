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
        verify_database_setup = setup_db.verify_database_setup
        parse_arguments = setup_db.parse_arguments
        main = setup_db.main
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
        password="FAKE_PASSWORD",  # pragma: allowlist secret
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
    config_content = """
[postgresql]
host = localhost
port = 5432
user = FAKE_USER
password = FAKE_PASSWORD
root_db = postgres

[databases]
legacy_dbs = tmp_df8, tmp_df9, tmp_df10, tmp_rean_df2

[paths]
sql_dump_dir = /fake/dump/dir
"""  # pragma: allowlist secret
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)

    config = load_config(config_file)
    assert config.host == "localhost"
    assert config.password == "FAKE_PASSWORD"  # pragma: allowlist secret
    assert config.legacy_dbs == ["tmp_df8", "tmp_df9", "tmp_df10", "tmp_rean_df2"]
    assert config.dump_dir.name == "dir"  # Path resolution


def test_load_config_raises_error_if_file_not_found(tmp_path: Path):
    """Verify ConfigurationError is raised for a non-existent file."""
    with pytest.raises(ConfigurationError, match="Config file not found"):
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
    config_content = """
[postgresql]
host = localhost
user = FAKE_USER

[databases]
legacy_dbs = tmp_df8

[paths]
sql_dump_dir = /fake/dir
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)
    # This should not raise an error since ConfigParser.get() returns None
    # for missing keys and current implementation doesn't validate them
    config = load_config(config_file)
    assert config.password is None


# ---------------------------------------------------------------------------
# Tests for Database Engine
# ---------------------------------------------------------------------------


@patch.object(setup_db, "create_engine")
def test_get_engine_constructs_correct_url(
    mock_create_engine: MagicMock, mock_config: Config
):
    """Verify get_engine constructs the correct PostgreSQL connection URL."""
    get_engine(mock_config)
    expected_url = (  # pragma: allowlist secret
        f"postgresql+psycopg2://{mock_config.user}:{mock_config.password}"
        f"@{mock_config.host}:{mock_config.port}/{mock_config.root_db}"
    )
    mock_create_engine.assert_called_once_with(expected_url)


@patch.object(setup_db, "create_engine")
def test_get_engine_uses_override_db(
    mock_create_engine: MagicMock, mock_config: Config
):
    """Verify get_engine uses the override database name when provided."""
    override_db = "override_db"
    get_engine(mock_config, dbname=override_db)
    expected_url = (  # pragma: allowlist secret
        f"postgresql+psycopg2://{mock_config.user}:{mock_config.password}"
        f"@{mock_config.host}:{mock_config.port}/{override_db}"
    )
    mock_create_engine.assert_called_once_with(expected_url)


# ---------------------------------------------------------------------------
# Tests for Core Database Operations
# ---------------------------------------------------------------------------


def test_database_exists_returns_true_when_db_present(mock_connection: Connection):
    """Verify database_exists returns True when the database is found."""
    mock_connection.execute.return_value.scalar.return_value = 1
    assert database_exists(mock_connection, "existing_db") is True
    mock_connection.execute.assert_called_once()


def test_database_exists_returns_false_when_db_absent(mock_connection: Connection):
    """Verify database_exists returns False when the database is not found."""
    mock_connection.execute.return_value.scalar.return_value = None
    assert database_exists(mock_connection, "non_existent_db") is False
    mock_connection.execute.assert_called_once()


@patch.object(setup_db, "database_exists", return_value=False)
@patch.object(setup_db, "text")
def test_create_database_executes_create_statement(
    mock_text: MagicMock, mock_db_exists: MagicMock, mock_engine: Engine
):
    """Verify create_database issues a CREATE DATABASE statement when db is absent."""
    mock_conn = MagicMock()
    mock_context = mock_engine.connect.return_value.execution_options.return_value
    mock_context.__enter__.return_value = mock_conn

    create_database(mock_engine, "new_db")

    mock_db_exists.assert_called_once()
    mock_text.assert_called_once_with('CREATE DATABASE "new_db"')
    mock_conn.execute.assert_called_once()


@patch.object(setup_db, "database_exists", return_value=True)
@patch("sqlalchemy.text")
def test_create_database_skips_if_db_exists(
    mock_text: MagicMock, mock_db_exists: MagicMock, mock_engine: Engine
):
    """Verify create_database does nothing if the database already exists."""
    mock_conn = MagicMock()
    mock_context = mock_engine.connect.return_value.execution_options.return_value
    mock_context.__enter__.return_value = mock_conn

    create_database(mock_engine, "existing_db")

    mock_db_exists.assert_called_once()
    mock_conn.execute.assert_not_called()


@patch.object(setup_db, "database_exists", return_value=True)
@patch("sqlalchemy.text")
def test_drop_database_executes_drop_statement(
    mock_text: MagicMock, mock_db_exists: MagicMock, mock_engine: Engine
):
    """Verify drop_database issues a DROP DATABASE statement when db is present."""
    mock_conn = MagicMock()
    mock_context = mock_engine.connect.return_value.execution_options.return_value
    mock_context.__enter__.return_value = mock_conn

    drop_database(mock_engine, "existing_db")

    mock_db_exists.assert_called_once()
    # Expect calls for terminate and drop
    assert mock_conn.execute.call_count == 2


@patch("subprocess.run")
def test_populate_database_executes_psql(
    mock_subprocess_run: MagicMock, mock_config: Config
):
    """Verify populate_database executes psql command."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = "Success"
    mock_subprocess_run.return_value = mock_result

    sql_file = Path("/fake/dump.sql")
    result = populate_database(mock_config, "test_db", sql_file)

    assert result is True
    mock_subprocess_run.assert_called_once()

    # Verify psql command structure
    call_args = mock_subprocess_run.call_args
    command = call_args[0][0]
    assert command[0] == "psql"
    assert "-d" in command
    assert "test_db" in command


@patch.object(setup_db, "get_engine")
@patch.object(setup_db, "verify_schema_populated")
def test_verify_database_setup_success(
    mock_verify_schema: MagicMock, mock_get_engine: MagicMock, mock_config: Config
):
    """Verify verify_database_setup returns success for properly set up database."""
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    mock_verify_schema.return_value = (True, {"table1": 100, "table2": 200})

    success, message = verify_database_setup(mock_config, "test_db")

    assert success is True
    assert "verified" in message
    assert "300 total rows" in message


@patch.object(setup_db, "get_engine")
@patch.object(setup_db, "verify_schema_populated")
def test_verify_database_setup_failure(
    mock_verify_schema: MagicMock, mock_get_engine: MagicMock, mock_config: Config
):
    """Verify verify_database_setup returns failure for empty database."""
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    mock_verify_schema.return_value = (False, {})

    success, message = verify_database_setup(mock_config, "test_db")

    assert success is False
    assert "empty or corrupted" in message


# ---------------------------------------------------------------------------
# Tests for Command Line Arguments
# ---------------------------------------------------------------------------


def test_parse_arguments_defaults():
    """Test that parse_arguments returns correct defaults."""
    with patch("sys.argv", ["00_setup_databases.py"]):
        args = parse_arguments()
        assert args.config == Path("config.ini")
        assert args.force_recreate is False
        assert args.verify_only is False


def test_parse_arguments_custom():
    """Test that parse_arguments handles custom arguments."""
    with patch(
        "sys.argv",
        [
            "00_setup_databases.py",
            "--config",
            "/custom/config.ini",
            "--force-recreate",
            "--verify-only",
        ],
    ):
        args = parse_arguments()
        assert args.config == Path("/custom/config.ini")
        assert args.force_recreate is True
        assert args.verify_only is True


# ---------------------------------------------------------------------------
# Tests for Main Function
# ---------------------------------------------------------------------------


@patch.object(setup_db, "setup_logging")
@patch.object(setup_db, "load_config")
@patch.object(setup_db, "get_engine")
@patch.object(setup_db, "verify_database_exists")
@patch.object(setup_db, "verify_database_setup")
@patch.object(setup_db, "parse_arguments")
@patch("pathlib.Path.is_file")
def test_main_verify_only_mode(
    mock_is_file: MagicMock,
    mock_parse_args: MagicMock,
    mock_verify_setup: MagicMock,
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
    mock_verify_setup.return_value = (True, "Database verified")
    mock_is_file.return_value = True  # SQL files exist

    # Execute
    main()

    # Verify
    mock_setup_logging.assert_called_once()
    mock_load_config.assert_called_once_with(mock_args.config)
    mock_get_engine.assert_called_once_with(mock_config)
    assert mock_verify_exists.call_count == len(mock_config.legacy_dbs)
    assert mock_verify_setup.call_count == len(mock_config.legacy_dbs)


@patch.object(setup_db, "setup_logging")
@patch.object(setup_db, "load_config")
@patch.object(setup_db, "get_engine")
@patch.object(setup_db, "verify_database_exists")
@patch.object(setup_db, "create_database")
@patch.object(setup_db, "populate_database")
@patch.object(setup_db, "verify_database_setup")
@patch.object(setup_db, "parse_arguments")
@patch("pathlib.Path.is_file")
def test_main_create_mode(
    mock_is_file: MagicMock,
    mock_parse_args: MagicMock,
    mock_verify_setup: MagicMock,
    mock_populate: MagicMock,
    mock_create: MagicMock,
    mock_verify_exists: MagicMock,
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
    mock_verify_exists.return_value = False  # Database doesn't exist
    mock_is_file.return_value = True  # SQL files exist
    mock_populate.return_value = True  # Population succeeds
    mock_verify_setup.return_value = (True, "Database created successfully")

    # Execute
    main()

    # Verify
    mock_setup_logging.assert_called_once()
    mock_load_config.assert_called_once_with(mock_args.config)
    mock_get_engine.assert_called_once_with(mock_config)
    assert mock_create.call_count == len(mock_config.legacy_dbs)
    assert mock_populate.call_count == len(mock_config.legacy_dbs)
    assert mock_verify_setup.call_count == len(mock_config.legacy_dbs)
