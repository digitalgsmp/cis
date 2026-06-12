"""
7R.3 acceptance tests — SWAAdapter (validation use case).

Tests the SWA domain adapter as a validation use case for the
DomainAdapter contract. Verifies SWA handles a second domain without
changing the CISAdapter interface.

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.4 and §8.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.adapters import get_adapter, is_swa_domain, SWA_DOMAIN_KEYWORDS
from runtime.tier7r.adapters.swa_adapter import SWAAdapter
from runtime.tier7r.classifier import (
    classify,
    classify_domain_router,
    classify_full,
    classify_with_candidates,
)


# ═══════════════════════════════════════════════════
# 7R.1 + 7R.2 back-compat tests
# ═══════════════════════════════════════════════════

def test_7r1_classify_still_works():
    """classify() still rejects Micro1 (unchanged)."""
    wi = classify("Start Micro1 task planning")
    assert wi.domain == "OUT_OF_SCOPE"
    assert wi.status == "BLOCKED"


def test_7r2_classify_full_cis_still_works():
    """classify_full() still routes CIS prompts to CISAdapter."""
    wi = classify_full("What did I say about the social worker app in past sessions?")
    assert wi.domain == "CIS"
    assert wi.intent_class == "ARCHIVE_DISCOVERY"


# ═══════════════════════════════════════════════════
# SWAAdapter existence + contract
# ═══════════════════════════════════════════════════

def test_swa_adapter_exists():
    """SWAAdapter is registered and instantiable."""
    adapter = get_adapter("SWA")
    assert adapter is not None
    assert isinstance(adapter, SWAAdapter)
    assert adapter.domain == "SWA"


def test_swa_adapter_implements_all_methods():
    """SWAAdapter implements all DomainAdapter abstract methods."""
    adapter = get_adapter("SWA")
    assert hasattr(adapter, "classify_intent")
    assert hasattr(adapter, "validate_state")
    assert hasattr(adapter, "resolve_objects")
    assert hasattr(adapter, "stage_candidates")
    assert callable(adapter.classify_intent)
    assert callable(adapter.validate_state)
    assert callable(adapter.resolve_objects)
    assert callable(adapter.stage_candidates)


def test_cis_adapter_still_registered():
    """CISAdapter is still registered after adding SWAAdapter."""
    assert get_adapter("CIS") is not None
    assert get_adapter("SWA") is not None
    assert get_adapter("CIS").domain == "CIS"
    assert get_adapter("SWA").domain == "SWA"


# ═══════════════════════════════════════════════════
# Domain Router tests (SWA detection)
# ═══════════════════════════════════════════════════

def test_router_swa_detected_workflow():
    """SWA workflow event prompts detected."""
    assert classify_domain_router("Schedule intake for new client") == "SWA"


def test_router_swa_detected_document():
    """SWA document analysis prompts detected."""
    assert classify_domain_router(
        "Use this SWA document to identify what the app needs"
    ) == "SWA"


def test_router_swa_detected_crisis():
    """SWA crisis call prompts detected."""
    assert classify_domain_router(
        "Schedule a crisis call with client — no formal goal exists yet"
    ) == "SWA"


def test_router_swa_detected_implement():
    """SWA implementation directive detected (spec §8.6)."""
    # "Implement Phase 45" — per spec §8.6, this is SWA domain
    assert classify_domain_router("Implement Phase 45") == "SWA"


def test_router_swa_takes_priority():
    """SWA keywords take priority over CIS for SWA-specific prompts."""
    # "client intake" is SWA-specific, should route to SWA even though
    # "process this" is a CIS keyword
    result = classify_domain_router("Process this client intake form")
    assert result == "SWA"


def test_router_cis_still_works():
    """CIS prompts without SWA keywords still route to CIS."""
    result = classify_domain_router("What did I say about the social worker app?")
    assert result == "CIS"


def test_router_micro1_still_rejected():
    """Micro1 is still OUT_OF_SCOPE ahead of SWA."""
    assert classify_domain_router("Start Micro1 task planning for SWA") == "OUT_OF_SCOPE"


# ═══════════════════════════════════════════════════
# SWAAdapter.classify_intent tests
# ═══════════════════════════════════════════════════

def _mk_swa_intent(prompt: str) -> WorkIntent:
    """Create a WorkIntent for SWA adapter testing."""
    return WorkIntent(domain="SWA", source_raw=prompt, source_type="prompt")


def test_classify_domain_workflow_event():
    """DOMAIN_WORKFLOW_EVENT detected for SWA workflow prompts."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("Schedule intake for new client")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "DOMAIN_WORKFLOW_EVENT"
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False
    assert result.status == "CLASSIFIED"


