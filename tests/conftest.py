import sys
import os
from pathlib import Path
import inspect

# Get the absolute path to the project root directory
project_root = Path(__file__).parent.parent.absolute()

# Print debugging information about paths
print(f"Project root: {project_root}")
print(f"Current directory: {os.getcwd()}")
print(f"Original sys.path: {sys.path}")

# Add the project root to sys.path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"Added {project_root} to sys.path")

# Verify the app module location
app_path = project_root / 'app'
config_path = project_root / 'app' / 'config.py'
print(f"app directory exists: {app_path.exists()}")
print(f"config.py exists: {config_path.exists()}")

# Show all imported modules
print("\nImported modules before tests:")
for name, module in list(sys.modules.items())[:20]:  # Show just first 20 to avoid clutter
    try:
        file = inspect.getfile(module) if hasattr(module, "__file__") else "built-in"
        print(f"  {name}: {file}")
    except (TypeError, ValueError):
        print(f"  {name}: unknown location")