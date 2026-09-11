from typing import Any, Dict, List

from app.models import Diagnostic, Evidence, NormalizedSetting, RuleResult, Status


class Rule:
    def __init__(
        self,
        rule_id: str,
        title: str,
        category: str,
        severity: str,
        description: str,
        required_settings: List[str],
        version: str = "1.0",
    ):
        self.rule_id = rule_id
        self.title = title
        self.category = category
        self.severity = severity
        self.description = description
        self.required_settings = required_settings
        self.version = version

    def evaluate(self, settings_map: Dict[str, NormalizedSetting]) -> RuleResult:
        raise NotImplementedError()

    def _create_evidence(
        self, setting: NormalizedSetting, expected_value: Any
    ) -> Evidence:
        observed_value = setting.value if not setting.sensitive else "***REDACTED***"

        return Evidence(
            setting_key=setting.key,
            observed_value=observed_value,
            expected_value=expected_value,
            source_line_start=setting.source_line_start,
            source_line_end=setting.source_line_end,
            source_text=(
                setting.source_text if not setting.sensitive else "***REDACTED***"
            ),
            safe_to_display=not setting.sensitive,
        )

    def _missing_evidence(self, key: str, expected_value: Any) -> Evidence:
        return Evidence(
            setting_key=key,
            observed_value=None,
            expected_value=expected_value,
            source_line_start=None,
            source_line_end=None,
            source_text=None,
            safe_to_display=True,
        )


class AuthMfaRule(Rule):
    def __init__(self):
        super().__init__(
            rule_id="AUTH-MFA-001",
            title="Multi-factor authentication enabled",
            category="authentication",
            severity="high",
            description="Administrative access requires multi-factor authentication.",
            required_settings=["authentication.mfa_enabled"],
        )

    def evaluate(self, settings_map: Dict[str, NormalizedSetting]) -> RuleResult:
        key = "authentication.mfa_enabled"
        setting = settings_map.get(key)

        if not setting:
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                status=Status.AMBIGUOUS,
                rationale=f"Missing setting: {key}",
                evidence=[self._missing_evidence(key, True)],
            )

        if setting.value_type != "boolean":
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                status=Status.AMBIGUOUS,
                rationale=f"Invalid value type for {key}",
                evidence=[self._create_evidence(setting, True)],
            )

        is_compliant = setting.value is True
        status = Status.COMPLIANT if is_compliant else Status.FAILING

        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            category=self.category,
            severity=self.severity,
            status=status,
            rationale="MFA is enabled" if is_compliant else "MFA is not enabled",
            evidence=[self._create_evidence(setting, True)],
        )


class AuthPwdLengthRule(Rule):
    def __init__(self):
        super().__init__(
            rule_id="AUTH-PWD-001",
            title="Minimum password length meets policy",
            category="authentication",
            severity="medium",
            description="Password minimum length must be at least 12.",
            required_settings=["authentication.password_min_length"],
        )

    def evaluate(self, settings_map: Dict[str, NormalizedSetting]) -> RuleResult:
        key = "authentication.password_min_length"
        setting = settings_map.get(key)

        if not setting:
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                status=Status.AMBIGUOUS,
                rationale=f"Missing setting: {key}",
                evidence=[self._missing_evidence(key, ">= 12")],
            )

        if setting.value_type != "integer":
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                status=Status.AMBIGUOUS,
                rationale=f"Invalid value type for {key}",
                evidence=[self._create_evidence(setting, ">= 12")],
            )

        is_compliant = int(setting.value) >= 12 if setting.value is not None else False
        status = Status.COMPLIANT if is_compliant else Status.FAILING

        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            category=self.category,
            severity=self.severity,
            status=status,
            rationale=(
                "Password length is compliant"
                if is_compliant
                else "Password length is too short"
            ),
            evidence=[self._create_evidence(setting, ">= 12")],
        )


class BooleanRule(Rule):
    def __init__(self, rule_id, title, category, severity, description, key, expected):
        super().__init__(
            rule_id=rule_id,
            title=title,
            category=category,
            severity=severity,
            description=description,
            required_settings=[key],
        )
        self.key = key
        self.expected = expected

    def evaluate(self, settings_map: Dict[str, NormalizedSetting]) -> RuleResult:
        setting = settings_map.get(self.key)

        if not setting:
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                status=Status.AMBIGUOUS,
                rationale=f"Missing setting: {self.key}",
                evidence=[self._missing_evidence(self.key, self.expected)],
            )

        if setting.value_type != "boolean":
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                status=Status.AMBIGUOUS,
                rationale=f"Invalid value type for {self.key}",
                evidence=[self._create_evidence(setting, self.expected)],
            )

        is_compliant = setting.value == self.expected
        status = Status.COMPLIANT if is_compliant else Status.FAILING

        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            category=self.category,
            severity=self.severity,
            status=status,
            rationale="Setting is compliant" if is_compliant else "Setting is failing",
            evidence=[self._create_evidence(setting, self.expected)],
        )


# Register all rules
def get_all_rules() -> List[Rule]:
    return [
        AuthMfaRule(),
        AuthPwdLengthRule(),
        BooleanRule(
            "AUTH-PWD-002",
            "Password complexity enabled",
            "authentication",
            "medium",
            "Password complexity must be enabled.",
            "authentication.password_complexity_enabled",
            True,
        ),
        BooleanRule(
            "ACCESS-ADM-001",
            "Default admin disabled",
            "access",
            "high",
            "Default admin account must be disabled.",
            "access.default_admin_disabled",
            True,
        ),
        BooleanRule(
            "NET-SSH-001",
            "Secure remote administration enabled",
            "network",
            "high",
            "SSH must be enabled.",
            "network.ssh.enabled",
            True,
        ),
        BooleanRule(
            "NET-PORT-001",
            "Insecure management port disabled",
            "network",
            "high",
            "Insecure port must be disabled.",
            "network.insecure_management_port.enabled",
            False,
        ),
        BooleanRule(
            "LOG-AUD-001",
            "Audit logging enabled",
            "logging",
            "medium",
            "Audit logging must be enabled.",
            "logging.audit.enabled",
            True,
        ),
        BooleanRule(
            "TIME-NTP-001",
            "Trusted time synchronization configured",
            "time",
            "low",
            "NTP must be enabled.",
            "time.ntp.enabled",
            True,
        ),
    ]


def evaluate_all(settings_map: Dict[str, NormalizedSetting]) -> List[RuleResult]:
    rules = get_all_rules()
    # Ensure deterministic rule-ID order
    rules.sort(key=lambda r: r.rule_id)

    results = []
    for rule in rules:
        try:
            results.append(rule.evaluate(settings_map))
        except Exception as e:
            results.append(
                RuleResult(
                    rule_id=rule.rule_id,
                    title=rule.title,
                    category=rule.category,
                    severity=rule.severity,
                    status=Status.ERROR,
                    rationale=f"Internal rule error: {str(e)}",
                    diagnostics=[
                        Diagnostic(
                            code="INTERNAL_RULE_ERROR",
                            message=str(e),
                            severity="error",
                            source_line_start=None,
                            source_line_end=None,
                            field=None,
                        )
                    ],
                )
            )

    return results
