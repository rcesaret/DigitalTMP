import importlib.util
import sys
import types
from pathlib import Path


def load_metrics_performance():
    """Load metrics_performance module with a stubbed sqlalchemy."""
    sqlalchemy = types.ModuleType("sqlalchemy")
    engine = types.ModuleType("engine")

    class Engine:  # pragma: no cover - simple placeholder
        pass

    engine.Engine = Engine
    sqlalchemy.text = lambda x: x
    sqlalchemy.engine = engine
    sys.modules.setdefault("sqlalchemy", sqlalchemy)
    sys.modules.setdefault("sqlalchemy.engine", engine)

    module_path = Path(
        "phases/01_LegacyDB/src/profiling_modules/metrics_performance.py"
    )
    spec = importlib.util.spec_from_file_location("metrics_performance", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_parse_categorized_queries_reads_categories_correctly():
    mp = load_metrics_performance()
    sql_file = Path(
        "phases/01_LegacyDB/sql/canonical_queries/canonical_queries_benchmark.sql"
    )
    sql_content = sql_file.read_text()
    result = mp.parse_categorized_queries(sql_content)

    categories = [r[0] for r in result]
    query_ids = [r[1] for r in result]
    assert categories == ["baseline", "join_performance", "complex_filtering"]
    assert query_ids == ["1.1", "2.1", "3.1"]
