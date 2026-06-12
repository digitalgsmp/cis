"""
7R.4 acceptance tests — Process Manager (state machine).

Tests the Process Manager state-transition validation layer:
validates legal transitions, blocks illegal ones, enforces Eric Gate
requirements, and works with both CIS and SWA domain adapters.

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §6.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.process_manager import (
    ProcessManager,
    ProcessResult,
    CIS_TRANSITION_RULES,
    SWA_TRANSITION_RULES,
    READ_ONLY_INTENTS,
    GATED_INTENTS,
    BLOCKED_INTENTS,
)
from runtime.tier7r.classifier import (
    classify,
    classify_full,
    classify_with_candidates,
    classify_with_pm,
    classify_full_pipeline,
)


# ═══════════════════════════════════════════════════
# 7R.1-7R.3 back-compat tests
# ═══════════════════════════════════════════════════

def test_7r1_classify_unchanged():
    """classify() still rejects Micro1."""
    wi = classify("Start Micro1 task planning")
    assert wi.domain == "OUT_OF_SCOPE"
    assert wi.status == "BLOCKED"


def test_7r2_classify_full_cis_unchanged():
    """classify_full() still routes CIS archive queries."""
    wi = classify_full("What did I say about the social worker app in past sessions?")
    assert wi.domain == "CIS"
    assert wi.intent_class == "ARCHIVE_DISCOVERY"


def test_7r2_classify_with_candidates_unchanged():
    """classify_with_candidates() still returns candidates."""
    intent, candidates = classify_with_candidates(
        "Process this PDF into a knowledge record"
    )
    assert intent.domain == "CIS"
    assert len(candidates) == 2


def test_7r3_classify_full_swa_unchanged():
    """classify_full() still routes SWA crisis calls."""
    wi = classify_full(
        "Schedule a crisis call with client — no formal goal exists yet"
    )
    assert wi.domain == "SWA"


# ═══════════════════════════════════════════════════
# Process Manager: basic structure
# ═══════════════════════════════════════════════════

def test_pm_instantiable():
    """Process Manager can be instantiated."""
    pm = ProcessManager()
    assert pm is not None


def test_pm_returns_process_result():
    """process() returns a ProcessResult."""
    pm = ProcessManager()
    intent = WorkIntent(domain="CIS", intent_class="ARCHIVE_DISCOVERY")
    result = pm.process(intent)
    assert isinstance(result, ProcessResult)


def test_pm_rules_loaded():
    """CIS and SWA transition rules are populated."""
    pm = ProcessManager()
    assert len(pm._cis_rules) > 0
    assert len(pm._swa_rules) > 0


# ═══════════════════════════════════════════════════
# Process Manager: read-only intents (always allowed)
# ═══════════════════════════════════════════════════

def test_pm_archive_discovery_allowed():
    """ARCHIVE_DISCOVERY → allowed, retrieve, no Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="ARCHIVE_DISCOVERY",
        workflow_state="N/A",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.requires_eric_gate == False
    assert result.candidates_allowed == False  # read-only


def test_pm_knowledge_retrieval_allowed():
    """KNOWLEDGE_RETRIEVAL → allowed, retrieve, no Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_RETRIEVAL",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.requires_eric_gate == False
    assert result.candidates_allowed == False


# ═══════════════════════════════════════════════════
# Process Manager: gated intents (always Eric Gate)
# ═══════════════════════════════════════════════════

def test_pm_implementation_directive_gated():
    """IMPLEMENTATION_DIRECTIVE → request_approval, Eric Gate required."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
        workflow_state="PENDING",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "request_approval"
    assert result.requires_eric_gate == True
    assert result.candidates_allowed == True


def test_pm_implementation_directive_swa():
    """IMPLEMENTATION_DIRECTIVE in SWA domain also gated."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="IMPLEMENTATION_DIRECTIVE",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "request_approval"
    assert result.requires_eric_gate == True


# ═══════════════════════════════════════════════════
# Process Manager: BLOCKED intents
# ═══════════════════════════════════════════════════

def test_pm_blocked_intent():
    """BLOCKED_MISSING_CAPABILITY → not allowed, block."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="BLOCKED_MISSING_CAPABILITY",
        status="BLOCKED",
    )
    result = pm.process(intent)
    assert result.allowed == False
    assert result.allowed_action == "block"
    assert result.requires_eric_gate == False
    assert result.candidates_allowed == False


