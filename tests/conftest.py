import sys
import os
from pathlib import Path
import pytest

# Register the asyncio marker
pytest_plugins = ["pytest_asyncio"]

# Get the absolute path to the project root directory
project_root = Path(__file__).parent.parent.absolute()

# Add the project root to sys.path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))