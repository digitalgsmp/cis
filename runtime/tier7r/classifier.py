"""
Classifier for Tier 7R — domain classification and adapter routing.

7R.1: Minimal classifier — only rejects Micro1 as OUT_OF_SCOPE.
7R.2: Adds CIS domain detection and routes through CISAdapter.

classify() preserves 7R.1 behavior (backward compatible).
classify_full() runs the complete 7R.2 pipeline: domain → adapter → state → objects → candidates.
"""
from .scope_registry import classify_domain, Domain, is_out_of_scope, is_in_scope
from .work_intent import WorkIntent
from .adapters import get_adapter, is_cis_domain
from typing import List, Optional


def classify(prompt: str, source_type: str = "prompt") -> WorkIntent:
    """
    Minimal classifier — 7R.1 scope only. Backward compatible.

    Currently handles:
    - OUT_OF_SCOPE rejection (Micro1)
    - Unclassified passthrough

    For full CIS classification, use classify_full().
    """
    domain = classify_domain(prompt)

    intent = WorkIntent(
        domain=domain if domain else "",
        source_raw=prompt,
        source_type=source_type,
    )

    if is_out_of_scope(domain):
        intent.intent_class = "BLOCKED_MISSING_CAPABILITY"
        intent.allowed_action = "block"
        intent.status = "BLOCKED"

    return intent


def classify_domain_router(prompt: str) -> str:
    """
    Content-Based Router — determine which domain a prompt belongs to.

    7R.2: Detects CIS domain via keyword matching.
    Falls back to empty string (unclassified) for non-CIS, non-Micro1 prompts.
    Micro1 is still rejected as OUT_OF_SCOPE.

    Returns: "CIS" | "OUT_OF_SCOPE" | ""
    """
    # First check out-of-scope (Micro1)
    domain = classify_domain(prompt)
    if is_out_of_scope(domain):
        return Domain.OUT_OF_SCOPE.value

    # Check CIS domain via keyword matching
    if is_cis_domain(prompt):
        return Domain.CIS.value

    # Unclassified — no adapter available yet
    return ""


def classify_full(
    prompt: str,
    source_type: str = "prompt",
    evidence_refs: Optional[List[str]] = None,
) -> WorkIntent:
    """
    Full 7R.2 pipeline: domain classification → adapter classification → validate → resolve.

    Steps:
    1. classify_domain_router() — determine domain
    2. If CIS → route to CISAdapter.classify_intent()
    3. CISAdapter.validate_state()
    4. CISAdapter.resolve_objects()
    5. Return classified WorkIntent

    Returns the fully classified WorkIntent. Candidates are NOT staged here —
    that happens at the Process Manager level (7R.4).
    """
    domain = classify_domain_router(prompt)

    intent = WorkIntent(
        domain=domain if domain else "",
        source_raw=prompt,
        source_type=source_type,
        evidence_refs=evidence_refs or [],
    )

    if is_out_of_scope(domain):
        intent.intent_class = "BLOCKED_MISSING_CAPABILITY"
        intent.allowed_action = "block"
        intent.status = "BLOCKED"
        return intent

    if not domain:
        # Unclassified — no adapter available
        return intent

    # Route to domain adapter
    adapter = get_adapter(domain)
    if adapter is None:
        intent.intent_class = "BLOCKED_MISSING_CAPABILITY"
        intent.allowed_action = "block"
        intent.status = "BLOCKED"
        return intent

    # Run adapter pipeline: classify → validate → resolve
    intent = adapter.classify_intent(intent)
    intent = adapter.validate_state(intent)
    intent = adapter.resolve_objects(intent)

    return intent


def classify_with_candidates(
    prompt: str,
    source_type: str = "prompt",
    evidence_refs: Optional[List[str]] = None,
) -> tuple:
    """
    Full classification + candidate staging.

    Returns (work_intent, candidates) where candidates is a list of
    staged WorkIntents for Eric review.
    """
    intent = classify_full(prompt, source_type, evidence_refs)

    domain = intent.domain
    if not domain or intent.status == "BLOCKED":
        return intent, []

    adapter = get_adapter(domain)
    if adapter is None:
        return intent, []

    candidates = adapter.stage_candidates(intent)
    return intent, candidates
