"""Pytest configuration and environment initialization for Knowledge Layer tests."""

from pathlib import Path
import sys

# Ensure package root ('knowledge') and backend root are on sys.path for test discovery and imports
package_root = Path(__file__).resolve().parent.parent
backend_root = package_root.parent

if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
