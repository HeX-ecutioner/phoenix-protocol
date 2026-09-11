"""Teach-the-Auditor agentic package for Phoenix Protocol.

Exports structured data contracts, knowledge provider interfaces, and the ADK
Teach-the-Auditor agent service.
"""

from app.agents.knowledge import KnowledgeProvider, MockKnowledgeProvider
from app.agents.schemas import (
    KNOWN_PHOENIX_RULES,
    CommandInterpretation,
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
    "KnowledgeProvider",
    "MockKnowledgeProvider",
    "TeachAuditorService",
    "build_teach_auditor_agent",
    "make_lookup_tool",
    "heuristic_fallback_interpreter",
    "TEACH_AUDITOR_INSTRUCTION",
]
