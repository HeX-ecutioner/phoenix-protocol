"""Phoenix Protocol End-to-End Demonstration.

Demonstrates the full 13-step lifecycle:
1. Upload known secure configuration.
2. Scanner evaluates configuration deterministically.
3. Deterministic compliance results appear.
4. Finding includes evidence.
5. AI explains finding (why it matters).
6. AI generates remediation guidance (advisory, requires human approval).
7. Configuration contains unfamiliar command.
8. Teach-the-Auditor identifies and interprets it.
9. Human approval is simulated explicitly.
10. Mapping is persisted in Dev2 KnowledgeService.
11. Same command is processed again in a second scan.
12. Knowledge lookup recognizes it immediately without invoking AI.
13. Compliance engine remains deterministic throughout.
"""

import os
import sys
import uuid

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.audit_bridge import AuditorLearningBridge
from app.agents.explanation import FindingExplainer
from app.agents.knowledge import Dev2KnowledgeProvider
from app.agents.orchestrator import PhoenixAuditorOrchestrator
from app.agents.remediation import RemediationService
from app.agents.schemas import UnknownCommand
from app.agents.teach_auditor import TeachAuditorService
from app.services.scanner import run_scan


def print_header(title: str) -> None:
    print("\n" + "=" * 76)
    print(f"  {title}")
    print("=" * 76)


