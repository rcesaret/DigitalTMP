# tests/p1_w2/test_generate_erds.py

import configparser
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Mock the problematic sqlalchemy_schemadisplay module before importing the script
mock_schemadisplay = MagicMock()
mock_schemadisplay.create_schema_graph = MagicMock()
sys.modules["sqlalchemy_schemadisplay"] = mock_schemadisplay

# Dynamically load the orchestrator script
script_path = (
    Path(__file__).parent.parent.parent
    / "phases"
    / "01_LegacyDB"
    / "src"
    / "03_generate_erds.py"
)
spec = importlib.util.spec_from_file_location("generate_erds_orchestrator", script_path)
orchestrator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator)


@pytest.fixture
def mock_config():
    """Fixture for a comprehensive mocked configuration parser."""
    config = configparser.ConfigParser()
    config["postgresql"] = {
        "user": "test_user",
        "password": "test_password",  # pragma: allowlist-secret
        "host": "localhost",
        "port": "5432",
    }
    config["databases"] = {
        "legacy_dbs": "tmp_df8,tmp_df9,tmp_df10,tmp_rean_df2",
        "benchmark_dbs": ("tmp_benchmark_wide_numeric,tmp_benchmark_wide_text_nulls"),
    }
    config["paths"] = {"erd_outputs": "test_erds"}
    # Note: subsystem_tables removed as script uses hardcoded constants
    return config


@pytest.fixture
def mock_args(tmp_path):
    """Fixture for mocked command-line arguments."""
    args = MagicMock()
    args.config = str(tmp_path / "config.ini")
    return args


@pytest.fixture
def mock_metadata():
    """Fixture for mocked SQLAlchemy metadata with realistic structure."""
    metadata = MagicMock()

    # Mock tables for different database types
    def create_mock_tables(db_name):
        if db_name == "tmp_df9":
            # Complex normalized structure with many tables matching
            # TMP_DF9_SUBSYSTEMS
            table_names = [
                "tmp_df9.location",
                "tmp_df9.description",
                "tmp_df9.archInterp",
                "tmp_df9.cerVessel",
                "tmp_df9.cerPhTot",
                "tmp_df9.cerNonVessel",
                "tmp_df9.lithicFlaked",
                "tmp_df9.lithicGround",
                "tmp_df9.lithicDeb",
                "tmp_df9.admin",
                "tmp_df9.condition",
                "tmp_df9.figurine",
                "tmp_df9.plasterFloor",
                "tmp_df9.archaeology",
                "tmp_df9.artifactOther",
                "tmp_df9.architecture",
                "tmp_df9.complexData",
                "tmp_df9.complexMacroData",
            ]
        elif "benchmark" in db_name:
            # Simple denormalized structure
            table_names = ["public.wide_format_data"]
        else:
            # Other legacy databases
            table_names = [f"{db_name.lower()}.table1", f"{db_name.lower()}.table2"]

        # Create mock table objects
        mock_tables = {}
        for table_name in table_names:
            mock_table = MagicMock()
            mock_table.name = table_name.split(".")[-1]
            mock_table.schema = table_name.split(".")[0]
            mock_tables[table_name] = mock_table

        return mock_tables

    metadata.tables = MagicMock()
    metadata._current_db = None

    def mock_keys():
        if metadata._current_db:
            tables = create_mock_tables(metadata._current_db)
            return list(tables.keys())
        return []

    def mock_items():
        if metadata._current_db:
            tables = create_mock_tables(metadata._current_db)
            return list(tables.items())
        return []

    metadata.tables.keys = mock_keys
    metadata.tables.items = mock_items

    return metadata


