"""
Dead Letter / Blocked Handling for Tier 7R.6.

Captures blocked WorkIntents that cannot safely advance through the pipeline.
Records category, reason, source, and timestamp for each blocked intent.

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §2.1 and §11.4.

Categories:
- OUT_OF_SCOPE: Domain explicitly excluded (Micro1)
- UNSUPPORTED_DOMAIN: No domain adapter available
- INVALID_TRANSITION: Process Manager blocked the transition
- REJECTED_BY_GATE: Eric Gate rejected the intent
- AWAITING_APPROVAL: Gated, but not yet approved/rejected
- MISSING_CAPABILITY: Required capability not available (BLOCKED_MISSING_CAPABILITY)
- UNRECOGNIZED: Unclassified prompt with no domain match

Does NOT auto-recover or re-route blocked intents.
Recovery is a future explicit action.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from .work_intent import WorkIntent
from .process_manager import ProcessResult
from .approval_gate import ApprovalDecision


class BlockCategory(str, Enum):
    """Categories of blocked/dead-letter states."""
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNSUPPORTED_DOMAIN = "UNSUPPORTED_DOMAIN"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    REJECTED_BY_GATE = "REJECTED_BY_GATE"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    UNRECOGNIZED = "UNRECOGNIZED"


@dataclass
class BlockRecord:
    """A single dead-letter entry."""
    intent_id: str
    category: BlockCategory
    reason: str
    source: str  # which pipeline component triggered the block
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    domain: str = ""
    intent_class: str = ""
    source_raw: str = ""

    def to_dict(self) -> dict:
        return {
            "intent_id": self.intent_id,
            "category": self.category.value if isinstance(self.category, BlockCategory) else self.category,
            "reason": self.reason,
            "source": self.source,
            "timestamp": self.timestamp,
            "domain": self.domain,
            "intent_class": self.intent_class,
            "source_raw": self.source_raw,
        }


class DeadLetterRegistry:
    """
    Central registry for blocked/dead-letter intents.

    Stores blocked intents with category, reason, source, and timestamp.
    Provides inspection and dismissal. Does NOT auto-recover.

    In-memory for 7R.6 scope. Production would persist to SQLite spine.
    """

    def __init__(self):
        self._entries: List[BlockRecord] = []
        self._by_id: Dict[str, BlockRecord] = {}
        self._counter = 0

    def record(
        self,
        intent: WorkIntent,
        category: BlockCategory,
        reason: str,
        source: str = "pipeline",
    ) -> BlockRecord:
        """Record a blocked intent in the dead-letter registry."""
        intent_id = intent.id or f"dl-{self._counter}"
        self._counter += 1

        record = BlockRecord(
            intent_id=intent_id,
            category=category,
            reason=reason,
            source=source,
            domain=intent.domain or "",
            intent_class=intent.intent_class or "",
            source_raw=intent.source_raw or "",
        )
        self._entries.append(record)
        self._by_id[intent_id] = record
        return record

    def record_from_pm(self, intent: WorkIntent, pm_result: ProcessResult) -> BlockRecord:
        """Record a block from the Process Manager."""
        category = BlockCategory.INVALID_TRANSITION
        if pm_result.allowed_action == "block":
            return self.record(intent, category, pm_result.reason, "process_manager")
        return self.record(intent, category, "Blocked by Process Manager", "process_manager")

    def record_from_gate(self, intent: WorkIntent, decision: ApprovalDecision) -> Optional[BlockRecord]:
        """Record a block from the Approval Gate (only if rejected, not awaiting)."""
        if decision.status == "REJECTED":
            return self.record(intent, BlockCategory.REJECTED_BY_GATE,
                               decision.reason, "approval_gate")
        elif decision.status == "AWAITING_APPROVAL":
            return self.record(intent, BlockCategory.AWAITING_APPROVAL,
                               decision.reason, "approval_gate")
        return None

    def record_out_of_scope(self, intent: WorkIntent, reason: str = "") -> BlockRecord:
        """Record an out-of-scope intent."""
        return self.record(intent, BlockCategory.OUT_OF_SCOPE,
                           reason or "Domain explicitly excluded from scope",
                           "scope_registry")

    def record_unsupported_domain(self, intent: WorkIntent) -> BlockRecord:
        """Record an intent with no domain adapter available."""
        return self.record(intent, BlockCategory.UNSUPPORTED_DOMAIN,
                           f"No adapter for domain: {intent.domain or '(unrecognized)'}",
                           "domain_router")

    def record_unrecognized(self, intent: WorkIntent) -> BlockRecord:
        """Record an unclassified intent."""
        return self.record(intent, BlockCategory.UNRECOGNIZED,
                           "No domain matched — unclassified prompt",
                           "domain_router")

    # ── Query methods ──

    def get_all(self) -> List[BlockRecord]:
        """Return all dead-letter entries."""
        return list(self._entries)

    def get_by_category(self, category: BlockCategory) -> List[BlockRecord]:
        """Return entries for a specific category."""
        return [e for e in self._entries if e.category == category]

    def get_by_id(self, intent_id: str) -> Optional[BlockRecord]:
        """Return a specific entry by intent ID."""
        return self._by_id.get(intent_id)

    def count(self) -> int:
        """Return total blocked entries."""
        return len(self._entries)

    def count_by_category(self, category: BlockCategory) -> int:
        """Return count of entries for a specific category."""
        return len(self.get_by_category(category))

    def categories_present(self) -> List[str]:
        """Return list of categories that have at least one entry."""
        seen = set()
        for e in self._entries:
            seen.add(e.category.value if isinstance(e.category, BlockCategory) else e.category)
        return sorted(seen)

    # ── Dismissal ──

    def dismiss(self, intent_id: str) -> bool:
        """Remove an entry from the dead-letter registry (acknowledged)."""
        if intent_id in self._by_id:
            entry = self._by_id.pop(intent_id)
            self._entries.remove(entry)
            return True
        return False

    def dismiss_by_category(self, category: BlockCategory) -> int:
        """Remove all entries for a category. Returns count removed."""
        to_remove = self.get_by_category(category)
        for entry in to_remove:
            self._by_id.pop(entry.intent_id, None)
            self._entries.remove(entry)
        return len(to_remove)

    def clear(self) -> int:
        """Clear all entries. Returns count removed."""
        count = len(self._entries)
        self._entries.clear()
        self._by_id.clear()
        return count


# ═══════════════════════════════════════════════════
# Pipeline integration
# ═══════════════════════════════════════════════════

def handle_blocked_result(
    intent: WorkIntent,
    pm_result: ProcessResult,
    gate_decision: Optional[ApprovalDecision] = None,
    registry: Optional[DeadLetterRegistry] = None,
) -> Optional[BlockRecord]:
    """
    Determine if a pipeline result should go to dead-letter and record it.

    Priority: intent status > gate_decision > pm_result.

    Returns the BlockRecord if recorded, else None.
    """
    if registry is None:
        return None

    # Intent-level blocked status (highest priority — captures domain/router-level blocks)
    if intent.status == "BLOCKED":
        if intent.intent_class == "BLOCKED_MISSING_CAPABILITY":
            return registry.record(intent, BlockCategory.MISSING_CAPABILITY,
                                   intent.source_raw or "Missing capability",
                                   "classifier")
        return registry.record(intent, BlockCategory.INVALID_TRANSITION,
                               f"Intent blocked: {intent.intent_class}",
                               "classifier")

    # No domain — unrecognized
    if not intent.domain:
        return registry.record_unrecognized(intent)

    # Gate rejection
    if gate_decision is not None and gate_decision.status == "REJECTED":
        return registry.record_from_gate(intent, gate_decision)

    # Gate awaiting approval
    if gate_decision is not None and gate_decision.status == "AWAITING_APPROVAL":
        return registry.record_from_gate(intent, gate_decision)

    # Process Manager blocked
    if not pm_result.allowed:
        return registry.record_from_pm(intent, pm_result)

    return None
