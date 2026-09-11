"""Test suite for the Teach-the-Auditor and Knowledge Base REST API endpoints.

Verifies:
1. Command interpretation proposal (POST /api/knowledge/propose)
2. Human-in-the-loop approval (POST /api/knowledge/approve)
3. Rejection lifecycle (POST /api/knowledge/reject)
4. Knowledge lookup before and after approval (GET /api/knowledge/lookup)
5. Mappings catalog retrieval and status filtering (GET /api/knowledge/mappings)
6. Zero AI retraining: learned commands hit knowledge base directly on subsequent audits
"""

import tempfile
import pytest

from app.api import create_app


@pytest.fixture
def client():
    """Create test client with isolated SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tf:
        db_path = tf.name

    app = create_app(
        db_path=db_path,
        test_config={
            "TESTING": True,
            "KNOWLEDGE_DB_PATH": ":memory:",
        },
    )
    with app.test_client() as test_client:
        yield test_client


def test_knowledge_propose_validation(client):
    """Propose requires a valid, non-empty command."""
    res = client.post("/api/knowledge/propose", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"]["code"] == "INVALID_PAYLOAD"

    res2 = client.post("/api/knowledge/propose", json={"command": "   "})
    assert res2.status_code == 400


def test_knowledge_propose_unknown_command(client):
    """Proposing an unknown command yields an AI proposal requiring human approval."""
    res = client.post(
        "/api/knowledge/propose",
        json={
            "command": "ip ssh time-out 60",
            "vendor": "Cisco",
            "platform": "IOS",
        },
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["error"] is None
    payload = body["data"]

    assert payload["command"] == "ip ssh time-out 60"
    assert payload["requires_human_approval"] is True
    assert payload["source"] == "ai_agent"
    assert payload["status"] == "proposed"
    assert payload["mapping_id"] is not None
    assert payload["security_control"] == "transport_security"
    assert payload["mapped_rule_id"] == "NET-002"
    assert payload["confidence"] >= 0.8


def test_knowledge_lookup_unapproved_command(client):
    """Commands not yet approved do not return as trusted knowledge."""
    # First propose
    res = client.post(
        "/api/knowledge/propose",
        json={"command": "access-class ADMIN_ACL in", "vendor": "Cisco", "platform": "IOS"},
    )
    assert res.status_code == 200

    # Lookup should still return found=False because it hasn't been approved by a human
    lookup_res = client.get(
        "/api/knowledge/lookup?command=access-class ADMIN_ACL in&vendor=Cisco&platform=IOS"
    )
    assert lookup_res.status_code == 200
    lookup_body = lookup_res.get_json()["data"]
    assert lookup_body["found"] is False
    assert lookup_body["requires_human_approval"] is True
    assert lookup_body["interpretation"] is None


def test_knowledge_approval_and_persistence_loop(client):
    """Full Teach-the-Auditor loop:
    1. Encounter unknown command -> Propose mapping (AI agent)
    2. Human approves proposal
    3. Subsequent lookup finds it directly from knowledge base (source=knowledge_base)
    4. Subsequent propose recognizes it directly without AI re-interpretation!
    """
    cmd = "login block-for 300 attempts 3 within 60"

    # Step 1: Propose
    p_res = client.post(
        "/api/knowledge/propose",
        json={"command": cmd, "vendor": "Cisco", "platform": "IOS"},
    )
    assert p_res.status_code == 200
    proposal = p_res.get_json()["data"]
    mapping_id = proposal["mapping_id"]
    assert proposal["requires_human_approval"] is True
    assert proposal["source"] == "ai_agent"

    # Step 2: Approve
    appr_res = client.post(
        "/api/knowledge/approve",
        json={"mapping_id": mapping_id},
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.get_json()["data"]
    assert appr_data["status"] == "approved"
    assert appr_data["mapping"]["approval_status"] == "approved"

    # Step 3: Lookup - now found in knowledge base!
    lookup_res = client.get(
        f"/api/knowledge/lookup?command={cmd}&vendor=Cisco&platform=IOS"
    )
    assert lookup_res.status_code == 200
    lookup_data = lookup_res.get_json()["data"]
    assert lookup_data["found"] is True
    assert lookup_data["source"] == "knowledge_base"
    assert lookup_data["requires_human_approval"] is False
    assert lookup_data["interpretation"]["security_control"] == "brute_force_protection"

    # Step 4: Propose again for identical command - hits knowledge base directly!
    p2_res = client.post(
        "/api/knowledge/propose",
        json={"command": cmd, "vendor": "Cisco", "platform": "IOS"},
    )
    assert p2_res.status_code == 200
    p2_data = p2_res.get_json()["data"]
    assert p2_data["source"] == "knowledge_base"
    assert p2_data["requires_human_approval"] is False
    assert p2_data["status"] == "approved"


def test_knowledge_rejection(client):
    """Rejecting a proposal excludes it from lookup and sets status='rejected'."""
    cmd = "logging host 10.10.10.50"
    p_res = client.post(
        "/api/knowledge/propose",
        json={"command": cmd, "vendor": "Cisco", "platform": "IOS"},
    )
    mapping_id = p_res.get_json()["data"]["mapping_id"]

    rej_res = client.post(
        "/api/knowledge/reject",
        json={"mapping_id": mapping_id, "reason": "Incorrect logging destination test"},
    )
    assert rej_res.status_code == 200
    rej_data = rej_res.get_json()["data"]
    assert rej_data["status"] == "rejected"

    # Lookup should still return found=False
    lookup_res = client.get(
        f"/api/knowledge/lookup?command={cmd}&vendor=Cisco&platform=IOS"
    )
    assert lookup_res.status_code == 200
    assert lookup_res.get_json()["data"]["found"] is False


def test_knowledge_mappings_list(client):
    """Retrieve list of mappings and filter by status."""
    res = client.get("/api/knowledge/mappings")
    assert res.status_code == 200
    body = res.get_json()["data"]
    assert "mappings" in body
    assert isinstance(body["mappings"], list)
