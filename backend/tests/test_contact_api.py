"""Tests for the Contact Submissions API (/api/contact)."""

import os
import re
import sqlite3
import tempfile
from typing import Generator
import pytest
from flask.testing import FlaskClient

from app.api import create_app
from app.database.connection import get_connection
from app.database.repositories import ContactSubmissionRepository


@pytest.fixture
def client_and_db() -> Generator[tuple[FlaskClient, str], None, None]:
    """Provide a Flask test client configured with an isolated temporary SQLite database."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = create_app(db_path=temp_db_path, test_config={"TESTING": True})
    with app.test_client() as c:
        yield c, temp_db_path

    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


def test_contact_submission_success(client_and_db):
    """Test successful contact submission returns 201 and valid ticket_id."""
    client, db_path = client_and_db
    payload = {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.corp",
        "subject": "Mission Brief: Core Infrastructure Audit",
        "message": "We need verification of Cisco IOS router configs for upcoming compliance certification.",
    }

    res = client.post("/api/contact", json=payload)
    assert res.status_code == 201

    body = res.get_json()
    assert body["error"] is None
    assert body["data"] is not None
    assert body["data"]["status"] == "received"

    ticket_id = body["data"]["ticket_id"]
    assert ticket_id is not None
    # Ticket ID format: PX-YYYYMMDD-XXXXXX
    assert re.match(r"^PX-\d{8}-[A-F0-9]{6}$", ticket_id)


def test_contact_submission_persists_to_sqlite(client_and_db):
    """Test contact submission is actually persisted into SQLite table."""
    client, db_path = client_and_db
    payload = {
        "name": "Marcus Wright",
        "email": "marcus@resistance.net",
        "subject": "Firewall Rule Audit",
        "message": "Requesting validation of ACL rules and management interface isolation.",
    }

    res = client.post("/api/contact", json=payload)
    assert res.status_code == 201
    ticket_id = res.get_json()["data"]["ticket_id"]

    # Verify directly against database
    conn = get_connection(db_path)
    try:
        repo = ContactSubmissionRepository(conn)
        stored = repo.get_by_ticket_id(ticket_id)
        assert stored is not None
        assert stored["ticket_id"] == ticket_id
        assert stored["name"] == "Marcus Wright"
        assert stored["email"] == "marcus@resistance.net"
        assert stored["subject"] == "Firewall Rule Audit"
        assert "Requesting validation" in stored["message"]
        assert stored["status"] == "received"
        assert stored["created_at"] is not None
    finally:
        conn.close()


def test_contact_submission_missing_fields(client_and_db):
    """Test validation errors for missing or empty required fields."""
    client, _ = client_and_db

    valid_payload = {
        "name": "Kyle Reese",
        "email": "kyle@defense.gov",
        "subject": "Urgent Audit",
        "message": "Verify border gateway protocol security parameters.",
    }

    for required_field in ["name", "email", "subject", "message"]:
        incomplete = dict(valid_payload)
        del incomplete[required_field]
        res = client.post("/api/contact", json=incomplete)
        assert res.status_code == 400
        body = res.get_json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert required_field in body["error"]["message"].lower()

        # Also test with empty string
        empty_val = dict(valid_payload)
        empty_val[required_field] = "   "
        res = client.post("/api/contact", json=empty_val)
        assert res.status_code == 400


def test_contact_submission_invalid_email(client_and_db):
    """Test validation errors for malformed email addresses."""
    client, _ = client_and_db

    invalid_emails = [
        "notanemail",
        "user@",
        "@domain.com",
        "user@domain",
        "user space@domain.com",
    ]

    for bad_email in invalid_emails:
        payload = {
            "name": "John Connor",
            "email": bad_email,
            "subject": "Inquiry",
            "message": "Checking email validator functionality.",
        }
        res = client.post("/api/contact", json=payload)
        assert res.status_code == 400
        body = res.get_json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "email" in body["error"]["message"].lower()


def test_contact_submission_rejects_phone_field(client_and_db):
    """Test that submitting phone fields is explicitly rejected."""
    client, _ = client_and_db

    forbidden_payloads = [
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "subject": "Inquiry",
            "message": "Valid message",
            "phone": "+1 555-0199",
        },
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "subject": "Inquiry",
            "message": "Valid message",
            "phone_number": "+91 9876543210",
        },
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "subject": "Inquiry",
            "message": "Valid message",
            "mobile": "07123456789",
        },
    ]

    for payload in forbidden_payloads:
        res = client.post("/api/contact", json=payload)
        assert res.status_code == 400
        body = res.get_json()
        assert body["error"]["code"] == "DISALLOWED_FIELD"
        assert "phone" in body["error"]["message"].lower()


def test_contact_submission_oversized_inputs(client_and_db):
    """Test that oversized inputs exceeding bounds are rejected."""
    client, _ = client_and_db

    # Oversized name (> 100)
    res = client.post(
        "/api/contact",
        json={
            "name": "A" * 101,
            "email": "valid@example.com",
            "subject": "Valid Subject",
            "message": "Valid Message",
        },
    )
    assert res.status_code == 400
    assert "name" in res.get_json()["error"]["message"].lower()

    # Oversized subject (> 200)
    res = client.post(
        "/api/contact",
        json={
            "name": "Valid Name",
            "email": "valid@example.com",
            "subject": "S" * 201,
            "message": "Valid Message",
        },
    )
    assert res.status_code == 400
    assert "subject" in res.get_json()["error"]["message"].lower()

    # Oversized message (> 5000)
    res = client.post(
        "/api/contact",
        json={
            "name": "Valid Name",
            "email": "valid@example.com",
            "subject": "Valid Subject",
            "message": "M" * 5001,
        },
    )
    assert res.status_code == 400
    assert "message" in res.get_json()["error"]["message"].lower()


def test_contact_submission_no_secret_leakage(client_and_db):
    """Verify that response envelope contains only safe tracking metadata."""
    client, _ = client_and_db
    payload = {
        "name": "Audit Officer",
        "email": "officer@enterprise.corp",
        "subject": "Audit Scope",
        "message": "Confidential internal inquiry regarding edge gateway configurations.",
    }

    res = client.post("/api/contact", json=payload)
    assert res.status_code == 201
    body = res.get_json()

    # Response should have only data with ticket_id and status
    assert set(body.keys()) == {"data", "error", "request_id"}
    assert set(body["data"].keys()) == {"ticket_id", "status"}
    # Verify neither email nor message are reflected in the response
    assert "email" not in body["data"]
    assert "message" not in body["data"]
