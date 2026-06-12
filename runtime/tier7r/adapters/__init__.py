"""
Tier 7R adapter package — domain adapter registry and router.

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.
"""
from typing import Dict, Optional
from .cis_adapter import CISAdapter
from .swa_adapter import SWAAdapter
from ..domain_adapter import DomainAdapter

# Adapter registry — maps domain string to adapter instance
_REGISTRY: Dict[str, DomainAdapter] = {
    "CIS": CISAdapter(),
    "SWA": SWAAdapter(),
    # WIAS adapter in 7R.x+
}

# CIS domain detection keywords
CIS_DOMAIN_KEYWORDS = [
    # Archive / session recall
    "archive", "past session", "my notes", "what did i say",
    "my words", "session archive", "search my",
    # Knowledge pipeline
    "knowledge record", "knowledge pipeline", "process this",
    "into knowledge", "knowledge intake", "knowledge retrieval",
    # CIS infrastructure
    "cis build", "build_plan", "workflow_run", "orchestrator",
    "spine", "deliberation", "router",
    # Retrieval (in CIS context)
    "find everything about", "retrieve from",
    # Requirements recovery
    "requirements recovery", "what the app needs",
    "candidate requirements", "extract requirement",
    # Implementation directives (CIS context)
    "implement phase", "implement tier", "build tier",
]

# SWA domain detection keywords
SWA_DOMAIN_KEYWORDS = [
    # SWA-specific document terms
    "swa document", "swa technical", "cmamp",
    # Client / case management
    "client intake", "new client", "schedule intake",
    "schedule a crisis", "client need", "case management",
    # Appointments
    "appointment", "schedule appointment", "crisis call",
    "unlinked appointment",
    # Workflow objects
    "action_step", "action step", "client_need",
    "progress note", "d.a.p.", "treatment plan",
    "goal_id", "need_id",
    # SWA implementation
    "implement phase 45", "swa phase",
    # SWA requirements recovery
    "swa document to identify", "swa document to decide",
    "analysis of current workflow",
]


def get_adapter(domain: str) -> Optional[DomainAdapter]:
    """Return the adapter instance for a given domain, or None if not registered."""
    return _REGISTRY.get(domain)


def is_cis_domain(prompt: str) -> bool:
    """Return True if the prompt likely belongs to the CIS domain."""
    prompt_lower = prompt.lower().strip()
    return any(kw in prompt_lower for kw in CIS_DOMAIN_KEYWORDS)


def is_swa_domain(prompt: str) -> bool:
    """Return True if the prompt likely belongs to the SWA domain."""
    prompt_lower = prompt.lower().strip()
    return any(kw in prompt_lower for kw in SWA_DOMAIN_KEYWORDS)
