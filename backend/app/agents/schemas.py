"""Structured schemas for Teach-the-Auditor intelligence layer.

Defines typed models for unknown network configuration commands, AI interpretations,
and human-in-the-loop teaching proposals.
Adheres to the Phoenix Protocol trust boundary:
- AI explains command meaning and security context.
- AI NEVER makes a pass/fail compliance decision.
- Rule mapping is optional; AI never invents unknown rule IDs.
- High-consequence actions require explicit human approval.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


# Curated, authoritative set of baseline Phoenix Protocol compliance rules
KNOWN_PHOENIX_RULES = {
    "NET-001",
    "NET-002",
    "NET-003",
    "NET-004",
    "NET-005",
    "NET-006",
    "NET-007",
    "NET-008",
    "NET-009",
    "NET-010",
}


class UnknownCommand(BaseModel):
    """Input contract for an unfamiliar or unmapped network configuration command."""

    vendor: str = Field(..., description="Device vendor (e.g., Cisco, Arista, Juniper, Palo Alto).")
    platform: str = Field(..., description="Device operating platform (e.g., IOS, EOS, JunOS, PAN-OS).")
    command: str = Field(..., min_length=1, description="The raw or normalized configuration command string.")
    context: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Surrounding configuration block lines providing context.",
    )
    source_line: Optional[int] = Field(
        default=None,
        ge=1,
        description="Optional 1-based source line number in the original configuration file.",
    )

    @field_validator("command")
    @classmethod
    def sanitize_and_bound_command(cls, v: str) -> str:
        """Sanitize secrets and bound maximum length defensively."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty or whitespace only.")
        clean = v.strip()
        # Bound excessive length to prevent memory/token exhaustion
        if len(clean) > 4096:
            clean = clean[:4096]
        # Redact credentials and keys defensively
        from app.security.sanitization import sanitize_evidence
        return sanitize_evidence(clean)

    @field_validator("vendor", "platform")
    @classmethod
    def sanitize_metadata(cls, v: str) -> str:
        if not v or not v.strip():
            return "Unknown"
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary representation."""
        return {
            "vendor": self.vendor,
            "platform": self.platform,
            "command": self.command,
            "context": self.context,
            "source_line": self.source_line,
        }



class CommandInterpretation(BaseModel):
    """Structured security interpretation produced by the Teach-the-Auditor agent.

    Trust boundary:
    This model captures semantic meaning, relevant security control, and confidence.
    It deliberately does NOT contain compliance verdicts ('pass'/'fail'), which are
    reserved solely for deterministic rule evaluation.
    """

    command: str = Field(..., description="The command being interpreted.")
    vendor: str = Field(..., description="Target vendor.")
    platform: str = Field(..., description="Target platform/OS.")
    meaning: str = Field(..., min_length=1, description="Concise explanation of what the command configures.")
    security_control: str = Field(
        ...,
        min_length=1,
        description="The security domain/control area (e.g. management_access, logging, encryption, authentication).",
    )
    mapped_rule_id: Optional[str] = Field(
        default=None,
        description="Authoritative Phoenix rule ID (NET-001 to NET-010) if confidently mapped; null otherwise.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )
    explanation: str = Field(
        ...,
        min_length=1,
        description="Rationale justifying the interpretation and any mapped rule.",
    )

    @field_validator("mapped_rule_id")
    @classmethod
    def validate_mapped_rule_id(cls, v: Optional[str]) -> Optional[str]:
        """Ensure mapped_rule_id is either None or one of the known Phoenix rule IDs.

        Never allows arbitrary or hallucinated rule IDs.
        """
        if v is None:
            return None
        cleaned = v.strip().upper()
        if not cleaned:
            return None
        if cleaned not in KNOWN_PHOENIX_RULES:
            raise ValueError(
                f"Unknown Phoenix rule ID '{v}'. Must be one of {sorted(KNOWN_PHOENIX_RULES)} or null."
            )
        return cleaned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary representation."""
        return {
            "command": self.command,
            "vendor": self.vendor,
            "platform": self.platform,
            "meaning": self.meaning,
            "security_control": self.security_control,
            "mapped_rule_id": self.mapped_rule_id,
            "confidence": round(self.confidence, 4),
            "explanation": self.explanation,
        }