def test_when_valid_config_then_generates_all_erds_successfully(
    mock_config, mock_args, mock_metadata, monkeypatch
):
    """Test the complete ERD generation flow with all expected outputs."""
    # --- Setup Mocks ---
    mock_engine = MagicMock()
    mock_graph = Mock()
    mock_graph.write_svg.return_value = None
    mock_graph.set_graph_defaults.return_value = None
    mock_graph.set_node_defaults.return_value = None
    mock_graph.set_edge_defaults.return_value = None

    create_schema_graph_calls = []

    def mock_create_schema_graph(*args, **kwargs):
        """Track calls to create_schema_graph and return mock graph."""
        create_schema_graph_calls.append((args, kwargs))
        assert args[0] == mock_engine, "create_schema_graph not called with engine"
        return mock_graph

    # Setup temporary config file
    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        mock_config.write(f)

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", lambda *args, **kwargs: mock_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(orchestrator, "create_schema_graph", mock_create_schema_graph)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    # Mock metadata reflection to set current database context
    original_reflect = mock_metadata.reflect

    def mock_reflect(*args, **kwargs):
        # Extract database name from engine URL for context
        schema = kwargs.get("schema", "public")
        if schema != "public":
            mock_metadata._current_db = schema
        else:
            # Default for public schema
            mock_metadata._current_db = "tmp_benchmark_wide_numeric"
        return original_reflect(*args, **kwargs)

    mock_metadata.reflect = mock_reflect

    # --- Execute ---
    orchestrator.main()

    # --- Assertions ---
    # Total ERDs = 6 full ERDs + 3 focused ERDs = 9
    total_expected_erds = 9
    assert len(create_schema_graph_calls) == total_expected_erds, (
        f"Expected {total_expected_erds} ERDs to be generated, "
        f"got {len(create_schema_graph_calls)}"
    )
    assert (
        mock_graph.write_svg.call_count == total_expected_erds
    ), f"Expected {total_expected_erds} SVG files to be written"

    # Verify new styling API is used
    assert mock_graph.set_graph_defaults.call_count == total_expected_erds
    assert mock_graph.set_node_defaults.call_count == total_expected_erds
    assert mock_graph.set_edge_defaults.call_count == total_expected_erds


def test_when_tmp_df9_has_subsystems_then_generates_focused_erds(
    mock_config, mock_args, mock_metadata, monkeypatch
):
    """Test that focused ERDs are generated for tmp_df9 subsystems."""
    # --- Setup ---
    mock_engine = MagicMock()
    mock_graph = Mock()

    create_schema_graph_calls = []

    def mock_create_schema_graph(*args, **kwargs):
        create_schema_graph_calls.append((args, kwargs))
        return mock_graph

    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        mock_config.write(f)

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", lambda *args, **kwargs: mock_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(orchestrator, "create_schema_graph", mock_create_schema_graph)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    # Set up metadata to return tmp_df9 context
    mock_metadata._current_db = "tmp_df9"

    # --- Execute ---
    orchestrator.main()

    # --- Find tmp_df9 specific calls ---
    tmp_df9_calls = []
    for _, kwargs in create_schema_graph_calls:
        # Check if this is a call made during tmp_df9 processing
        # We can identify this by checking the tables parameter
        if "tables" in kwargs:
            tmp_df9_calls.append((_, kwargs))

    # --- Assertions ---
    # Should have 3 focused ERDs for tmp_df9 subsystems
    focused_erd_calls = [
        call for call in tmp_df9_calls if call[1].get("tables") is not None
    ]
    assert (
        len(focused_erd_calls) == 3
    ), f"Expected 3 focused ERDs for tmp_df9, got {len(focused_erd_calls)}"

    # Verify each focused ERD has a restricted table list
    for _, kwargs in focused_erd_calls:
        tables_to_include = kwargs.get("tables")
        assert tables_to_include is not None, "Focused ERD should have tables parameter"
        assert len(tables_to_include) > 0, "Focused ERD should include some tables"


