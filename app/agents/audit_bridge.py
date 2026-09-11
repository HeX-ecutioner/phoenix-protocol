"""Teach-the-Auditor Scanner Bridge and Learning Loop Orchestrator.

Bridges deterministic configuration parsing/scanning and the adaptive Teach-the-Auditor
knowledge loop without modifying the authoritative deterministic rule engine.

Workflow:
  Configuration
        ↓
  Deterministic Parser
        ↓
  NormalizedConfig
        ↓
  Unfamiliar / Ambiguous Syntax
        ↓
  TeachAuditorService
        ↓
  TeachingProposal (requires_human_approval = True)
        ↓
  Human Approval Step
        ↓
  Dev2 Persistent KnowledgeService
        ↓
  Future Scans Retrieve Cached Mapping (zero AI invocation)
"""

import re
from typing import Any, Dict, List, Optional

from app.agents.knowledge import Dev2KnowledgeProvider, KnowledgeProvider, MockKnowledgeProvider
from app.agents.schemas import CommandInterpretation, TeachingProposal, UnknownCommand
from app.agents.teach_auditor import TeachAuditorService
from app.models.normalized_config import NormalizedConfig


class AuditorLearningBridge:
    """Service bridging scan normalization to adaptive Teach-the-Auditor knowledge learning."""

    def __init__(
        self,
        knowledge_provider: Optional[KnowledgeProvider] = None,
        teach_service: Optional[TeachAuditorService] = None,
    ) -> None:
        self.knowledge_provider = (
            knowledge_provider if knowledge_provider is not None else MockKnowledgeProvider()
        )
        self.teach_service = (
            teach_service
            if teach_service is not None
            else TeachAuditorService(knowledge_provider=self.knowledge_provider)
        )

    def extract_unfamiliar_commands(
        self, normalized_config: NormalizedConfig
    ) -> List[UnknownCommand]:
        """Extract unfamiliar, ambiguous, or warned configuration commands from normalized config."""
        extracted: List[UnknownCommand] = []
        vendor = normalized_config.vendor or "Cisco"
        platform = normalized_config.device_type or "cisco_ios"

        # Inspect parser warnings for flagged or unfamiliar syntax
        for warn in normalized_config.warnings:
            # Look for quoted or explicit commands in warnings
            match = re.search(r"'(.*?)'|\"(.*?)\"", warn)
            if match:
                cmd_text = match.group(1) or match.group(2)
                if cmd_text and len(cmd_text.strip()) > 2:
                    extracted.append(
                        UnknownCommand(
                            vendor=vendor,
                            platform=platform,
                            command=cmd_text.strip(),
                            context=[warn],
                        )
                    )

        return extracted

    def interpret_unknown(self, unknown: UnknownCommand) -> TeachingProposal:
        """Interpret an unfamiliar command and return a structured TeachingProposal."""
        return self.teach_service.interpret_command(unknown)

    def demonstrate_learning_loop(
        self,
        vendor: str,
        platform: str,
        command: str,
        context: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute and demonstrate the full two-pass learning loop.

        Pass 1: Command is unfamiliar -> AI agent interprets -> proposes mapping -> human approves.
        Pass 2: Same command encountered again -> Dev2 knowledge lookup hits immediately.
        """
        unknown = UnknownCommand(
            vendor=vendor,
            platform=platform,
            command=command,
            context=context or [],
        )

        # PASS 1: Initial encounter
        first_pass_proposal = self.teach_service.interpret_command(unknown)
        pass1_source = first_pass_proposal.source
        pass1_approval_required = first_pass_proposal.requires_human_approval
        pass1_interpretation = first_pass_proposal.interpretation

        mapping_id: Optional[str] = None
        # If backed by Dev2KnowledgeProvider, persist proposal and approve it
        if isinstance(self.knowledge_provider, Dev2KnowledgeProvider):
            dev2_prop = self.knowledge_provider.propose_mapping(pass1_interpretation)
            mapping_id = dev2_prop.id
            # Simulate human auditor reviewing and approving the proposal
            self.knowledge_provider.approve_mapping(mapping_id)
        elif isinstance(self.knowledge_provider, MockKnowledgeProvider):
            self.knowledge_provider.add_mapping(pass1_interpretation)
            mapping_id = "mock-approved-id"

        # PASS 2: Second encounter of identical command
        second_pass_proposal = self.teach_service.interpret_command(unknown)
        pass2_source = second_pass_proposal.source
        pass2_approval_required = second_pass_proposal.requires_human_approval
        pass2_interpretation = second_pass_proposal.interpretation

        return {
            "command": command,
            "vendor": vendor,
            "platform": platform,
            "pass_1": {
                "source": pass1_source,
                "requires_human_approval": pass1_approval_required,
                "interpretation": pass1_interpretation.to_dict(),
            },
            "approval_step": {
                "mapping_id": mapping_id,
                "status": "approved",
                "approved_by": "human_auditor",
            },
            "pass_2": {
                "source": pass2_source,
                "requires_human_approval": pass2_approval_required,
                "interpretation": pass2_interpretation.to_dict(),
                "knowledge_hit": (pass2_source == "knowledge_base"),
            },
        }
