"""Pytest configuration and environment initialization for Developer 2 tests."""

from pathlib import Path
import sys

# Ensure package root ('dev 2 part') is on sys.path for test discovery and imports
package_root = Path(__file__).resolve().parent.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))