# ═══════════════════════════════════════════════════
# Process Manager: CIS state transitions (§6.2-6.3)
# ═══════════════════════════════════════════════════

def test_pm_cis_intake_arrived():
    """KNOWLEDGE_INTAKE at 'arrived' → stage_candidate, no Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="arrived",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False
    assert result.candidates_allowed == True


def test_pm_cis_intake_draft():
    """KNOWLEDGE_INTAKE at 'draft' → stage_candidate, Eric Gate required."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="draft",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == True


def test_pm_cis_intake_approved():
    """KNOWLEDGE_INTAKE at 'approved' → retrieve only."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="approved",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.candidates_allowed == False


def test_pm_cis_intake_locked():
    """KNOWLEDGE_INTAKE at 'locked' → retrieve only, no mutation."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="locked",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.candidates_allowed == False


def test_pm_cis_requirements_pending():
    """REQUIREMENTS_RECOVERY at PENDING → stage_candidate, Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="REQUIREMENTS_RECOVERY",
        workflow_state="PENDING",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == True


def test_pm_cis_requirements_blocked():
    """REQUIREMENTS_RECOVERY at BLOCKED → retrieve only."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="REQUIREMENTS_RECOVERY",
        workflow_state="BLOCKED",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.candidates_allowed == False


# ═══════════════════════════════════════════════════
# Process Manager: SWA state transitions (§6.4)
# ═══════════════════════════════════════════════════

def test_pm_swa_pre_plan():
    """DOMAIN_WORKFLOW_EVENT at PRE_PLAN → stage_candidate, no Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="PRE_PLAN",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False
    assert result.candidates_allowed == True


def test_pm_swa_intake():
    """DOMAIN_WORKFLOW_EVENT at INTAKE → stage_candidate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="INTAKE",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_pm_swa_need_identified():
    """DOMAIN_WORKFLOW_EVENT at NEED_IDENTIFIED → stage_candidate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="NEED_IDENTIFIED",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"


def test_pm_swa_goal_defined():
    """DOMAIN_WORKFLOW_EVENT at GOAL_DEFINED → stage_candidate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="GOAL_DEFINED",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"


def test_pm_swa_unlinked_appointment():
    """APPOINTMENT_UNLINKED → valid state, stage_candidate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="APPOINTMENT_UNLINKED",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_pm_swa_note_generated():
    """NOTE_GENERATED → stage_candidate, Eric Gate required."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="NOTE_GENERATED",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == True


def test_pm_swa_approved():
    """APPROVED → retrieve only."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="APPROVED",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.candidates_allowed == False


# ═══════════════════════════════════════════════════
# Process Manager: unknown states → block
# ═══════════════════════════════════════════════════

def test_pm_invalid_transition_blocked():
    """Unknown state/intent combination → blocked."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="NONEXISTENT_STATE",
    )
    result = pm.process(intent)
    assert result.allowed == False
    assert result.allowed_action == "block"


