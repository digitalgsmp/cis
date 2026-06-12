"""
WorkIntent — Canonical data model for Tier 7R.
Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §4.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class WorkIntent:
    """Canonical interchange object for the intent-to-workflow pipeline."""

    # --- Required fields ---
    domain: str  # "CIS" | "SWA" | "WIAS" | "OUT_OF_SCOPE"

    # --- Classified fields (populated by domain adapters) ---
    intent_class: Optional[str] = None
    # One of: ARCHIVE_DISCOVERY, REQUIREMENTS_RECOVERY, KNOWLEDGE_INTAKE,
    #         KNOWLEDGE_RETRIEVAL, PROJECT_WORKFLOW_ACTION,
    #         DOMAIN_WORKFLOW_EVENT, AGENT_ADVISORY,
    #         IMPLEMENTATION_DIRECTIVE, BLOCKED_MISSING_CAPABILITY

    object_type: Optional[str] = None
    # Domain-specific object type (e.g., source_manifest, knowledge_record,
    # project, build_plan_node, workflow_run, client, appointment, etc.)

    object_refs: List[str] = field(default_factory=list)
    # Array of specific object identifiers (DB row IDs, file paths, etc.)

    workflow_state: Optional[str] = None
    # Current state of the primary object (domain-specific)

    allowed_action: Optional[str] = None
    # retrieve | stage_candidate | request_approval | dispatch | block

    # --- Evidence ---
    evidence_refs: List[str] = field(default_factory=list)
    # Source documents, session IDs, file paths, DB rows

    requires_eric_gate: bool = False

    target_project_id: Optional[str] = None

    # --- Source ---
    source_raw: Optional[str] = None
    source_type: Optional[str] = None
    # prompt | file_upload | archive_hit | system_event | document_reference

    # --- Metadata ---
    id: Optional[str] = None  # UUID
    created_at: Optional[str] = None
    status: Optional[str] = None
    # CLASSIFIED | STAGED | APPROVED | REJECTED | DISPATCHED | BLOCKED | COMPLETE

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.status is None and self.domain == "OUT_OF_SCOPE":
            self.status = "BLOCKED"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain,
            "intent_class": self.intent_class,
            "object_type": self.object_type,
            "object_refs": self.object_refs,
            "workflow_state": self.workflow_state,
            "allowed_action": self.allowed_action,
            "evidence_refs": self.evidence_refs,
            "requires_eric_gate": self.requires_eric_gate,
            "target_project_id": self.target_project_id,
            "source_raw": self.source_raw,
            "source_type": self.source_type,
            "created_at": self.created_at,
            "status": self.status,
        }
