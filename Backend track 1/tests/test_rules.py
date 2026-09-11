from app.models import NormalizedSetting, Status
from app.rules import evaluate_all


def test_rules_compliant():
    settings = {
        "authentication.mfa_enabled": NormalizedSetting(
            key="authentication.mfa_enabled",
            value=True,
            value_type="boolean",
            source_line_start=1,
            source_line_end=1,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "authentication.password_min_length": NormalizedSetting(
            key="authentication.password_min_length",
            value=14,
            value_type="integer",
            source_line_start=2,
            source_line_end=2,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "authentication.password_complexity_enabled": NormalizedSetting(
            key="authentication.password_complexity_enabled",
            value=True,
            value_type="boolean",
            source_line_start=3,
            source_line_end=3,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "access.default_admin_disabled": NormalizedSetting(
            key="access.default_admin_disabled",
            value=True,
            value_type="boolean",
            source_line_start=4,
            source_line_end=4,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "network.ssh.enabled": NormalizedSetting(
            key="network.ssh.enabled",
            value=True,
            value_type="boolean",
            source_line_start=5,
            source_line_end=5,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "network.insecure_management_port.enabled": NormalizedSetting(
            key="network.insecure_management_port.enabled",
            value=False,
            value_type="boolean",
            source_line_start=6,
            source_line_end=6,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "logging.audit.enabled": NormalizedSetting(
            key="logging.audit.enabled",
            value=True,
            value_type="boolean",
            source_line_start=7,
            source_line_end=7,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "time.ntp.enabled": NormalizedSetting(
            key="time.ntp.enabled",
            value=True,
            value_type="boolean",
            source_line_start=8,
            source_line_end=8,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
    }

    results = evaluate_all(settings)
    assert len(results) == 8
    for r in results:
        assert r.status == Status.COMPLIANT


def test_rules_failing():
    settings = {
        "authentication.mfa_enabled": NormalizedSetting(
            key="authentication.mfa_enabled",
            value=False,
            value_type="boolean",
            source_line_start=1,
            source_line_end=1,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "authentication.password_min_length": NormalizedSetting(
            key="authentication.password_min_length",
            value=8,
            value_type="integer",
            source_line_start=2,
            source_line_end=2,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "authentication.password_complexity_enabled": NormalizedSetting(
            key="authentication.password_complexity_enabled",
            value=False,
            value_type="boolean",
            source_line_start=3,
            source_line_end=3,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "access.default_admin_disabled": NormalizedSetting(
            key="access.default_admin_disabled",
            value=False,
            value_type="boolean",
            source_line_start=4,
            source_line_end=4,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "network.ssh.enabled": NormalizedSetting(
            key="network.ssh.enabled",
            value=False,
            value_type="boolean",
            source_line_start=5,
            source_line_end=5,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "network.insecure_management_port.enabled": NormalizedSetting(
            key="network.insecure_management_port.enabled",
            value=True,
            value_type="boolean",
            source_line_start=6,
            source_line_end=6,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "logging.audit.enabled": NormalizedSetting(
            key="logging.audit.enabled",
            value=False,
            value_type="boolean",
            source_line_start=7,
            source_line_end=7,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
        "time.ntp.enabled": NormalizedSetting(
            key="time.ntp.enabled",
            value=False,
            value_type="boolean",
            source_line_start=8,
            source_line_end=8,
            source_text="",
            confidence="high",
            sensitive=False,
        ),
    }
    results = evaluate_all(settings)
    assert len(results) == 8
    for r in results:
        assert r.status == Status.FAILING


def test_rules_ambiguous():
    results = evaluate_all({})
    assert len(results) == 8
    for r in results:
        assert r.status == Status.AMBIGUOUS