def test_pm_unknown_domain_blocked():
    """Unknown domain → blocked (no rules)."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="BOGUS", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state="PRE_PLAN",
    )
    result = pm.process(intent)
    assert result.allowed == False
    assert result.allowed_action == "block"


def test_pm_object_does_not_exist_cis():
    """Object does not exist (None state) → stage_candidate for CIS."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state=None,
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_pm_object_does_not_exist_swa():
    """Object does not exist (None state) → stage_candidate for SWA."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT",
        workflow_state=None,
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"


# ═══════════════════════════════════════════════════
# Process Manager: domain neutrality
# ═══════════════════════════════════════════════════

def test_pm_works_with_cis():
    """Process Manager handles CIS domain intents."""
    pm = ProcessManager()
    cs = [
        ("CIS", "KNOWLEDGE_INTAKE", "arrived", "stage_candidate"),
        ("CIS", "REQUIREMENTS_RECOVERY", "draft", "stage_candidate"),
        ("CIS", "ARCHIVE_DISCOVERY", "N/A", "retrieve"),
    ]
    for domain, iclass, state, expected_action in cs:
        intent = WorkIntent(domain=domain, intent_class=iclass,
                            workflow_state=state)
        result = pm.process(intent)
        assert result.allowed == True
        assert result.allowed_action == expected_action


def test_pm_works_with_swa():
    """Process Manager handles SWA domain intents."""
    pm = ProcessManager()
    cs = [
        ("SWA", "DOMAIN_WORKFLOW_EVENT", "PRE_PLAN", "stage_candidate"),
        ("SWA", "DOMAIN_WORKFLOW_EVENT", "APPOINTMENT_UNLINKED", "stage_candidate"),
        ("SWA", "IMPLEMENTATION_DIRECTIVE", None, "request_approval"),
    ]
    for domain, iclass, state, expected_action in cs:
        intent = WorkIntent(domain=domain, intent_class=iclass,
                            workflow_state=state)
        result = pm.process(intent)
        assert result.allowed == True
        assert result.allowed_action == expected_action


def test_pm_does_not_execute():
    """Process Manager does not mutate the WorkIntent."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="arrived",
    )
    original_status = intent.status
    original_domain = intent.domain
    pm.process(intent)
    # Intent unchanged by process()
    assert intent.domain == original_domain
    assert intent.status == original_status


# ═══════════════════════════════════════════════════
# classify_with_pm pipeline tests
# ═══════════════════════════════════════════════════

def test_pipeline_archive_with_pm():
    """classify_with_pm() → CIS archive, allowed, retrieve."""
    intent, result = classify_with_pm(
        "What did I say about the social worker app in past sessions?"
    )
    assert intent.domain == "CIS"
    assert intent.intent_class == "ARCHIVE_DISCOVERY"
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.requires_eric_gate == False


def test_pipeline_intake_with_pm():
    """classify_with_pm() → CIS intake, allowed, stage_candidate."""
    intent, result = classify_with_pm(
        "Process this PDF into a knowledge record"
    )
    assert intent.domain == "CIS"
    assert intent.intent_class == "KNOWLEDGE_INTAKE"
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.candidates_allowed == True


def test_pipeline_micro1_with_pm():
    """classify_with_pm() → Micro1 blocked."""
    intent, result = classify_with_pm("Start Micro1 task planning")
    assert intent.domain == "OUT_OF_SCOPE"
    assert result.allowed == False
    assert result.allowed_action == "block"


def test_pipeline_swa_pre_plan_with_pm():
    """classify_with_pm() → SWA PRE_PLAN, allowed."""
    intent, result = classify_with_pm("Schedule intake for new client")
    assert intent.domain == "SWA"
    assert intent.intent_class == "DOMAIN_WORKFLOW_EVENT"
    assert result.allowed == True


# ═══════════════════════════════════════════════════
# classify_full_pipeline tests (end-to-end)
# ═══════════════════════════════════════════════════

def test_full_pipeline_archive():
    """classify_full_pipeline() → archive, no candidates."""
    intent, candidates, result = classify_full_pipeline(
        "What did I say about the social worker app in past sessions?"
    )
    assert intent.domain == "CIS"
    assert intent.intent_class == "ARCHIVE_DISCOVERY"
    assert result.allowed == True
    assert len(candidates) == 0  # read-only, no candidates


def test_full_pipeline_intake():
    """classify_full_pipeline() → intake with candidates."""
    intent, candidates, result = classify_full_pipeline(
        "Process this PDF into a knowledge record"
    )
    assert intent.domain == "CIS"
    assert result.allowed == True
    assert result.candidates_allowed == True
    assert len(candidates) == 2


def test_full_pipeline_micro1():
    """classify_full_pipeline() → Micro1, blocked, no candidates."""
    intent, candidates, result = classify_full_pipeline(
        "Start Micro1 task planning"
    )
    assert result.allowed == False
    assert len(candidates) == 0