class TeachingProposal(BaseModel):
    """Proposal generated by Teach-the-Auditor requiring human review before persistence."""

    interpretation: CommandInterpretation = Field(
        ...,
        description="The structured security interpretation.",
    )
    requires_human_approval: bool = Field(
        default=True,
        description="Flag enforcing human-in-the-loop approval before knowledge persistence.",
    )
    source: str = Field(
        default="ai_agent",
        description="Origin of the interpretation ('knowledge_base' or 'ai_agent').",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary representation."""
        return {
            "interpretation": self.interpretation.to_dict(),
            "requires_human_approval": self.requires_human_approval,
            "source": self.source,
        }


class RemediationSuggestion(BaseModel):
    """Structured remediation proposal generated by the ADK Remediation Agent.

    Strict trust & safety boundaries:
    - Remediation is strictly ADVISORY.
    - Zero automatic execution (no subprocess, no shell, no live device mutation).
    - Requires explicit human approval before any operational change.
    - Cannot invent nonexistent rule IDs.
    - Secrets are never reflected in recommendations.
    """

    rule_id: str = Field(..., description="The authoritative Phoenix rule ID (NET-001 to NET-010).")
    vendor: str = Field(..., description="Target device vendor.")
    platform: str = Field(..., description="Target device platform/OS.")
    current_state: str = Field(..., min_length=1, description="Description of the non-compliant configuration state.")
    recommended_change: str = Field(..., min_length=1, description="Specific configuration commands or changes recommended.")
    example_configuration: str = Field(..., description="Syntactically valid snippet illustrating the recommended fix.")
    explanation: str = Field(..., min_length=1, description="Security rationale explaining why this change is necessary.")
    risk_if_unfixed: str = Field(..., min_length=1, description="Impact and threat exposure if left unaddressed.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    requires_human_approval: bool = Field(
        default=True,
        description="Enforces mandatory human review prior to adopting this remediation.",
    )

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if cleaned not in KNOWN_PHOENIX_RULES:
            raise ValueError(
                f"Unknown Phoenix rule ID '{v}'. Must be one of {sorted(KNOWN_PHOENIX_RULES)}."
            )
        return cleaned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "vendor": self.vendor,
            "platform": self.platform,
            "current_state": self.current_state,
            "recommended_change": self.recommended_change,
            "example_configuration": self.example_configuration,
            "explanation": self.explanation,
            "risk_if_unfixed": self.risk_if_unfixed,
            "confidence": round(self.confidence, 4),
            "requires_human_approval": self.requires_human_approval,
        }


class FindingExplanation(BaseModel):
    """Structured plain-language security explanation for a deterministic finding.

    Adheres to the core principle:
    - Rules decide compliance; AI explains what findings mean.
    - Does not alter deterministic severity, status, or score.
    """

    rule_id: str = Field(..., description="The evaluated Phoenix rule ID.")
    severity: str = Field(..., description="Deterministic finding severity (high, medium, low).")
    summary: str = Field(..., min_length=1, description="Concise summary of the security finding.")
    why_it_matters: str = Field(..., min_length=1, description="Security risks and practical impact.")
    evidence_explanation: str = Field(..., description="Interpretation of the specific configuration evidence.")
    recommended_action: str = Field(..., min_length=1, description="High-level security guidance to resolve the finding.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Explanation confidence score.")

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if cleaned not in KNOWN_PHOENIX_RULES:
            raise ValueError(
                f"Unknown Phoenix rule ID '{v}'. Must be one of {sorted(KNOWN_PHOENIX_RULES)}."
            )
        return cleaned

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in {"critical", "high", "medium", "low", "info"}:
            raise ValueError(f"Invalid severity '{v}'.")
        return cleaned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "summary": self.summary,
            "why_it_matters": self.why_it_matters,
            "evidence_explanation": self.evidence_explanation,
            "recommended_action": self.recommended_action,
            "confidence": round(self.confidence, 4),
        }