def test_when_schema_names_are_determined_then_uses_correct_naming_convention(
    mock_config, mock_args, mock_metadata, monkeypatch
):
    """Test that schema names are correctly determined for different database types."""
    # --- Setup ---
    mock_engine = MagicMock()
    mock_graph = Mock()

    reflect_calls = []

    def mock_reflect(*args, **kwargs):
        reflect_calls.append(kwargs)
        return None

    mock_metadata.reflect = mock_reflect

    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        mock_config.write(f)

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", lambda *args, **kwargs: mock_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(
        orchestrator, "create_schema_graph", lambda *args, **kwargs: mock_graph
    )
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    # --- Execute ---
    orchestrator.main()

    # --- Assertions ---
    # Extract schema names from reflect calls
    schemas_used = [call.get("schema") for call in reflect_calls if "schema" in call]

    # Legacy databases should use lowercase schema names
    expected_legacy_schemas = ["tmp_df8", "tmp_df9", "tmp_df10", "tmp_rean_df2"]
    # Benchmark databases should use 'public' schema
    expected_benchmark_schemas = ["public", "public"]  # Two benchmark DBs

    expected_all_schemas = expected_legacy_schemas + expected_benchmark_schemas

    # Sort both lists for comparison
    assert sorted(schemas_used) == sorted(expected_all_schemas), (
        f"Schema names don't match. Expected: {sorted(expected_all_schemas)}, "
        f"Got: {sorted(schemas_used)}"
    )


def test_when_no_subsystem_tables_configured_then_only_generates_full_erds(
    mock_args, mock_metadata, monkeypatch
):
    """Test that without matching tables, only full ERDs are generated."""
    # --- Setup config without subsystem_tables ---
    config = configparser.ConfigParser()
    config["postgresql"] = {
        "user": "test_user",
        "password": "test_password",  # pragma: allowlist-secret
        "host": "localhost",
        "port": "5432",
    }
    config["databases"] = {
        "legacy_dbs": "tmp_df9",  # Just one DB to simplify
        "benchmark_dbs": "",
    }
    config["paths"] = {"erd_outputs": "test_erds"}

    mock_engine = MagicMock()
    mock_graph = Mock()

    create_schema_graph_calls = []

    def mock_create_schema_graph(*args, **kwargs):
        create_schema_graph_calls.append((args, kwargs))
        return mock_graph

    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        config.write(f)

    # Mock the metadata to return empty tables for tmp_df9 to prevent subsystem
    # ERD generation
    mock_metadata.tables = MagicMock()
    mock_metadata.tables.keys.return_value = []
    mock_metadata.tables.items.return_value = []

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", lambda *args, **kwargs: mock_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(orchestrator, "create_schema_graph", mock_create_schema_graph)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    mock_metadata._current_db = "tmp_df9"

    # --- Execute ---
    orchestrator.main()

    # --- Assertions ---
    # Should have 1 ERD (the full one for tmp_df9)
    # Note: The script has hardcoded TMP_DF9_SUBSYSTEMS but since we mock empty
    # tables, the subsystem ERDs will be skipped due to no matching tables
    assert len(create_schema_graph_calls) == 1, (
        f"Expected 1 ERD without subsystem tables, "
        f"got {len(create_schema_graph_calls)}"
    )

    # The single call should be for a full ERD (no tables restriction)
    _, kwargs = create_schema_graph_calls[0]
    assert (
        kwargs.get("tables") is None
    ), "Without matching tables, should only generate full ERD"


@pytest.mark.parametrize(
    "db_name,expected_schema",
    [
        ("tmp_df8", "tmp_df8"),
        ("tmp_df9", "tmp_df9"),
        ("tmp_df10", "tmp_df10"),
        ("tmp_rean_df2", "tmp_rean_df2"),
        ("tmp_benchmark_wide_numeric", "public"),
        ("tmp_benchmark_wide_text_nulls", "public"),
    ],
)
def test_when_determining_schema_for_db_then_returns_correct_schema(
    db_name, expected_schema
):
    """Test schema name determination logic for different database types."""
    legacy_dbs = ["tmp_df8", "tmp_df9", "tmp_df10", "tmp_rean_df2"]

    # Test the get_schema_for_db function directly
    actual_schema = orchestrator.get_schema_for_db(db_name, legacy_dbs)

    assert actual_schema == expected_schema, (
        f"For database '{db_name}', expected schema '{expected_schema}', "
        f"got '{actual_schema}'"
    )