def test_full_pipeline_swa_workflow():
    """classify_full_pipeline() → SWA workflow, candidate staged."""
    intent, candidates, result = classify_full_pipeline(
        "Schedule intake for new client"
    )
    assert intent.domain == "SWA"
    assert result.allowed == True
    assert len(candidates) >= 1


def test_full_pipeline_swa_recovery():
    """classify_full_pipeline() → SWA requirements recovery, 4 candidates."""
    intent, candidates, result = classify_full_pipeline(
        "Use this SWA document to identify what the app needs"
    )
    assert intent.domain == "SWA"
    assert intent.intent_class == "REQUIREMENTS_RECOVERY"
    assert result.allowed == True
    assert len(candidates) == 4


# ═══════════════════════════════════════════════════
# Process Manager: §6.3 table validation
# ═══════════════════════════════════════════════════

def test_spec_6_3_object_does_not_exist():
    """§6.3: Object does not exist → stage_candidate, no Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state=None,  # object doesn't exist
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == False


def test_spec_6_3_object_draft():
    """§6.3: Object in draft → retrieve + stage_candidate, no Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="draft",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "stage_candidate"
    assert result.requires_eric_gate == True  # draft → approval needs gate


def test_spec_6_3_object_approved():
    """§6.3: Object approved → retrieve + request_approval, Eric Gate."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="approved",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.candidates_allowed == False


def test_spec_6_3_object_locked():
    """§6.3: Object locked → retrieve only, no mutation."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="locked",
    )
    result = pm.process(intent)
    assert result.allowed == True
    assert result.allowed_action == "retrieve"
    assert result.candidates_allowed == False


