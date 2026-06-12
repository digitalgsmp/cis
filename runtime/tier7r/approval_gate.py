"""
Human Approval Gate for Tier 7R.5.

Intercepts Process Manager results that require Eric Gate approval
and blocks dispatch until explicit human approval is recorded.

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §7.

Principle: "Every promotion gate requires human approval; AI proposes only."
Eric remains the final authority. Approval state is explicit, inspectable,
and testable.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from .process_manager import ProcessResult
from .work_intent import WorkIntent


@dataclass
class ApprovalDecision:
    """Result of human approval gate check."""
    allowed: bool
    status: str  # APPROVED | REJECTED | AWAITING_APPROVAL | NOT_GATED
    reason: str
    requires_eric_gate: bool = False
    intent_id: Optional[str] = None


class ApprovalGate:
    """
    Human approval gate — blocks gated transitions until approved.

    Integrates with Process Manager:
    - ProcessResult.requires_eric_gate → check gate
    - If gated → AWAITING_APPROVAL (blocked)
    - After approve() → ALLOWED
    - reject() → REJECTED

    Approval registry is in-memory for 7R.5 scope.
    Production would use Eric Gate infrastructure (Component 3).
    """

    def __init__(self):
        # In-memory approval registry: intent_id → approval status
        self._registry: Dict[str, str] = {}  # APPROVED or REJECTED
        self._rejection_reasons: Dict[str, str] = {}
        self._counter = 0

    def check(self, result: ProcessResult, intent: Optional[WorkIntent] = None) -> ApprovalDecision:
        """
        Check whether a transition requires human approval.

        If not gated → NOT_GATED (proceed normally).
        If gated and already approved → APPROVED (proceed).
        If gated and not yet approved → AWAITING_APPROVAL (blocked).
        If gated and rejected → REJECTED (blocked permanently).
        """
        if not result.requires_eric_gate:
            return ApprovalDecision(
                allowed=True,
                status="NOT_GATED",
                reason="No Eric Gate required for this transition",
                requires_eric_gate=False,
            )

        # Gated — check registry
        intent_id = intent.id if intent else None

        if intent_id and intent_id in self._rejection_reasons:
            return ApprovalDecision(
                allowed=False,
                status="REJECTED",
                reason=self._rejection_reasons[intent_id],
                requires_eric_gate=True,
                intent_id=intent_id,
            )

        if intent_id and self._registry.get(intent_id) == "APPROVED":
            return ApprovalDecision(
                allowed=True,
                status="APPROVED",
                reason="Eric Gate approval recorded — transition allowed",
                requires_eric_gate=True,
                intent_id=intent_id,
            )

        # Gated, not yet decided → awaiting
        return ApprovalDecision(
            allowed=False,
            status="AWAITING_APPROVAL",
            reason="Eric Gate approval required before this transition can proceed",
            requires_eric_gate=True,
            intent_id=intent_id,
        )

    def approve(self, intent_id: str) -> ApprovalDecision:
        """
        Record Eric's approval for a gated transition.

        Returns ApprovalDecision with status=APPROVED.
        """
        self._registry[intent_id] = "APPROVED"
        self._rejection_reasons.pop(intent_id, None)
        return ApprovalDecision(
            allowed=True,
            status="APPROVED",
            reason=f"Intent {intent_id}: Eric Gate approved",
            requires_eric_gate=True,
            intent_id=intent_id,
        )

    def reject(self, intent_id: str, reason: str = "Rejected by Eric Gate") -> ApprovalDecision:
        """
        Record Eric's rejection for a gated transition.

        Returns ApprovalDecision with status=REJECTED.
        """
        self._registry.pop(intent_id, None)
        self._rejection_reasons[intent_id] = reason
        return ApprovalDecision(
            allowed=False,
            status="REJECTED",
            reason=f"Intent {intent_id}: {reason}",
            requires_eric_gate=True,
            intent_id=intent_id,
        )

    def is_approved(self, intent_id: str) -> bool:
        """Return True if intent has been approved."""
        return self._registry.get(intent_id) == "APPROVED"

    def is_rejected(self, intent_id: str) -> bool:
        """Return True if intent has been rejected."""
        return intent_id in self._rejection_reasons

    def pending_count(self) -> int:
        """Return number of intents awaiting approval (gated but not decided)."""
        # This is conceptual — in 7R.5 we track via the pipeline,
        # not by counting un-decided intents in the registry
        return 0

    def assigned_id(self) -> str:
        """Assign a new intent ID for gate tracking."""
        self._counter += 1
        return f"gate-{self._counter}"


# ═══════════════════════════════════════════════════
# Pipeline integration helpers
# ═══════════════════════════════════════════════════

def process_with_approval(
    intent: WorkIntent,
    pm_result: ProcessResult,
    gate: ApprovalGate,
) -> tuple:
    """
    Full approval-gated pipeline step.

    Returns (decision, candidates) where:
    - decision: ApprovalDecision
    - candidates: list of WorkIntent (empty if blocked or awaiting approval)

    Steps:
    1. Check gate
    2. If NOT_GATED or APPROVED → return candidates (delegated to caller)
    3. If AWAITING_APPROVAL or REJECTED → return empty candidates

    The caller is responsible for staging candidates when the gate allows.
    """
    # Assign an ID for gate tracking if not already assigned
    if intent.id is None:
        intent.id = gate.assigned_id()

    decision = gate.check(pm_result, intent)

    if decision.allowed:
        return decision, True  # candidates_allowed
    else:
        return decision, False  # blocked — awaiting or rejected
