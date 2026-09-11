"""Integration contract and typed protocols for Developer 1 integration.

Defines the contract between the future Teach-the-Auditor AI agent, the auditor approval
workflow, and the deterministic scanner. This file contains NO imports of Google ADK,
Gemini, or any LLM SDK.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

try:
    from .models.knowledge_mapping import KnowledgeMapping
except ImportError:
    from models.knowledge_mapping import KnowledgeMapping


class AgentCommandInterpretation:
    """Contract describing the structured output expected from a future Teach-the-Auditor agent.

    When the future agent analyzes an unknown command, it must supply this structured data
    to KnowledgeService.propose_mapping().
    """

    def __init__(
        self,
        vendor: str,
        platform: str,
        command_pattern: str,
        meaning: str,
        security_control: str,
        mapped_rule_id: Optional[str] = None,
        explanation: str = "",
        confidence: float = 1.0,
        source: str = "ai_agent",
    ):
        self.vendor = vendor
        self.platform = platform
        self.command_pattern = command_pattern
        self.meaning = meaning
        self.security_control = security_control
        self.mapped_rule_id = mapped_rule_id
        self.explanation = explanation
        self.confidence = confidence
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor": self.vendor,
            "platform": self.platform,
            "command_pattern": self.command_pattern,
            "meaning": self.meaning,
            "security_control": self.security_control,
            "mapped_rule_id": self.mapped_rule_id,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "source": self.source,
        }


@runtime_checkable
class KnowledgeServiceInterface(Protocol):
    """Public protocol for the Teach the Auditor knowledge service.

    Developer 1's integration should depend strictly on this interface.
    Callers must NEVER directly manipulate the SQLite database.
    """

    def propose_mapping(
        self,
        vendor: str,
        platform: str,
        command_pattern: str,
        meaning: str,
        security_control: str,
        mapped_rule_id: Optional[str] = None,
        explanation: str = "",
        confidence: float = 1.0,
        source: str = "ai_agent",
    ) -> KnowledgeMapping:
        """Submit a newly interpreted command mapping for human approval.

        Status will always be 'proposed'.
        Enforces validate -> normalize -> sanitize -> persist.
        """
        ...

    def approve_mapping(self, mapping_id: str) -> KnowledgeMapping:
        """Promote a proposed mapping to 'approved' status.

        Only approved mappings can ever be retrieved by lookup_command().
        Raises DuplicateMappingError if an identical approved mapping already exists.
        """
        ...

    def reject_mapping(
        self, mapping_id: str, reason: Optional[str] = None
    ) -> KnowledgeMapping:
        """Reject a proposed mapping, keeping it for audit history while excluding from lookup."""
        ...

    def lookup_command(
        self,
        vendor: str,
        platform: str,
        command: str,
    ) -> Optional[KnowledgeMapping]:
        """Look up an approved command meaning for the scanner engine.

        Returns None if no approved mapping exists.
        Never returns proposed or rejected mappings.
        """
        ...

    def list_approved_knowledge(
        self,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[KnowledgeMapping]:
        """List currently active and approved knowledge mappings."""
        ...

    def list_proposals(
        self,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[KnowledgeMapping]:
        """List proposals awaiting human review and approval."""
        ...