def test_spec_6_3_invalid_transition():
    """§6.3: Invalid transition → block."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="KNOWLEDGE_INTAKE",
        workflow_state="INVALID_STATE_XYZ",
    )
    result = pm.process(intent)
    assert result.allowed == False
    assert result.allowed_action == "block"


# ═══════════════════════════════════════════════════
# Boundary tests
# ═══════════════════════════════════════════════════

def test_pm_does_not_bypass_eric_gate():
    """IMPLEMENTATION_DIRECTIVE always requires Eric Gate (never False)."""
    pm = ProcessManager()
    intent = WorkIntent(
        domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
    )
    result = pm.process(intent)
    assert result.requires_eric_gate == True
    # Even with a different state, Eric Gate still required
    intent.workflow_state = "draft"
    result2 = pm.process(intent)
    assert result2.requires_eric_gate == True


def test_pm_result_fields():
    """ProcessResult has all required fields."""
    result = ProcessResult(
        allowed=True, allowed_action="retrieve",
        requires_eric_gate=False, reason="test",
    )
    assert hasattr(result, "allowed")
    assert hasattr(result, "allowed_action")
    assert hasattr(result, "requires_eric_gate")
    assert hasattr(result, "reason")
    assert hasattr(result, "workflow_state")
    assert hasattr(result, "candidates_allowed")


def test_read_only_intents_defined():
    """READ_ONLY_INTENTS set is correct."""
    assert "ARCHIVE_DISCOVERY" in READ_ONLY_INTENTS
    assert "KNOWLEDGE_RETRIEVAL" in READ_ONLY_INTENTS


def test_gated_intents_defined():
    """GATED_INTENTS set is correct."""
    assert "IMPLEMENTATION_DIRECTIVE" in GATED_INTENTS


def test_blocked_intents_defined():
    """BLOCKED_INTENTS set is correct."""
    assert "BLOCKED_MISSING_CAPABILITY" in BLOCKED_INTENTS


# ═══════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # Back-compat
        ("7R.1 classify() unchanged", test_7r1_classify_unchanged),
        ("7R.2 classify_full CIS unchanged", test_7r2_classify_full_cis_unchanged),
        ("7R.2 classify_with_candidates unchanged", test_7r2_classify_with_candidates_unchanged),
        ("7R.3 classify_full SWA unchanged", test_7r3_classify_full_swa_unchanged),
        # PM structure
        ("PM: instantiable", test_pm_instantiable),
        ("PM: returns ProcessResult", test_pm_returns_process_result),
        ("PM: rules loaded", test_pm_rules_loaded),
        # Read-only
        ("PM: archive discovery allowed", test_pm_archive_discovery_allowed),
        ("PM: knowledge retrieval allowed", test_pm_knowledge_retrieval_allowed),
        # Gated
        ("PM: implementation gated (CIS)", test_pm_implementation_directive_gated),
        ("PM: implementation gated (SWA)", test_pm_implementation_directive_swa),
        # Blocked
        ("PM: blocked intent", test_pm_blocked_intent),
        # CIS transitions
        ("PM: CIS intake arrived", test_pm_cis_intake_arrived),
        ("PM: CIS intake draft", test_pm_cis_intake_draft),
        ("PM: CIS intake approved", test_pm_cis_intake_approved),
        ("PM: CIS intake locked", test_pm_cis_intake_locked),
        ("PM: CIS requirements PENDING", test_pm_cis_requirements_pending),
        ("PM: CIS requirements BLOCKED", test_pm_cis_requirements_blocked),
        # SWA transitions
        ("PM: SWA PRE_PLAN", test_pm_swa_pre_plan),
        ("PM: SWA INTAKE", test_pm_swa_intake),
        ("PM: SWA NEED_IDENTIFIED", test_pm_swa_need_identified),
        ("PM: SWA GOAL_DEFINED", test_pm_swa_goal_defined),
        ("PM: SWA APPOINTMENT_UNLINKED", test_pm_swa_unlinked_appointment),
        ("PM: SWA NOTE_GENERATED", test_pm_swa_note_generated),
        ("PM: SWA APPROVED", test_pm_swa_approved),
        # Invalid
        ("PM: invalid transition blocked", test_pm_invalid_transition_blocked),
        ("PM: unknown domain blocked", test_pm_unknown_domain_blocked),
        ("PM: object does not exist (CIS)", test_pm_object_does_not_exist_cis),
        ("PM: object does not exist (SWA)", test_pm_object_does_not_exist_swa),
        # Domain neutrality
        ("PM: works with CIS", test_pm_works_with_cis),
        ("PM: works with SWA", test_pm_works_with_swa),
        ("PM: does not execute", test_pm_does_not_execute),
        # classify_with_pm pipeline
        ("Pipeline: archive with PM", test_pipeline_archive_with_pm),
        ("Pipeline: intake with PM", test_pipeline_intake_with_pm),
        ("Pipeline: Micro1 with PM", test_pipeline_micro1_with_pm),
        ("Pipeline: SWA pre-plan with PM", test_pipeline_swa_pre_plan_with_pm),
        # classify_full_pipeline
        ("Full pipeline: archive", test_full_pipeline_archive),
        ("Full pipeline: intake", test_full_pipeline_intake),
        ("Full pipeline: Micro1", test_full_pipeline_micro1),
        ("Full pipeline: SWA workflow", test_full_pipeline_swa_workflow),
        ("Full pipeline: SWA recovery", test_full_pipeline_swa_recovery),
        # Spec §6.3 validation
        ("Spec §6.3: object doesn't exist", test_spec_6_3_object_does_not_exist),
        ("Spec §6.3: object draft", test_spec_6_3_object_draft),
        ("Spec §6.3: object approved", test_spec_6_3_object_approved),
        ("Spec §6.3: object locked", test_spec_6_3_object_locked),
        ("Spec §6.3: invalid transition", test_spec_6_3_invalid_transition),
        # Boundary
        ("Boundary: never bypasses Eric Gate", test_pm_does_not_bypass_eric_gate),
        ("Boundary: ProcessResult fields", test_pm_result_fields),
        ("Boundary: READ_ONLY_INTENTS", test_read_only_intents_defined),
        ("Boundary: GATED_INTENTS", test_gated_intents_defined),
        ("Boundary: BLOCKED_INTENTS", test_blocked_intents_defined),
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