def test_when_database_connection_fails_then_continues_with_other_databases(
    mock_config, mock_args, mock_metadata, monkeypatch
):
    """Test error handling when database connection fails."""
    # --- Setup with one failing database ---
    mock_engine_success = MagicMock()
    mock_graph = Mock()

    call_count = 0

    def mock_get_sqlalchemy_engine(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:  # Second database fails
            return None  # get_sqlalchemy_engine returns None on failure
        return mock_engine_success

    create_schema_graph_calls = []

    def mock_create_schema_graph(*args, **kwargs):
        create_schema_graph_calls.append((args, kwargs))
        return mock_graph

    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        mock_config.write(f)

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", mock_get_sqlalchemy_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(orchestrator, "create_schema_graph", mock_create_schema_graph)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    mock_metadata._current_db = "tmp_df8"

    # --- Execute ---
    # Should not raise exception despite one database failing
    orchestrator.main()

    # --- Assertions ---
    # Should have processed fewer databases due to the failure
    # But should have continued processing other databases
    assert (
        len(create_schema_graph_calls) < 9
    ), "Should have fewer ERDs due to database failure"
    assert (
        len(create_schema_graph_calls) > 0
    ), "Should still process some databases despite failure"


def test_when_graph_generation_fails_then_logs_error_and_continues(
    mock_config, mock_args, mock_metadata, monkeypatch
):
    """Test error handling when ERD generation fails for one database."""
    # --- Setup ---
    mock_engine = MagicMock()
    mock_graph = Mock()

    call_count = 0

    def mock_create_schema_graph(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # First ERD generation fails
            raise Exception("ERD generation failed")
        return mock_graph

    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        mock_config.write(f)

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", lambda *args, **kwargs: mock_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(orchestrator, "create_schema_graph", mock_create_schema_graph)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    mock_metadata._current_db = "tmp_df8"

    # --- Execute ---
    # Should not raise exception despite ERD generation failure
    # because generate_and_save_erd catches exceptions internally
    orchestrator.main()

    # --- Assertions ---
    # Should have attempted multiple ERDs despite one failure
    assert call_count > 1, "Should continue processing after ERD generation failure"


def test_when_valid_config_then_script_executes_successfully(
    mock_config, mock_args, mock_metadata, monkeypatch
):
    """Test that the script executes successfully with valid configuration."""
    # --- Setup ---
    mock_engine = MagicMock()
    mock_graph = Mock()

    config_file_path = Path(mock_args.config)
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file_path, "w") as f:
        mock_config.write(f)

    # --- Apply Patches ---
    monkeypatch.setattr(
        orchestrator, "get_sqlalchemy_engine", lambda *args, **kwargs: mock_engine
    )
    monkeypatch.setattr(orchestrator, "MetaData", lambda: mock_metadata)
    monkeypatch.setattr(
        orchestrator, "create_schema_graph", lambda *args, **kwargs: mock_graph
    )
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "parse_arguments", lambda: mock_args)
    monkeypatch.setattr(orchestrator, "setup_logging", lambda *args, **kwargs: None)

    mock_metadata._current_db = "tmp_df8"

    # --- Execute ---
    # The main assertion is that this doesn't raise an exception
    try:
        orchestrator.main()
        execution_successful = True
    except Exception as e:
        execution_successful = False
        pytest.fail(f"Script execution failed with error: {e}")

    # --- Assertions ---
    assert (
        execution_successful
    ), "Script should execute successfully with valid configuration"

    # Verify create_schema_graph was called (indicating ERD generation attempted)
    assert mock_graph.write_svg.called, "Should have attempted to write SVG files"
    assert mock_graph.set_graph_defaults.called, "Should have applied graph styling"
