"""Phoenix Auditor Orchestrator coordinating AI Intelligence with Deterministic Compliance.

Architecture:
  Deterministic Parser & Scanner
        ↓
  Deterministic Rule Engine (Sole authority on pass/fail and scores)
        ↓
  Orchestrator
    ├── Teach-the-Auditor: Explains unfamiliar configuration syntax
    ├── Finding Explainer: Explains why compliance findings matter
    └── Remediation Agent: Proposes vendor-specific advisory fixes
        ↓
  Human-in-the-Loop Review: Authorizes knowledge persistence and remediation
"""

from typing import Any, Dict, List, Optional

from app.agents.audit_bridge import AuditorLearningBridge
from app.agents.explanation import FindingExplainer
from app.agents.knowledge import KnowledgeProvider, MockKnowledgeProvider
from app.agents.remediation import RemediationService
from app.agents.schemas import (
    FindingExplanation,
    RemediationSuggestion,
    TeachingProposal,
    UnknownCommand,
)
from app.agents.teach_auditor import TeachAuditorService


class PhoenixAuditorOrchestrator:
    """Minimal, high-clarity orchestrator coordinating audit intelligence."""

    def __init__(
        self,
        knowledge_provider: Optional[KnowledgeProvider] = None,
        teach_service: Optional[TeachAuditorService] = None,
        remediation_service: Optional[RemediationService] = None,
        explanation_service: Optional[FindingExplainer] = None,
    ) -> None:
        self.knowledge_provider = (
            knowledge_provider if knowledge_provider is not None else MockKnowledgeProvider()
        )
        self.teach_service = (
            teach_service
            if teach_service is not None
            else TeachAuditorService(knowledge_provider=self.knowledge_provider)
        )
        self.remediation_service = (
            remediation_service if remediation_service is not None else RemediationService()
        )
        self.explanation_service = (
            explanation_service if explanation_service is not None else FindingExplainer()
        )
        self.learning_bridge = AuditorLearningBridge(
            knowledge_provider=self.knowledge_provider,
            teach_service=self.teach_service,
        )

    def enhance_scan_results(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich deterministic scan output with AI explanations and advisory remediations.

        Strict invariant:
        Deterministic status, severities, compliance scores, and rule verdicts
        are preserved completely unchanged. AI only provides explanation and remediation.
        """
        enhanced_scan = dict(scan_result)
        enhanced_devices: List[Dict[str, Any]] = []

        for device in scan_result.get("devices", []):
            dev_copy = dict(device)
            dev_vendor = device.get("vendor", "Cisco")
            dev_platform = device.get("device_type", "cisco_ios")
            enhanced_results: List[Dict[str, Any]] = []

            for res in device.get("results", []):
                res_copy = dict(res)
                rule_id = res.get("rule_id", "NET-001")
                status = res.get("status", "pass")
                severity = res.get("severity", "medium")
                evidence = res.get("evidence", "")

                # AI enhancement is attached only to findings needing explanation/action (fail / warning)
                if status in {"fail", "warning"}:
                    explanation = self.explanation_service.explain(
                        rule_id=rule_id,
                        severity=severity,
                        evidence=evidence,
                        vendor=dev_vendor,
                        platform=dev_platform,
                    )
                    res_copy["ai_explanation"] = explanation.to_dict()

                    remediation = self.remediation_service.generate_remediation(
                        rule_id=rule_id,
                        vendor=dev_vendor,
                        platform=dev_platform,
                        evidence=evidence,
                        severity=severity,
                    )
                    res_copy["ai_remediation"] = remediation.to_dict()

                enhanced_results.append(res_copy)

            dev_copy["results"] = enhanced_results
            enhanced_devices.append(dev_copy)

        enhanced_scan["devices"] = enhanced_devices
        enhanced_scan["ai_enhanced"] = True
        return enhanced_scan

    def teach_unfamiliar_command(
        self,
        command: str,
        vendor: str = "Cisco",
        platform: str = "cisco_ios",
        context: Optional[List[str]] = None,
    ) -> TeachingProposal:
        """Interpret an unfamiliar command through Teach-the-Auditor."""
        unknown = UnknownCommand(
            vendor=vendor,
            platform=platform,
            command=command,
            context=context or [],
        )
        return self.teach_service.interpret_command(unknown)
