"""
CISAdapter — CIS domain adapter for Tier 7R.2.

Classifies CIS-domain WorkIntents per the rules defined in
docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.3.

Rules:
  C1 — KNOWLEDGE_INTAKE + file evidence → object_type=source_manifest,
        allowed_action=stage_candidate
  C2 — ARCHIVE_DISCOVERY → intent_class=ARCHIVE_DISCOVERY,
        allowed_action=retrieve (no mutation)
  C3 — REQUIREMENTS_RECOVERY → stage build_plan_nodes with status=PROPOSED
  C4 — IMPLEMENTATION_DIRECTIVE → requires_eric_gate=true,
        allowed_action=request_approval
  C5 — Unrecognized within CIS domain → allowed_action=block, status=BLOCKED
  C6 — KNOWLEDGE_RETRIEVAL → allowed_action=retrieve, routes to Research
"""
from typing import List
from ..domain_adapter import DomainAdapter
from ..work_intent import WorkIntent


class CISAdapter(DomainAdapter):
    """CIS domain adapter — classifies CIS intents only."""

    domain = "CIS"

    # Keyword sets for intent classification (ordered, first match wins)
    ARCHIVE_KEYWORDS = [
        "what did i say", "past session", "my notes",
        "my words", "session archive", "search my notes",
        "search my sessions", "archive search",
    ]

    INTAKE_KEYWORDS = [
        "process this pdf", "process this file", "into a knowledge record",
        "knowledge intake", "into knowledge", "as a knowledge record",
        "add to knowledge", "ingest", "import into",
    ]

    RETRIEVAL_KEYWORDS = [
        "find everything about", "find all", "retrieve knowledge",
        "knowledge retrieval", "search knowledge", "search records",
        "look up", "query the",
    ]

    RECOVERY_KEYWORDS = [
        "requirements recovery", "candidate requirements",
        "extract requirement", "identify what the app needs",
        "what does the app need", "recover requirements",
        "use this document to", "analyze this document for",
    ]

    IMPLEMENT_KEYWORDS = [
        "implement phase", "implement tier", "build phase",
        "build tier", "execute tier", "execute phase",
    ]

    def classify_intent(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Classify intent_class, object_type, object_refs from source_raw.

        First-match priority: ARCHIVE > INTAKE > RETRIEVAL > RECOVERY > IMPLEMENT > BLOCKED.
        """
        prompt_lower = work_intent.source_raw.lower().strip() if work_intent.source_raw else ""

        if any(kw in prompt_lower for kw in self.ARCHIVE_KEYWORDS):
            work_intent.intent_class = "ARCHIVE_DISCOVERY"
            work_intent.object_type = "session_record"
            work_intent.allowed_action = "retrieve"
            work_intent.requires_eric_gate = False
            work_intent.status = "CLASSIFIED"

        elif any(kw in prompt_lower for kw in self.INTAKE_KEYWORDS):
            work_intent.intent_class = "KNOWLEDGE_INTAKE"
            work_intent.object_type = "source_manifest"
            work_intent.allowed_action = "stage_candidate"
            work_intent.requires_eric_gate = False
            work_intent.status = "CLASSIFIED"
            # If evidence path is in source_raw, add to object_refs
            if work_intent.evidence_refs:
                work_intent.object_refs = list(work_intent.evidence_refs)

        elif any(kw in prompt_lower for kw in self.RETRIEVAL_KEYWORDS):
            work_intent.intent_class = "KNOWLEDGE_RETRIEVAL"
            work_intent.allowed_action = "retrieve"
            work_intent.requires_eric_gate = False
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
            # C5: Unrecognized within CIS domain → block
            work_intent.intent_class = "BLOCKED_MISSING_CAPABILITY"
            work_intent.allowed_action = "block"
            work_intent.status = "BLOCKED"

        return work_intent

    def validate_state(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Check spine for current object state and set workflow_state.

        Per §6.3 allowed action determination:
        - ARCHIVE_DISCOVERY + KNOWLEDGE_RETRIEVAL → read-only, workflow_state=N/A
        - KNOWLEDGE_INTAKE → object doesn't exist yet → workflow_state=arrived
        - REQUIREMENTS_RECOVERY → draft → workflow_state=draft
        - IMPLEMENTATION_DIRECTIVE → workflow_state=PENDING
        """
        intent_class = work_intent.intent_class

        if intent_class in ("ARCHIVE_DISCOVERY", "KNOWLEDGE_RETRIEVAL"):
            work_intent.workflow_state = "N/A"
            # Read-only operations — no mutation allowed
            work_intent.allowed_action = "retrieve"

        elif intent_class == "KNOWLEDGE_INTAKE":
            work_intent.workflow_state = "arrived"
            work_intent.allowed_action = "stage_candidate"

        elif intent_class == "REQUIREMENTS_RECOVERY":
            work_intent.workflow_state = "draft"
            work_intent.allowed_action = "stage_candidate"

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
        Resolve object_refs from spine. Verify objects exist and are accessible.

        For 7R.2: minimal implementation — verifies that object_refs are not empty
        for intents that require them. Full spine query in 7R.4 (Process Manager).
        """
        if work_intent.intent_class in ("BLOCKED_MISSING_CAPABILITY",):
            return work_intent

        # KNOWLEDGE_INTAKE: if no file evidence was provided, note but don't block
        # (the user might provide file path later)
        if work_intent.intent_class == "KNOWLEDGE_INTAKE":
            if not work_intent.object_refs and work_intent.evidence_refs:
                work_intent.object_refs = list(work_intent.evidence_refs)

        # ARCHIVE_DISCOVERY and KNOWLEDGE_RETRIEVAL: no specific object required
        # REQUIREMENTS_RECOVERY: may not have object_refs until document is analyzed

        return work_intent

    def stage_candidates(self, work_intent: WorkIntent) -> List[WorkIntent]:
        """
        Generate candidate WorkIntents for Eric review.

        NEVER mutates spine directly. All candidates are proposals.

        Per §5.3:
        - KNOWLEDGE_INTAKE → stage source_manifest + knowledge_record candidates
        - REQUIREMENTS_RECOVERY → stage build_plan_node candidates
        - IMPLEMENTATION_DIRECTIVE → stage for Eric Gate approval
        - ARCHIVE_DISCOVERY / KNOWLEDGE_RETRIEVAL → no candidates (read-only)
        """
        candidates: List[WorkIntent] = []

        if work_intent.intent_class == "KNOWLEDGE_INTAKE":
            # C1: Stage source_manifest + knowledge_record pipeline entries
            sm = WorkIntent(
                domain="CIS",
                intent_class="KNOWLEDGE_INTAKE",
                object_type="source_manifest",
                workflow_state="arrived",
                allowed_action="stage_candidate",
                status="STAGED",
                requires_eric_gate=False,
                source_raw=work_intent.source_raw,
                object_refs=list(work_intent.object_refs),
                evidence_refs=list(work_intent.evidence_refs),
            )
            kr = WorkIntent(
                domain="CIS",
                intent_class="KNOWLEDGE_INTAKE",
                object_type="knowledge_record",
                workflow_state="draft",
                allowed_action="stage_candidate",
                status="STAGED",
                requires_eric_gate=False,
                source_raw=work_intent.source_raw,
            )
            candidates.extend([sm, kr])

        elif work_intent.intent_class == "REQUIREMENTS_RECOVERY":
            # C3: Stage build_plan_node candidates
            # The actual candidates are derived from the document analysis —
            # for now, stage a single requirements recovery entry.
            candidate = WorkIntent(
                domain="CIS",
                intent_class="REQUIREMENTS_RECOVERY",
                object_type="build_plan_node",
                workflow_state="draft",
                allowed_action="stage_candidate",
                status="STAGED",
                requires_eric_gate=True,
                source_raw=work_intent.source_raw,
            )
            candidates.append(candidate)

        elif work_intent.intent_class == "IMPLEMENTATION_DIRECTIVE":
            # C4: Stage for Eric Gate — must be approved before dispatch
            candidate = WorkIntent(
                domain="CIS",
                intent_class="IMPLEMENTATION_DIRECTIVE",
                object_type="build_plan_node",
                workflow_state="PENDING",
                allowed_action="request_approval",
                status="STAGED",
                requires_eric_gate=True,
                source_raw=work_intent.source_raw,
            )
            candidates.append(candidate)

        # ARCHIVE_DISCOVERY and KNOWLEDGE_RETRIEVAL produce no candidates
        # They are read-only operations — no staging needed

        return candidates
