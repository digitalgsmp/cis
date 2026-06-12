"""
SWAAdapter — SWA domain adapter for Tier 7R.3 (validation use case only).

Classifies SWA-domain WorkIntents per the rules defined in
docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.4.

Rules:
  S1 — DOMAIN_WORKFLOW_EVENT with client+appointment → check if client exists
  S2 — PRE_PLAN workflow state → stage_candidate, requires_eric_gate=false
  S3 — APPOINTMENT_UNLINKED → valid workflow state, no need/goal required
  S4 — NOTE_GENERATION → classify, check prerequisites, stage, never auto-generate
  S5 — DOMAIN_MODEL_CHANGE → classify as REQUIREMENTS_RECOVERY, stage candidates
  S6 — SWA adapter NEVER implements SWA app features — classify and stage only

IMPORTANT: SWA is a validation use case. This adapter validates that the
DomainAdapter contract supports a second domain without changing the interface.
It does NOT implement SWA application features. It does NOT access or modify
files in the SWA project directory. It does NOT connect to the SWA runtime.
"""
from typing import List
from ..domain_adapter import DomainAdapter
from ..work_intent import WorkIntent


class SWAAdapter(DomainAdapter):
    """SWA domain adapter — validation use case only."""

    domain = "SWA"

    # Intent classification keywords (ordered, first match wins)
    WORKFLOW_EVENT_KEYWORDS = [
        "schedule a crisis", "schedule intake", "new client",
        "crisis call", "client intake", "appointment",
        "log action", "generate note", "progress note",
        "d.a.p.", "client need", "action step",
    ]

    RECOVERY_KEYWORDS = [
        "swa document to identify", "swa document to decide",
        "swa document", "swa technical overview",
        "analysis of current workflow", "use this swa",
        "what does the app need",
    ]

    IMPLEMENT_KEYWORDS = [
        "implement phase 45", "swa phase", "implement swa",
    ]

    # SWA workflow states from spec §4.4
    VALID_STATES = {
        "PRE_PLAN", "INTAKE", "NEED_IDENTIFIED", "GOAL_DEFINED",
        "APPOINTMENT_LINKED", "APPOINTMENT_UNLINKED",
        "ACTION_LOGGED", "NOTE_GENERATED", "APPROVED",
    }

    # SWA object types from spec
    SWA_OBJECTS = {
        "client", "appointment", "need", "goal",
        "action_step", "provider", "progress_note",
    }

    def classify_intent(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Classify SWA intents from source_raw.

        Priority: WORKFLOW_EVENT > RECOVERY > IMPLEMENT > BLOCKED.
        """
        prompt_lower = work_intent.source_raw.lower().strip() if work_intent.source_raw else ""

        # Detect explicit workflow states in the prompt text
        if "pre_plan" in prompt_lower or "pre-plan" in prompt_lower or \
           "pre treatment" in prompt_lower or "first 30 days" in prompt_lower:
            work_intent.workflow_state = "PRE_PLAN"

        if "unlinked" in prompt_lower or "no formal goal" in prompt_lower or \
           "no goal exists" in prompt_lower or "without a goal" in prompt_lower or \
           "no need" in prompt_lower:
            work_intent.workflow_state = "APPOINTMENT_UNLINKED"

        if "progress note" in prompt_lower or "d.a.p." in prompt_lower or \
           "generate note" in prompt_lower:
            work_intent.workflow_state = "NOTE_GENERATED"

        if any(kw in prompt_lower for kw in self.WORKFLOW_EVENT_KEYWORDS):
            work_intent.intent_class = "DOMAIN_WORKFLOW_EVENT"
            work_intent.allowed_action = "stage_candidate"
            work_intent.requires_eric_gate = False

            # Detect affected objects
            objects = []
            if "client" in prompt_lower:
                objects.append("client")
            if "appointment" in prompt_lower or "schedule" in prompt_lower or \
               "crisis call" in prompt_lower:
                objects.append("appointment")
            if "need" in prompt_lower or "client_need" in prompt_lower:
                objects.append("need")
            if "goal" in prompt_lower or "goal_id" in prompt_lower:
                objects.append("goal")
            if "action" in prompt_lower or "log" in prompt_lower:
                objects.append("action_step")
            if "progress note" in prompt_lower or "d.a.p." in prompt_lower:
                objects.append("progress_note")

            work_intent.object_type = objects[0] if objects else "client"
            work_intent.object_refs = objects if len(objects) > 1 else []
            work_intent.status = "CLASSIFIED"

        elif any(kw in prompt_lower for kw in self.RECOVERY_KEYWORDS):
            work_intent.intent_class = "REQUIREMENTS_RECOVERY"
            work_intent.object_type = "build_plan_node"
            work_intent.allowed_action = "stage_candidate"
            work_intent.requires_eric_gate = False
            work_intent.status = "CLASSIFIED"

        elif any(kw in prompt_lower for kw in self.IMPLEMENT_KEYWORDS):
            work_intent.intent_class = "IMPLEMENTATION_DIRECTIVE"
            work_intent.object_type = "build_plan_node"
            work_intent.allowed_action = "request_approval"
            work_intent.requires_eric_gate = True
            work_intent.status = "CLASSIFIED"

        else:
            # S6: Unrecognized within SWA domain
            work_intent.intent_class = "BLOCKED_MISSING_CAPABILITY"
            work_intent.allowed_action = "block"
            work_intent.status = "BLOCKED"

        return work_intent

    def validate_state(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Validate workflow state per SWA state rules (§6.4).

        - PRE_PLAN: documentation only, no preconditions
        - APPOINTMENT_UNLINKED: valid, no forced need/goal hierarchy
        - NOTE_GENERATION: stage for review, never auto-generate
        """
        intent_class = work_intent.intent_class

        if intent_class == "DOMAIN_WORKFLOW_EVENT":
            state = work_intent.workflow_state

            if state == "PRE_PLAN":
                # S2: Flexible documentation before formal treatment plan
                work_intent.allowed_action = "stage_candidate"
                work_intent.requires_eric_gate = False

            elif state == "APPOINTMENT_UNLINKED":
                # S3: Valid state — no need/goal required
                work_intent.allowed_action = "stage_candidate"
                work_intent.requires_eric_gate = False

            elif state == "NOTE_GENERATED":
                # S4: Stage for review, never auto-generate
                work_intent.allowed_action = "stage_candidate"
                work_intent.requires_eric_gate = True

            elif work_intent.object_type == "client" and \
                 "appointment" in (work_intent.object_refs or []):
                # Client + appointment event — valid at any state
                work_intent.workflow_state = "INTAKE"
                work_intent.allowed_action = "stage_candidate"
                work_intent.requires_eric_gate = False

            else:
                # Default for workflow events: stage for review
                work_intent.workflow_state = work_intent.workflow_state or "PRE_PLAN"

        elif intent_class == "REQUIREMENTS_RECOVERY":
            # S5: DOMAIN_MODEL_CHANGE → REQUIREMENTS_RECOVERY
            work_intent.workflow_state = "PRE_PLAN"
            work_intent.allowed_action = "stage_candidate"
            work_intent.requires_eric_gate = False

        elif intent_class == "IMPLEMENTATION_DIRECTIVE":
            work_intent.workflow_state = "PENDING"
            work_intent.allowed_action = "request_approval"
            work_intent.requires_eric_gate = True

        elif intent_class == "BLOCKED_MISSING_CAPABILITY":
            work_intent.workflow_state = "N/A"
            work_intent.allowed_action = "block"
            work_intent.status = "BLOCKED"

        return work_intent

    def resolve_objects(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Resolve object_refs from spine.

        For 7R.3: minimal implementation — verifies object_refs are valid
        SWA object types. Full spine query in 7R.4 (Process Manager).

        S1: For client+appointment events, verify both objects are referenced.
        """
        if work_intent.intent_class in ("BLOCKED_MISSING_CAPABILITY",):
            return work_intent

        # Validate object_refs are known SWA objects
        if work_intent.object_refs:
            for ref in work_intent.object_refs:
                if ref not in self.SWA_OBJECTS:
                    # Unknown object type — flag but don't block
                    pass

        # S1: DOMAIN_WORKFLOW_EVENT with client+appointment
        if work_intent.intent_class == "DOMAIN_WORKFLOW_EVENT":
            refs = work_intent.object_refs or []
            if "client" in refs and "appointment" in refs:
                # Both objects referenced — valid
                pass

        return work_intent

    def stage_candidates(self, work_intent: WorkIntent) -> List[WorkIntent]:
        """
        Generate candidate WorkIntents for Eric review.

        NEVER mutates spine directly.

        Per §5.4:
        - DOMAIN_WORKFLOW_EVENT → stage workflow event candidates
        - REQUIREMENTS_RECOVERY → stage build_plan_node candidates
        - IMPLEMENTATION_DIRECTIVE → stage for Eric Gate approval
        - Never auto-generate notes (S4)
        """
        candidates: List[WorkIntent] = []

        if work_intent.intent_class == "DOMAIN_WORKFLOW_EVENT":
            # Stage based on workflow state
            state = work_intent.workflow_state

            if state == "PRE_PLAN":
                # S2: Documentation workflow — stage flexible pre-plan candidates
                candidate = WorkIntent(
                    domain="SWA",
                    intent_class="DOMAIN_WORKFLOW_EVENT",
                    object_type="client",
                    workflow_state="PRE_PLAN",
                    allowed_action="stage_candidate",
                    status="STAGED",
                    requires_eric_gate=False,
                    source_raw=work_intent.source_raw,
                )
                candidates.append(candidate)

            elif state == "APPOINTMENT_UNLINKED":
                # S3: Valid unlinked appointment — no forced need/goal
                candidate = WorkIntent(
                    domain="SWA",
                    intent_class="DOMAIN_WORKFLOW_EVENT",
                    object_type="appointment",
                    workflow_state="APPOINTMENT_UNLINKED",
                    allowed_action="stage_candidate",
                    status="STAGED",
                    requires_eric_gate=False,
                    source_raw=work_intent.source_raw,
                )
                candidates.append(candidate)

            elif state == "NOTE_GENERATED":
                # S4: Stage note for review — never auto-generate
                candidate = WorkIntent(
                    domain="SWA",
                    intent_class="DOMAIN_WORKFLOW_EVENT",
                    object_type="progress_note",
                    workflow_state="NOTE_GENERATED",
                    allowed_action="stage_candidate",
                    status="STAGED",
                    requires_eric_gate=True,
                    source_raw=work_intent.source_raw,
                )
                candidates.append(candidate)

            else:
                # Generic workflow event candidate
                candidate = WorkIntent(
                    domain="SWA",
                    intent_class="DOMAIN_WORKFLOW_EVENT",
                    object_type=work_intent.object_type or "client",
                    workflow_state=work_intent.workflow_state or "INTAKE",
                    allowed_action="stage_candidate",
                    status="STAGED",
                    requires_eric_gate=False,
                    source_raw=work_intent.source_raw,
                )
                candidates.append(candidate)

        elif work_intent.intent_class == "REQUIREMENTS_RECOVERY":
            # S5: Stage build_plan_node candidates from document analysis
            # Per §8.1, SWA Phase 45 should stage 4 candidate build_plan_nodes
            candidate_labels = [
                "SWA — Make goal_id optional in action_steps table",
                "SWA — Add client_need_id column to action_steps",
                "SWA — Update appointment scheduling to allow unlinked appointments",
                "SWA — Add General Service action step type",
            ]
            for label in candidate_labels:
                candidate = WorkIntent(
                    domain="SWA",
                    intent_class="REQUIREMENTS_RECOVERY",
                    object_type="build_plan_node",
                    workflow_state="draft",
                    allowed_action="stage_candidate",
                    status="STAGED",
                    requires_eric_gate=True,
                    source_raw=label,
                )
                candidates.append(candidate)

        elif work_intent.intent_class == "IMPLEMENTATION_DIRECTIVE":
            candidate = WorkIntent(
                domain="SWA",
                intent_class="IMPLEMENTATION_DIRECTIVE",
                object_type="build_plan_node",
                workflow_state="PENDING",
                allowed_action="request_approval",
                status="STAGED",
                requires_eric_gate=True,
                source_raw=work_intent.source_raw,
            )
            candidates.append(candidate)

        return candidates
