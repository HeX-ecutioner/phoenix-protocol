"""Shared pytest configuration and fixtures for backend test suite."""

import pathlib
import sys
import pytest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
SAMPLE_DATA_DIR = BACKEND_DIR / "sample_data"

# Ensure backend root is on sys.path when pytest is run from any working directory
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def get_fixture_path(relative_path: str) -> pathlib.Path:
    """Resolve a relative fixture path to an absolute path under backend/sample_data/."""
    p = pathlib.Path(relative_path)
    if p.parts and p.parts[0] == "sample_data":
        p = pathlib.Path(*p.parts[1:])
    return SAMPLE_DATA_DIR / p


@pytest.fixture
def sample_data_dir() -> pathlib.Path:
    """Provide the absolute path to backend/sample_data/."""
    return SAMPLE_DATA_DIR