def test_classify_workflow_detects_client():
    """Client object detected in workflow event."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("new client intake scheduled")
    result = adapter.classify_intent(wi)
    assert result.object_type == "client"
    assert "client" in result.object_refs


def test_classify_workflow_detects_appointment():
    """Appointment object detected in workflow event."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("schedule appointment with client")
    result = adapter.classify_intent(wi)
    assert "appointment" in result.object_refs


def test_classify_workflow_detects_progress_note():
    """Progress note object detected."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("Generate D.A.P. progress note for client")
    result = adapter.classify_intent(wi)
    assert "progress_note" in result.object_refs
    assert result.workflow_state == "NOTE_GENERATED"


def test_classify_requirements_recovery():
    """SWA document → REQUIREMENTS_RECOVERY."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("Use this SWA Technical Overview to identify what the app needs")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "REQUIREMENTS_RECOVERY"
    assert result.object_type == "build_plan_node"
    assert result.allowed_action == "stage_candidate"
    assert result.status == "CLASSIFIED"


def test_classify_pre_plan_state():
    """PRE_PLAN workflow state detected from keywords."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("Pre treatment plan documentation needed — first 30 days")
    result = adapter.classify_intent(wi)
    assert result.workflow_state == "PRE_PLAN"


def test_classify_unlinked_appointment():
    """APPOINTMENT_UNLINKED state detected."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("unlinked appointment for client")
    result = adapter.classify_intent(wi)
    assert result.workflow_state == "APPOINTMENT_UNLINKED"


def test_classify_unrecognized_blocked():
    """Unrecognized SWA prompt → BLOCKED."""
    adapter = get_adapter("SWA")
    wi = _mk_swa_intent("something random in swa domain")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "BLOCKED_MISSING_CAPABILITY"
    assert result.allowed_action == "block"
    assert result.status == "BLOCKED"


# ═══════════════════════════════════════════════════
# SWAAdapter.validate_state tests
# ═══════════════════════════════════════════════════

def test_validate_pre_plan():
    """PRE_PLAN → stage_candidate, eric_gate=false (S2)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="PRE_PLAN",
    )
    result = adapter.validate_state(wi)
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_validate_unlinked_appointment():
    """APPOINTMENT_UNLINKED → valid state, no forced hierarchy (S3)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="APPOINTMENT_UNLINKED",
    )
    result = adapter.validate_state(wi)
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_validate_note_generated():
    """NOTE_GENERATED → stage for review, never auto-generate (S4)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="NOTE_GENERATED",
    )
    result = adapter.validate_state(wi)
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == True


def test_validate_requirements_recovery():
    """REQUIREMENTS_RECOVERY → workflow_state=PRE_PLAN (S5)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="REQUIREMENTS_RECOVERY",
    )
    result = adapter.validate_state(wi)
    assert result.workflow_state == "PRE_PLAN"
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_validate_implementation_directive():
    """IMPLEMENTATION_DIRECTIVE → PENDING, eric_gate=true."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="IMPLEMENTATION_DIRECTIVE",
    )
    result = adapter.validate_state(wi)
    assert result.workflow_state == "PENDING"
    assert result.allowed_action == "request_approval"
    assert result.requires_eric_gate == True


def test_validate_blocked():
    """BLOCKED → no mutation."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="BLOCKED_MISSING_CAPABILITY",
        status="BLOCKED",
    )
    result = adapter.validate_state(wi)
    assert result.allowed_action == "block"
    assert result.status == "BLOCKED"