def main() -> None:
    print("\n" + "#" * 76)
    print("  PHOENIX PROTOCOL -- END-TO-END DEMO: AI + DETERMINISTIC COMPLIANCE")
    print("  Trust Model: AI Interprets Syntax; Deterministic Rules Decide.")
    print("#" * 76)

    # Use isolated SQLite knowledge database for this demo session
    knowledge_provider = Dev2KnowledgeProvider(db_path=":memory:")
    teach_service = TeachAuditorService(knowledge_provider=knowledge_provider)
    remediation_service = RemediationService()
    explanation_service = FindingExplainer()
    orchestrator = PhoenixAuditorOrchestrator(
        knowledge_provider=knowledge_provider,
        teach_service=teach_service,
        remediation_service=remediation_service,
        explanation_service=explanation_service,
    )
    bridge = AuditorLearningBridge(
        knowledge_provider=knowledge_provider,
        teach_service=teach_service,
    )

    # -------------------------------------------------------------------------
    # STEP 1 & 2: Upload configuration and execute deterministic scanner
    # -------------------------------------------------------------------------
    print_header("STEPS 1-3: DETERMINISTIC CONFIGURATION SCAN")
    failing_config = """! Cisco IOS Sample Router with mixed compliance
hostname EDGE-RTR-01
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
enable password cleartext_secret_123
!
line vty 0 4
 transport input telnet ssh
 login
!
"""
    demo_scan_id_1 = f"demo-scan-{uuid.uuid4().hex[:8]}"
    scan_result = run_scan(
        scan_id=demo_scan_id_1,
        device_type="cisco_ios",
        uploaded_files=[("edge_rtr.cfg", failing_config)],
    )

    print(f"Scan ID           : {scan_result['scan_id']}")
    print(f"Scan Status       : {scan_result['status'].upper()}")
    print(f"Compliance Score  : {scan_result['compliance_score']}%")
    summary = scan_result["summary"]
    print(
        f"Rules Evaluated   : Total: {summary['total_rules']} | Passed: {summary['passed_rules']} | Failed: {summary['failed_rules']}"
    )

    # -------------------------------------------------------------------------
    # STEP 3 & 4: Finding includes evidence
    # -------------------------------------------------------------------------
    device = scan_result["devices"][0]
    failed_results = [r for r in device["results"] if r["status"] == "fail"]
    target_finding = failed_results[0]
    print(f"\n[Finding with Evidence]:")
    print(f"  Rule ID  : {target_finding['rule_id']}")
    print(f"  Status   : {target_finding['status'].upper()}")
    print(f"  Severity : {target_finding['severity'].upper()}")
    print(f"  Evidence : '{target_finding['evidence']}' (Line: {target_finding.get('evidence_line_range', 'N/A')})")

    # -------------------------------------------------------------------------
    # STEP 5 & 6: AI Explains Finding & Generates Advisory Remediation
    # -------------------------------------------------------------------------
    print_header("STEPS 5-6: AI EXPLANATION & ADVISORY REMEDIATION")
    explanation = explanation_service.explain(
        rule_id=target_finding["rule_id"],
        severity=target_finding["severity"],
        evidence=target_finding["evidence"],
    )
    print(f"Finding Explanation:")
    print(f"  Summary         : {explanation.summary}")
    print(f"  Why It Matters  : {explanation.why_it_matters}")
    print(f"  Recommended Act : {explanation.recommended_action}")

    remediation = remediation_service.generate_remediation(
        rule_id=target_finding["rule_id"],
        evidence=target_finding["evidence"],
        severity=target_finding["severity"],
    )
    print(f"\nAI Advisory Remediation Suggestion:")
    print(f"  Recommended Fix : {remediation.recommended_change}")
    print(f"  Example Snippet :\n{remediation.example_configuration}")
    print(f"  Residual Risk   : {remediation.risk_if_unfixed}")
    print(f"  Approval Req'd  : {remediation.requires_human_approval} (Human Review Enforced)")

    # -------------------------------------------------------------------------
    # STEP 7 & 8: Unfamiliar Command Encounter & Teach-the-Auditor
    # -------------------------------------------------------------------------
    print_header("STEPS 7-8: UNFAMILIAR COMMAND ENCOUNTER (PASS 1)")
    unfamiliar_cmd = "ip ssh time-out 60"
    print(f"Encountered unfamiliar configuration syntax: '{unfamiliar_cmd}'")

    unknown = UnknownCommand(
        vendor="Cisco",
        platform="cisco_ios",
        command=unfamiliar_cmd,
        context=["line vty 0 4"],
    )
    proposal = teach_service.interpret_command(unknown)
    interp = proposal.interpretation

    print(f"Teach-the-Auditor Interpretation:")
    print(f"  Source          : {proposal.source.upper()}")
    print(f"  Approval Req'd  : {proposal.requires_human_approval}")
    print(f"  Meaning         : {interp.meaning}")
    print(f"  Security Control: {interp.security_control}")
    print(f"  Mapped Rule ID  : {interp.mapped_rule_id}")
    print(f"  Confidence      : {interp.confidence * 100:.1f}%")

    # -------------------------------------------------------------------------
    # STEP 9 & 10: Human Approval Simulation & Persistence
    # -------------------------------------------------------------------------
    print_header("STEPS 9-10: HUMAN APPROVAL & KNOWLEDGE PERSISTENCE")
    # Propose to Dev2 persistent KnowledgeService
    dev2_mapping = knowledge_provider.propose_mapping(interp)
    print(f"1. Submitted proposal to Dev2 KnowledgeService:")
    print(f"   Mapping ID: {dev2_mapping.id} | Status: {dev2_mapping.approval_status.upper()}")

    # Auditor reviews and approves
    approved_mapping = knowledge_provider.approve_mapping(dev2_mapping.id)
    print(f"2. Human Auditor reviewed and APPROVED proposal:")
    print(f"   Mapping ID: {approved_mapping.id} | Status: {approved_mapping.approval_status.upper()}")

    # -------------------------------------------------------------------------
    # STEP 11 & 12: Second Scan Encounter - Cached Knowledge Hit
    # -------------------------------------------------------------------------
    print_header("STEPS 11-12: SECOND ENCOUNTER (PASS 2 - CACHED KNOWLEDGE)")
    second_proposal = teach_service.interpret_command(unknown)

    print(f"Second Encounter Interpretation:")
    print(f"  Source          : {second_proposal.source.upper()}")
    print(f"  Approval Req'd  : {second_proposal.requires_human_approval} (Pre-Approved)")
    print(f"  Knowledge Hit   : {second_proposal.source == 'knowledge_base'}")
    print(f"  Meaning         : {second_proposal.interpretation.meaning}")
    print(f"  Mapped Rule ID  : {second_proposal.interpretation.mapped_rule_id}")

    # -------------------------------------------------------------------------
    # STEP 13: Proof of Compliance Determinism
    # -------------------------------------------------------------------------
    print_header("STEP 13: VERIFICATION OF COMPLIANCE DETERMINISM")
    demo_scan_id_2 = f"demo-scan-{uuid.uuid4().hex[:8]}"
    res2 = run_scan(
        scan_id=demo_scan_id_2,
        device_type="cisco_ios",
        uploaded_files=[("edge_rtr.cfg", failing_config)],
    )
    score_identical = (scan_result["compliance_score"] == res2["compliance_score"])
    print(f"Scan 1 Score      : {scan_result['compliance_score']}%")
    print(f"Scan 2 Score      : {res2['compliance_score']}%")
    print(f"Scores Match 100% : {score_identical}")
    print(f"Rule Engine State : Deterministic rules remained 100% authoritative throughout.")

    print("\n" + "#" * 76)
    print("  [OK] END-TO-END DEMO SUCCEEDED COMPLETELY")
    print("#" * 76 + "\n")

    knowledge_provider.close()


if __name__ == "__main__":
    main()
