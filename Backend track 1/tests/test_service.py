import os
import sqlite3

import pytest

from app.db import init_db
from app.models import ScanRequest, UploadObject
from app.repository import ScanRepository
from app.service import run_scan


@pytest.fixture
def db_repo():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    repo = ScanRepository(conn)
    yield repo
    conn.close()


def _get_fixture_content(filename: str) -> bytes:
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, "rb") as f:
        return f.read()


def test_run_scan_compliant(db_repo):
    content = _get_fixture_content("compliant.txt")
    req = ScanRequest(
        upload=UploadObject(
            original_filename="compliant.txt",
            content=content,
            content_type="text/plain",
            size_bytes=len(content),
            sha256="fakehash",
            format_hint=None,
        )
    )
    result = run_scan(req, db_repo)
    assert result.status == "completed"
    assert result.summary is not None
    assert result.summary.compliant == 8
    assert result.summary.failing == 0
    assert result.summary.ambiguous == 0
    assert result.summary.compliance_percent == 100.0


def test_run_scan_failing(db_repo):
    content = _get_fixture_content("failing.txt")
    req = ScanRequest(
        upload=UploadObject(
            original_filename="failing.txt",
            content=content,
            content_type="text/plain",
            size_bytes=len(content),
            sha256="fakehash",
            format_hint=None,
        )
    )
    result = run_scan(req, db_repo)
    assert result.status == "completed"
    assert result.summary is not None
    assert result.summary.compliant == 0
    assert result.summary.failing == 8
    assert result.summary.compliance_percent == 0.0


def test_run_scan_ambiguous(db_repo):
    content = _get_fixture_content("ambiguous.txt")
    req = ScanRequest(
        upload=UploadObject(
            original_filename="ambiguous.txt",
            content=content,
            content_type="text/plain",
            size_bytes=len(content),
            sha256="fakehash",
            format_hint=None,
        )
    )
    result = run_scan(req, db_repo)
    assert result.status == "completed"
    assert result.summary is not None
    assert result.summary.ambiguous == 8
    assert result.summary.compliant == 0
    assert result.summary.compliance_percent == 0.0
