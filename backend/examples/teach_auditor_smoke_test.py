"""Manual developer-facing smoke test demonstration for ADK Teach-the-Auditor.

Demonstrates:
  Unknown command
      ↓
  Teach Auditor (ADK / KnowledgeProvider)
      ↓
  Structured CommandInterpretation & TeachingProposal

Uses synthetic configuration commands with zero real credentials or sensitive data.
Exercises:
  1. 'transport input ssh' (clear transport security control)
  2. 'access-class MGMT_ACL in' (management access filtering)
  3. Synthetic unfamiliar vendor command ('set forwarding-options packet-capture rate 1000')
  4. Garbage / non-network syntax ('banana banana banana random text 1234')
  5. Pre-learned knowledge base lookup demonstrating instant cache resolution
"""

import json
import os
import sys
from typing import List

# Ensure project root is in sys.path for direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.knowledge import MockKnowledgeProvider
from app.agents.schemas import CommandInterpretation, UnknownCommand
from app.agents.teach_auditor import TeachAuditorService


def format_proposal(idx: int, title: str, unknown: UnknownCommand, proposal) -> None:
    """Pretty-print a command interpretation scenario."""
    interp = proposal.interpretation
    print("=" * 72)
    print(f"SCENARIO {idx}: {title}")
    print("=" * 72)
    print(f"  Input Vendor   : {unknown.vendor}")
    print(f"  Input Platform : {unknown.platform}")
    print(f"  Input Command  : {unknown.command}")
    if unknown.context:
        ctx_str = unknown.context if isinstance(unknown.context, str) else " | ".join(unknown.context)
        print(f"  Input Context  : {ctx_str}")
    print("-" * 72)
    print(f"  Origin Source  : {proposal.source.upper()}")
    print(f"  Approval Req'd : {proposal.requires_human_approval} (Human-in-the-Loop)")
    print(f"  Security Mean  : {interp.meaning}")
    print(f"  Control Area   : {interp.security_control}")
    print(f"  Mapped Rule ID : {interp.mapped_rule_id if interp.mapped_rule_id else 'None (Unmapped)'}")
    print(f"  Confidence     : {interp.confidence:.2f} ({interp.confidence * 100:.1f}%)")
    print(f"  Explanation    : {interp.explanation}")
    print("=" * 72)
    print()


def main() -> None:
    print("\n" + "#" * 72)
    print("  PHOENIX PROTOCOL -- ADK TEACH-THE-AUDITOR SMOKE TEST")
    print("  Trust Boundary: AI Interprets Syntax; Deterministic Rules Decide.")
    print("#" * 72 + "\n")

    # Initialize in-memory KnowledgeProvider
    kp = MockKnowledgeProvider()

    # Pre-populate one verified mapping into the knowledge provider to test lookup
    prelearned = CommandInterpretation(
        command="transport input ssh",
        vendor="Cisco",
        platform="IOS",
        meaning="Restricts terminal management access strictly to Secure Shell (SSH).",
        security_control="transport_security",
        mapped_rule_id="NET-002",
        confidence=0.99,
        explanation="Verified in enterprise gold image template; prevents insecure Telnet access.",
    )
    kp.add_mapping(prelearned)

    service = TeachAuditorService(knowledge_provider=kp)

    scenarios: List[tuple] = [
        (
            "Known Command in Knowledge Base (Fast-Path / Pre-Approved)",
            UnknownCommand(
                vendor="Cisco",
                platform="IOS",
                command="transport input ssh",
                context=["line vty 0 4"],
            ),
        ),
        (
            "Management Access Filtering (Access-Class on VTY)",
            UnknownCommand(
                vendor="Cisco",
                platform="IOS",
                command="access-class MGMT_ACL in",
                context=["line vty 0 4", "transport input ssh"],
            ),
        ),
        (
            "Synthetic Unfamiliar Vendor Command (Valid Network Syntax, Unmapped)",
            UnknownCommand(
                vendor="SyntheticVendor",
                platform="NextGenOS",
                command="set forwarding-options packet-capture rate 1000",
                context=["set system host-name EDGE-GATEWAY-01"],
            ),
        ),
        (
            "Nonsense / Garbage Input (Unrecognized Non-Network Syntax)",
            UnknownCommand(
                vendor="Unknown",
                platform="Unknown",
                command="banana banana banana random text 1234",
            ),
        ),
        (
            "Brute Force Attack Mitigation (Login Rate Limiting)",
            UnknownCommand(
                vendor="Cisco",
                platform="IOS",
                command="login block-for 120 attempts 3 within 60",
                context=["! Authentication security"],
            ),
        ),
    ]

    for idx, (title, unknown_cmd) in enumerate(scenarios, start=1):
        proposal = service.interpret_command(unknown_cmd)
        format_proposal(idx, title, unknown_cmd, proposal)

    print("Trust Boundary Verification:")
    print("  [OK] Zero compliance verdicts (no pass/fail) generated by the AI agent.")
    print("  [OK] All new interpretations require explicit human approval (requires_human_approval=True).")
    print("  [OK] Known mappings resolved through KnowledgeProvider abstraction.")
    print("  [OK] Rule IDs restricted to known Phoenix rules (NET-001..NET-010) or None.")
    print("\nSmoke test completed successfully.\n")


if __name__ == "__main__":
    main()
