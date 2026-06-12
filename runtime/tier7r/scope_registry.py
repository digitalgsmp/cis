"""
Scope registry for Tier 7R.
Defines in-scope and out-of-scope domains.
Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §3.
"""
from enum import Enum
from typing import Dict, List


class Domain(str, Enum):
    CIS = "CIS"
    SWA = "SWA"
    WIAS = "WIAS"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


# In-scope domains with descriptions
IN_SCOPE: Dict[str, str] = {
    Domain.CIS: "CIS infrastructure / archive / knowledge workflow",
    Domain.SWA: "SWA case-management workflow (validation use case only)",
    Domain.WIAS: "WIAS creative project workflow (per CIS roadmap Phases 3-5)",
}

# Out-of-scope domains — rejected at classification
OUT_OF_SCOPE_LIST: List[str] = [
    "Micro1",  # Accidental context contamination — belongs to another person
]

# Keywords that should trigger OUT_OF_SCOPE classification
OUT_OF_SCOPE_KEYWORDS: Dict[str, str] = {
    "micro1": "Accidental context contamination — belongs to another person. Removed from scope.",
}


def classify_domain(prompt: str) -> str:
    """
    Classify a raw prompt into a domain.
    Currently only rejects known out-of-scope domains.
    Full classification is in 7R.2+ (domain adapters).
    """
    prompt_lower = prompt.lower().strip()

    # Check out-of-scope keywords
    for keyword, reason in OUT_OF_SCOPE_KEYWORDS.items():
        if keyword in prompt_lower:
            return Domain.OUT_OF_SCOPE.value

    # Default: no classifier implemented yet (7R.2+)
    return ""  # Unclassified — domain adapters will handle


def is_out_of_scope(domain: str) -> bool:
    """Return True if the domain is explicitly out of scope."""
    return domain == Domain.OUT_OF_SCOPE.value


def is_in_scope(domain: str) -> bool:
    """Return True if the domain is in the scope registry."""
    return domain in IN_SCOPE
