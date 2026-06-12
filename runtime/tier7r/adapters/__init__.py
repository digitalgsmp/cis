"""
Tier 7R adapter package — domain adapter registry and router.

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.
"""
from typing import Dict, Optional
from .cis_adapter import CISAdapter
from ..domain_adapter import DomainAdapter

# Adapter registry — maps domain string to adapter instance
_REGISTRY: Dict[str, DomainAdapter] = {
    "CIS": CISAdapter(),
    # SWA and WIAS adapters in 7R.3+
}

# CIS domain detection keywords
# Used by the Content-Based Router to determine if a prompt belongs to CIS
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


def get_adapter(domain: str) -> Optional[DomainAdapter]:
    """Return the adapter instance for a given domain, or None if not registered."""
    return _REGISTRY.get(domain)


def is_cis_domain(prompt: str) -> bool:
    """Return True if the prompt likely belongs to the CIS domain."""
    prompt_lower = prompt.lower().strip()
    return any(kw in prompt_lower for kw in CIS_DOMAIN_KEYWORDS)