# ═══════════════════════════════════════════════════
# SWAAdapter.stage_candidates tests
# ═══════════════════════════════════════════════════

def test_stage_pre_plan():
    """Stage client candidate for PRE_PLAN workflow state."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="PRE_PLAN",
        source_raw="Schedule intake for new client",
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 1
    assert candidates[0].object_type == "client"
    assert candidates[0].workflow_state == "PRE_PLAN"
    assert candidates[0].status == "STAGED"
    assert candidates[0].requires_eric_gate == False


def test_stage_unlinked_appointment():
    """Stage appointment candidate for APPOINTMENT_UNLINKED (S3)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="APPOINTMENT_UNLINKED",
        source_raw="Schedule crisis call — no goal exists",
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 1
    assert candidates[0].object_type == "appointment"
    assert candidates[0].workflow_state == "APPOINTMENT_UNLINKED"
    assert candidates[0].status == "STAGED"
    assert candidates[0].requires_eric_gate == False


def test_stage_note_generated():
    """Stage progress_note for review (S4)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="NOTE_GENERATED",
        source_raw="Generate D.A.P. progress note",
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 1
    assert candidates[0].object_type == "progress_note"
    assert candidates[0].status == "STAGED"
    assert candidates[0].requires_eric_gate == True


def test_stage_requirements_recovery():
    """Stage 4 build_plan_node candidates for REQUIREMENTS_RECOVERY (S5)."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="REQUIREMENTS_RECOVERY",
        source_raw="SWA document analysis",
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 4  # per §8.1
    for c in candidates:
        assert c.object_type == "build_plan_node"
        assert c.status == "STAGED"
        assert c.requires_eric_gate == True


def test_stage_candidates_never_return_none():
    """All staging paths return a list (never None)."""
    adapter = get_adapter("SWA")
    for intent_class in ["DOMAIN_WORKFLOW_EVENT", "REQUIREMENTS_RECOVERY"]:
        wi = WorkIntent(domain="SWA", intent_class=intent_class)
        result = adapter.stage_candidates(wi)
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════
# classify_full pipeline tests (SWA)
# ═══════════════════════════════════════════════════

def test_full_swa_workflow_event():
    """classify_full() → SWA workflow event pipeline."""
    wi = classify_full("Schedule intake for new client")
    assert wi.domain == "SWA"
    assert wi.intent_class == "DOMAIN_WORKFLOW_EVENT"
    assert wi.status == "CLASSIFIED"


def test_full_swa_crisis_call():
    """classify_full() → SWA crisis/unlinked appointment."""
    wi = classify_full(
        "Schedule a crisis call with client — no formal goal exists yet"
    )
    assert wi.domain == "SWA"
    assert wi.intent_class == "DOMAIN_WORKFLOW_EVENT"
    assert wi.workflow_state == "APPOINTMENT_UNLINKED"


def test_full_swa_document_analysis():
    """classify_full() → SWA requirements recovery."""
    wi = classify_full("Use this SWA document to identify what the app needs")
    assert wi.domain == "SWA"
    assert wi.intent_class == "REQUIREMENTS_RECOVERY"
    assert wi.object_type == "build_plan_node"


# ═══════════════════════════════════════════════════
# classify_with_candidates tests (SWA)
# ═══════════════════════════════════════════════════

def test_with_candidates_swa_workflow():
    """classify_with_candidates() → SWA workflow stages candidate."""
    intent, candidates = classify_with_candidates("Schedule intake for new client")
    assert intent.domain == "SWA"
    assert len(candidates) == 1
    assert all(c.status == "STAGED" for c in candidates)


def test_with_candidates_swa_recovery():
    """classify_with_candidates() → 4 candidates for requirements recovery."""
    intent, candidates = classify_with_candidates(
        "Use this SWA document to identify what the app needs"
    )
    assert intent.intent_class == "REQUIREMENTS_RECOVERY"
    assert len(candidates) == 4


# ═══════════════════════════════════════════════════
# Spec acceptance tests (from docs §8)
# ═══════════════════════════════════════════════════

