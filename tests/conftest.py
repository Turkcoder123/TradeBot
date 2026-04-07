"""conftest.py - add the repository root to sys.path so tests can import fetch_prices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
