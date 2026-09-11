"""Tests verifying synthetic fixtures integrity and loading."""

import json
from pathlib import Path
import pytest
from services.knowledge_service import KnowledgeService
from storage.repository import DuplicateMappingError
from validation.mapping_validator import (
    ValidationError,
    validate_mapping_payload,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_sample_mappings_fixture():
    """Verify sample_mappings.json contains valid mappings for Cisco, Juniper, Fortinet, Palo Alto."""
    fixture_path = FIXTURES_DIR / "sample_mappings.json"
    assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    vendors = {item["vendor"] for item in data}
    expected_vendors = {"Cisco", "Juniper", "Fortinet", "Palo Alto"}
    assert expected_vendors.issubset(
        vendors
    ), f"Missing expected vendors in sample: {expected_vendors - vendors}"

    svc = KnowledgeService(db_path=":memory:")
    for item in data:
        # Validate structure
        validate_mapping_payload(item)
        mapping = svc.propose_mapping(
            vendor=item["vendor"],
            platform=item["platform"],
            command_pattern=item["command_pattern"],
            meaning=item["meaning"],
            security_control=item["security_control"],
            mapped_rule_id=item.get("mapped_rule_id"),
            explanation=item.get("explanation", ""),
            confidence=item.get("confidence", 1.0),
        )
        assert mapping.id is not None
        if item.get("approval_status") == "approved":
            approved = svc.approve_mapping(mapping.id)
            assert approved.approval_status == "approved"
    svc.close()


def test_duplicate_mappings_fixture():
    """Verify duplicate_mappings.json contains duplicate test cases."""
    fixture_path = FIXTURES_DIR / "duplicate_mappings.json"
    assert fixture_path.exists()

    with open(fixture_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    svc = KnowledgeService(db_path=":memory:")

    # Base mapping
    base_item = cases[0]["mapping"]
    base_mapping = svc.propose_mapping(
        vendor=base_item["vendor"],
        platform=base_item["platform"],
        command_pattern=base_item["command_pattern"],
        meaning=base_item["meaning"],
        security_control=base_item["security_control"],
    )
    svc.approve_mapping(base_mapping.id)

    # Exact duplicate
    dup_item = cases[1]["mapping"]
    dup_mapping = svc.propose_mapping(
        vendor=dup_item["vendor"],
        platform=dup_item["platform"],
        command_pattern=dup_item["command_pattern"],
        meaning=dup_item["meaning"],
        security_control=dup_item["security_control"],
    )
    with pytest.raises(DuplicateMappingError):
        svc.approve_mapping(dup_mapping.id)

    # Whitespace-varying duplicate
    ws_item = cases[2]["mapping"]
    ws_mapping = svc.propose_mapping(
        vendor=ws_item["vendor"],
        platform=ws_item["platform"],
        command_pattern=ws_item["command_pattern"],
        meaning=ws_item["meaning"],
        security_control=ws_item["security_control"],
    )
    with pytest.raises(DuplicateMappingError):
        svc.approve_mapping(ws_mapping.id)

    # Different platform should succeed
    diff_platform = cases[3]["mapping"]
    p_mapping = svc.propose_mapping(
        vendor=diff_platform["vendor"],
        platform=diff_platform["platform"],
        command_pattern=diff_platform["command_pattern"],
        meaning=diff_platform["meaning"],
        security_control=diff_platform["security_control"],
    )
    approved_diff = svc.approve_mapping(p_mapping.id)
    assert approved_diff.approval_status == "approved"

    svc.close()


def test_invalid_mappings_fixture():
    """Verify invalid_mappings.json entries all fail validation with expected errors."""
    fixture_path = FIXTURES_DIR / "invalid_mappings.json"
    assert fixture_path.exists()

    with open(fixture_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    for case in cases:
        payload = case["payload"]
        expected_substr = case["expected_error"]

        with pytest.raises(ValidationError) as exc_info:
            validate_mapping_payload(payload)

        assert expected_substr.lower() in str(exc_info.value).lower(), (
            f"Case '{case['description']}' failed to produce expected error '{expected_substr}'. "
            f"Actual error: {exc_info.value}"
        )


def test_vendor_mappings_fixture():
    """Verify vendor_mappings.json represents shared controls across distinct vendors."""
    fixture_path = FIXTURES_DIR / "vendor_mappings.json"
    assert fixture_path.exists()

    with open(fixture_path, "r", encoding="utf-8") as f:
        concepts = json.load(f)

    svc = KnowledgeService(db_path=":memory:")

    for concept in concepts:
        mappings = concept["mappings"]
        for m in mappings:
            prop = svc.propose_mapping(
                vendor=m["vendor"],
                platform=m["platform"],
                command_pattern=m["command_pattern"],
                meaning=m["meaning"],
                security_control=m["security_control"],
                mapped_rule_id=m.get("mapped_rule_id"),
                confidence=m.get("confidence", 1.0),
            )
            svc.approve_mapping(prop.id)

            # Check exact lookup
            looked_up = svc.lookup_command(
                m["vendor"], m["platform"], m["command_pattern"]
            )
            assert looked_up is not None
            assert looked_up.mapped_rule_id == concept["mapped_rule_id"]

    svc.close()