def test_spec_8_1_swa_phase_45():
    """
    §8.1: SWA Phase 45 — Flexible Documentation Workflow

    Expected:
      domain: SWA
      intent_class: REQUIREMENTS_RECOVERY
      object_type: build_plan_node
      workflow_state: PRE_PLAN
      allowed_action: stage_candidate
      requires_eric_gate: false
      4 staged candidates
    """
    intent, candidates = classify_with_candidates(
        "Use this SWA Technical Overview to identify what the app needs"
    )
    assert intent.domain == "SWA"
    assert intent.intent_class == "REQUIREMENTS_RECOVERY"
    assert intent.object_type == "build_plan_node"
    assert intent.allowed_action == "stage_candidate"
    assert intent.requires_eric_gate == False

    # 4 candidate build_plan_nodes per spec
    assert len(candidates) == 4
    for c in candidates:
        assert c.domain == "SWA"
        assert c.object_type == "build_plan_node"
        assert c.status == "STAGED"


def test_spec_8_2_unlinked_appointment():
    """
    §8.2: SWA Unlinked Appointment

    Input: "Schedule a crisis call with client — no formal goal exists yet"
    Expected:
      domain: SWA
      intent_class: DOMAIN_WORKFLOW_EVENT
      object_type: [client, appointment]
      workflow_state: APPOINTMENT_UNLINKED
      allowed_action: stage_candidate
      requires_eric_gate: false
    """
    intent, candidates = classify_with_candidates(
        "Schedule a crisis call with client — no formal goal exists yet"
    )
    assert intent.domain == "SWA"
    assert intent.intent_class == "DOMAIN_WORKFLOW_EVENT"
    assert "client" in intent.object_refs or intent.object_type == "client"
    assert "appointment" in intent.object_refs
    assert intent.workflow_state == "APPOINTMENT_UNLINKED"
    assert intent.allowed_action == "stage_candidate"
    assert intent.requires_eric_gate == False

    # Only 1 candidate (appointment), not a full build plan
    assert len(candidates) == 1
    assert candidates[0].status == "STAGED"


# ═══════════════════════════════════════════════════
# Scope boundary tests — SWA as validation use case only
# ═══════════════════════════════════════════════════

def test_no_swa_codebase_touch():
    """SWAAdapter does not reference the SWA project filesystem."""
    import importlib
    for module_name in [
        "runtime.tier7r.adapters.swa_adapter",
        "runtime.tier7r.adapters",
        "runtime.tier7r.classifier",
    ]:
        mod = importlib.import_module(module_name)
        src = str(getattr(mod, "__file__", ""))
        with open(src) as f:
            content = f.read()
        assert "/mnt/projects/swa/" not in content, \
            f"{module_name} references SWA codebase at /mnt/projects/swa/"


def test_no_swa_spine_mutation():
    """SWAAdapter.stage_candidates() returns candidates, no side effects."""
    adapter = get_adapter("SWA")
    wi = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="PRE_PLAN", source_raw="test",
    )
    # Run staging twice — no state mutation
    c1 = adapter.stage_candidates(wi)
    c2 = adapter.stage_candidates(wi)
    assert len(c1) == len(c2)
    # Each call returns fresh objects
    assert c1[0] is not c2[0]


def test_cis_adapter_unchanged():
    """CISAdapter contract unchanged by SWAAdapter addition."""
    from runtime.tier7r.adapters.cis_adapter import CISAdapter
    # Verify CISAdapter still has the same methods
    cis = get_adapter("CIS")
    assert cis.domain == "CIS"
    assert isinstance(cis, CISAdapter)
    # Run a CIS classification to verify
    wi = classify_full("Process this PDF into a knowledge record")
    assert wi.domain == "CIS"
    assert wi.intent_class == "KNOWLEDGE_INTAKE"


def test_swa_keywords_populated():
    """SWA_DOMAIN_KEYWORDS list is populated."""
    assert len(SWA_DOMAIN_KEYWORDS) > 0


def test_micro1_not_swa():
    """Micro1 is never classified as SWA."""
    assert not is_swa_domain("Start Micro1 task planning")


