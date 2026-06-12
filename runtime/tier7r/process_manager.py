"""
Process Manager (state machine) for Tier 7R.4.

Consumes classified WorkIntents from domain adapters and validates
workflow state transitions per the rules defined in
docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §6.

Does NOT execute implementation work.
Does NOT bypass Eric Gate.
Determines and represents workflow state transitions.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .work_intent import WorkIntent


@dataclass
class ProcessResult:
    """Result of Process Manager validation."""
    allowed: bool
    allowed_action: str
    requires_eric_gate: bool
    reason: str
    workflow_state: Optional[str] = None
    # Additional context
    candidates_allowed: bool = True  # whether candidate staging should proceed
    details: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════
# State transition rules per spec §6.2-6.4
# ═══════════════════════════════════════════════════

# Read-only intents — always allowed, never require Eric Gate
READ_ONLY_INTENTS = {"ARCHIVE_DISCOVERY", "KNOWLEDGE_RETRIEVAL"}

# Intents that always require Eric Gate
GATED_INTENTS = {"IMPLEMENTATION_DIRECTIVE"}

# Intents that always block
BLOCKED_INTENTS = {"BLOCKED_MISSING_CAPABILITY"}

# CIS state transition rules (§6.2)
CIS_TRANSITION_RULES = [
    # (current_state, intent_class, allowed_action, requires_eric_gate, description)
    # Source manifest pipeline
    ("arrived", "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Source manifest at arrived → stage for classification"),
    ("classified", "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Source manifest classified → stage for preprocessing"),
    ("preprocessed", "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Source manifest preprocessed → stage for extraction"),
    ("extracted", "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Source manifest extracted → stage for normalization"),
    ("normalized", "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Source manifest normalized → stage for review"),
    ("draft", "KNOWLEDGE_INTAKE", "stage_candidate", True,
     "Source manifest in draft → stage for approval (Eric Gate required)"),
    ("reviewed", "KNOWLEDGE_INTAKE", "stage_candidate", True,
     "Source manifest reviewed → request approval for promotion"),
    ("approved", "KNOWLEDGE_INTAKE", "retrieve", False,
     "Source manifest approved → retrieve only (mutation requires Eric Gate)"),
    ("rejected", "KNOWLEDGE_INTAKE", "block", False,
     "Source manifest rejected → blocked"),

    # Knowledge record pipeline
    ("draft", "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Knowledge record in draft → stage for checking"),
    ("checked", "KNOWLEDGE_INTAKE", "stage_candidate", True,
     "Knowledge record checked → stage for approval (Eric Gate required)"),
    ("approved", "KNOWLEDGE_INTAKE", "retrieve", False,
     "Knowledge record approved → retrieve only"),
    ("locked", "KNOWLEDGE_INTAKE", "retrieve", False,
     "Knowledge record locked → retrieve only, no mutation"),
    ("deprecated", "KNOWLEDGE_INTAKE", "retrieve", False,
     "Knowledge record deprecated → retrieve only"),

    # Build plan node transitions
    ("PROPOSED", "REQUIREMENTS_RECOVERY", "stage_candidate", True,
     "Requirements recovery → stage build_plan_node (Eric Gate required)"),
    ("draft", "REQUIREMENTS_RECOVERY", "stage_candidate", False,
     "Requirements in draft → stage candidate for review"),
    ("PENDING", "REQUIREMENTS_RECOVERY", "stage_candidate", True,
     "Build plan node PENDING → stage for review (Eric Gate required)"),
    ("IN_PROGRESS", "REQUIREMENTS_RECOVERY", "retrieve", False,
     "Build plan node IN_PROGRESS → retrieve only"),
    ("COMPLETE", "REQUIREMENTS_RECOVERY", "retrieve", False,
     "Build plan node COMPLETE → retrieve only"),
    ("BLOCKED", "REQUIREMENTS_RECOVERY", "retrieve", False,
     "Build plan node BLOCKED → retrieve only"),
    ("DEFERRED", "REQUIREMENTS_RECOVERY", "retrieve", False,
     "Build plan node DEFERRED → retrieve only"),

    # Object does not exist (None state) → stage_candidate
    # NOTE: None-state rules must be LAST — specific states match first
    (None, "KNOWLEDGE_INTAKE", "stage_candidate", False,
     "Object does not exist → stage candidate for creation"),
    (None, "REQUIREMENTS_RECOVERY", "stage_candidate", False,
     "Object does not exist → stage candidate requirements"),
]

# SWA state transition rules (§6.4)
SWA_TRANSITION_RULES = [
    # PRE_PLAN: client doesn't exist yet
    ("PRE_PLAN", "DOMAIN_WORKFLOW_EVENT", "stage_candidate", False,
     "PRE_PLAN → stage candidate for client creation + intake scheduling"),
    ("PRE_PLAN", "REQUIREMENTS_RECOVERY", "stage_candidate", False,
     "PRE_PLAN requirements recovery → stage candidates"),

    # INTAKE: client exists, no needs
    ("INTAKE", "DOMAIN_WORKFLOW_EVENT", "stage_candidate", False,
     "Client in intake → stage candidate for needs creation"),

    # NEED_IDENTIFIED: needs exist, no goals
    ("NEED_IDENTIFIED", "DOMAIN_WORKFLOW_EVENT", "stage_candidate", False,
     "Needs identified → stage candidate for goal creation"),

    # GOAL_DEFINED: goals exist
    ("GOAL_DEFINED", "DOMAIN_WORKFLOW_EVENT", "stage_candidate", False,
     "Goals defined → stage candidate for linked action step"),

    # APPOINTMENT_UNLINKED: valid state, no forced hierarchy
    ("APPOINTMENT_UNLINKED", "DOMAIN_WORKFLOW_EVENT", "stage_candidate", False,
     "Unlinked appointment → valid state, no forced need/goal hierarchy"),

    # NOTE_GENERATED: stage for review, never auto-generate
    ("NOTE_GENERATED", "DOMAIN_WORKFLOW_EVENT", "stage_candidate", True,
     "Note generated → stage for review (Eric Gate required)"),

    # APPROVED state
    ("APPROVED", "DOMAIN_WORKFLOW_EVENT", "retrieve", False,
     "Approved records → retrieve only"),

    # Object does not exist (None state) — MUST BE LAST
    (None, "DOMAIN_WORKFLOW_EVENT", "stage_candidate", False,
     "Object does not exist, PRE_PLAN → stage candidate"),
    (None, "REQUIREMENTS_RECOVERY", "stage_candidate", False,
     "Object does not exist → stage candidate requirements"),
]


class ProcessManager:
    """
    Validates workflow state transitions for classified WorkIntents.

    Domain-neutral — uses the intent's domain to select transition rules.
    Consumes adapter output (classify_intent → validate_state → resolve_objects).
    Produces ProcessResult: allowed, allowed_action, requires_eric_gate, reason.
    """

    def __init__(self):
        self._cis_rules = CIS_TRANSITION_RULES
        self._swa_rules = SWA_TRANSITION_RULES

    def process(self, intent: WorkIntent) -> ProcessResult:
        """
        Validate the proposed transition and determine allowed action.

        Priority:
        1. BLOCKED intents → block
        2. Read-only intents → retrieve (always allowed)
        3. Gated intents → request_approval (always requires Eric Gate)
        4. Domain-specific transition rules → match by state + intent_class
        5. No rule match → block
        """
        domain = intent.domain
        intent_class = intent.intent_class or ""
        current_state = intent.workflow_state
        object_type = intent.object_type or ""

        # 1. BLOCKED intents
        if intent_class in BLOCKED_INTENTS:
            return ProcessResult(
                allowed=False,
                allowed_action="block",
                requires_eric_gate=False,
                reason=f"Intent {intent_class} is blocked — missing capability",
                workflow_state=current_state,
                candidates_allowed=False,
            )

        # 2. Read-only intents — always allowed, no mutation
        if intent_class in READ_ONLY_INTENTS:
            return ProcessResult(
                allowed=True,
                allowed_action="retrieve",
                requires_eric_gate=False,
                reason=f"Read-only intent {intent_class} — no state transition needed",
                workflow_state="N/A",
                candidates_allowed=False,  # Read-only, no candidates to stage
            )

        # 3. Gated intents — always require Eric Gate
        if intent_class in GATED_INTENTS:
            return ProcessResult(
                allowed=True,
                allowed_action="request_approval",
                requires_eric_gate=True,
                reason="IMPLEMENTATION_DIRECTIVE requires Eric Gate approval before dispatch",
                workflow_state="PENDING",
                candidates_allowed=True,
            )

        # 4. Domain-specific transition rules
        rules = self._get_rules(domain)
        for state, iclass, action, gate, desc in rules:
            # Match: (rule state is None AND intent state is None) OR exact state match
            state_match = (state is None and current_state is None) or (state == current_state)
            if state_match and iclass == intent_class:
                return ProcessResult(
                    allowed=True,
                    allowed_action=action,
                    requires_eric_gate=gate,
                    reason=desc,
                    workflow_state=current_state,
                    candidates_allowed=(action == "stage_candidate"),
                )

        # 5. No rule matched — block
        return ProcessResult(
            allowed=False,
            allowed_action="block",
            requires_eric_gate=False,
            reason=f"No valid transition found for state={current_state!r} "
                   f"intent={intent_class!r} domain={domain!r}",
            workflow_state=current_state,
            candidates_allowed=False,
        )

    def process_with_candidates(
        self, intent: WorkIntent
    ) -> tuple:
        """
        Process the intent through the state machine, then determine
        whether candidate staging should proceed.

        Returns (ProcessResult, candidates_list).
        If not allowed or candidates not allowed, returns empty list.
        """
        result = self.process(intent)

        if not result.allowed or not result.candidates_allowed:
            return result, []

        # Candidates are determined by the adapter's stage_candidates method
        # at the caller level — Process Manager only validates the transition.
        return result, []

    def _get_rules(self, domain: str) -> list:
        """Return the transition rules for the given domain."""
        if domain == "CIS":
            return self._cis_rules
        elif domain == "SWA":
            return self._swa_rules
        else:
            return []
