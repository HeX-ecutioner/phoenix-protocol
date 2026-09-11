"""Teach-the-Auditor and AI intelligence package for Phoenix Protocol.

Exports structured data contracts, knowledge provider interfaces, ADK agents,
explanation services, remediation agents, and orchestration bridges.
"""

from app.agents.audit_bridge import AuditorLearningBridge
from app.agents.explanation import FindingExplainer
from app.agents.knowledge import (
    Dev2KnowledgeProvider,
    KnowledgeProvider,
    MockKnowledgeProvider,
)
from app.agents.orchestrator import PhoenixAuditorOrchestrator
from app.agents.remediation import (
    RemediationService,
    build_remediation_agent,
    heuristic_remediation_generator,
)
from app.agents.schemas import (
    KNOWN_PHOENIX_RULES,
    CommandInterpretation,
    FindingExplanation,
    RemediationSuggestion,
    TeachingProposal,
    UnknownCommand,
)
from app.agents.teach_auditor import (
    TEACH_AUDITOR_INSTRUCTION,
    TeachAuditorService,
    build_teach_auditor_agent,
    heuristic_fallback_interpreter,
    make_lookup_tool,
)

__all__ = [
    "KNOWN_PHOENIX_RULES",
    "UnknownCommand",
    "CommandInterpretation",
    "TeachingProposal",
    "RemediationSuggestion",
    "FindingExplanation",
    "KnowledgeProvider",
    "MockKnowledgeProvider",
    "Dev2KnowledgeProvider",
    "TeachAuditorService",
    "build_teach_auditor_agent",
    "make_lookup_tool",
    "heuristic_fallback_interpreter",
    "TEACH_AUDITOR_INSTRUCTION",
    "RemediationService",
    "build_remediation_agent",
    "heuristic_remediation_generator",
    "FindingExplainer",
    "AuditorLearningBridge",
    "PhoenixAuditorOrchestrator",
]

