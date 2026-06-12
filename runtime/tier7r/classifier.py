"""
Basic classifier for Tier 7R.1.
Only rejects Micro1 as OUT_OF_SCOPE.
Full intent classification is deferred to 7R.2+.
"""
from .scope_registry import classify_domain, Domain, is_out_of_scope
from .work_intent import WorkIntent


def classify(prompt: str, source_type: str = "prompt") -> WorkIntent:
    """
    Minimal classifier — 7R.1 scope only.

    Currently handles:
    - OUT_OF_SCOPE rejection (Micro1)
    - Unclassified passthrough (domain adapters in 7R.2+)

    Does NOT classify CIS, SWA, or WIAS intents — deferred to 7R.2+.
    """
    domain = classify_domain(prompt)

    intent = WorkIntent(
        domain=domain if domain else "",  # empty = unclassified
        source_raw=prompt,
        source_type=source_type,
    )

    if is_out_of_scope(domain):
        intent.intent_class = "BLOCKED_MISSING_CAPABILITY"
        intent.allowed_action = "block"
        intent.status = "BLOCKED"

    return intent