# ═══════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # 7R.1/7R.2 back-compat
        ("7R.1 classify() still works", test_7r1_classify_still_works),
        ("7R.2 classify_full CIS still works", test_7r2_classify_full_cis_still_works),
        # SWAAdapter existence
        ("SWAAdapter: registered + instantiable", test_swa_adapter_exists),
        ("SWAAdapter: implements all methods", test_swa_adapter_implements_all_methods),
        ("Registry: both CIS and SWA registered", test_cis_adapter_still_registered),
        # Domain Router
        ("Router: SWA detected (workflow)", test_router_swa_detected_workflow),
        ("Router: SWA detected (document)", test_router_swa_detected_document),
        ("Router: SWA detected (crisis)", test_router_swa_detected_crisis),
        ("Router: SWA implement", test_router_swa_detected_implement),
        ("Router: SWA priority over CIS", test_router_swa_takes_priority),
        ("Router: CIS still works", test_router_cis_still_works),
        ("Router: Micro1 still rejected", test_router_micro1_still_rejected),
        # classify_intent
        ("Classify: DOMAIN_WORKFLOW_EVENT", test_classify_domain_workflow_event),
        ("Classify: client object", test_classify_workflow_detects_client),
        ("Classify: appointment object", test_classify_workflow_detects_appointment),
        ("Classify: progress_note object", test_classify_workflow_detects_progress_note),
        ("Classify: REQUIREMENTS_RECOVERY", test_classify_requirements_recovery),
        ("Classify: PRE_PLAN state", test_classify_pre_plan_state),
        ("Classify: APPOINTMENT_UNLINKED", test_classify_unlinked_appointment),
        ("Classify: unrecognized → BLOCKED", test_classify_unrecognized_blocked),
        # validate_state
        ("Validate: PRE_PLAN (S2)", test_validate_pre_plan),
        ("Validate: APPOINTMENT_UNLINKED (S3)", test_validate_unlinked_appointment),
        ("Validate: NOTE_GENERATED (S4)", test_validate_note_generated),
        ("Validate: REQUIREMENTS_RECOVERY (S5)", test_validate_requirements_recovery),
        ("Validate: IMPLEMENTATION → PENDING", test_validate_implementation_directive),
        ("Validate: BLOCKED → block", test_validate_blocked),
        # stage_candidates
        ("Stage: PRE_PLAN", test_stage_pre_plan),
        ("Stage: APPOINTMENT_UNLINKED", test_stage_unlinked_appointment),
        ("Stage: NOTE_GENERATED", test_stage_note_generated),
        ("Stage: REQUIREMENTS_RECOVERY → 4", test_stage_requirements_recovery),
        ("Stage: never returns None", test_stage_candidates_never_return_none),
        # classify_full pipeline
        ("Full: SWA workflow event", test_full_swa_workflow_event),
        ("Full: SWA crisis call", test_full_swa_crisis_call),
        ("Full: SWA document analysis", test_full_swa_document_analysis),
        # classify_with_candidates
        ("Candidates: SWA workflow", test_with_candidates_swa_workflow),
        ("Candidates: SWA recovery → 4", test_with_candidates_swa_recovery),
        # Spec acceptance tests
        ("Spec §8.1: SWA Phase 45", test_spec_8_1_swa_phase_45),
        ("Spec §8.2: Unlinked appointment", test_spec_8_2_unlinked_appointment),
        # Scope boundary
        ("Scope: no SWA codebase touch", test_no_swa_codebase_touch),
        ("Scope: no SWA spine mutation", test_no_swa_spine_mutation),
        ("Scope: CISAdapter unchanged", test_cis_adapter_unchanged),
        ("Scope: SWA keywords populated", test_swa_keywords_populated),
        ("Scope: Micro1 not in SWA", test_micro1_not_swa),
    ]

    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
        except AssertionError as e:
            print(f"  FAIL: {name} — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {name} — {e}")
            failed += 1

    print(f"\n{failed} failures out of {len(tests)} tests")
    sys.exit(1 if failed else 0)
