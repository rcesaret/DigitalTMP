"""Verify that the dynamic import of the 04_run_comparison.py module works."""

import importlib.util
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Dynamically import module from file with importlib (since it starts with a number)
module_path = project_root / "phases" / "01_LegacyDB" / "src" / "04_run_comparison.py"
print(f"Module path: {module_path}")
print(f"Module exists: {module_path.exists()}")

spec = importlib.util.spec_from_file_location("run_comparison", module_path)
run_comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_comparison)

# Check if we can access functions from the module
print("\nAvailable functions in run_comparison module:")
for name in dir(run_comparison):
    if not name.startswith("__") and callable(getattr(run_comparison, name)):
        print(f"- {name}")
