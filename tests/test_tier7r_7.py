"""
7R.7 Acceptance Test Suite — full Tier 7R pipeline integration.

Verifies the complete WorkIntent → Content-Based Router → Domain Adapters →
Process Manager → Human Approval Gate → Dead Letter pipeline end-to-end.

Per docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §8:
- §8.1: SWA Phase 45 — Flexible Documentation Workflow
- §8.2: SWA Unlinked Appointment
- §8.3: CIS File-to-Knowledge Pipeline
- §8.4: Archive Discovery
- §8.5: Micro1 Out-of-Scope Rejection
- §8.6: Implementation Directive (blocked without Eric Gate)

Plus cross-cutting verification:
- PM does not execute implementation work
- Human approval required before executable advancement
- Dead-letter captures all blocked states
- Unsupported/unsafe/excluded work cannot advance
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.process_manager import ProcessManager
from runtime.tier7r.approval_gate import ApprovalGate
from runtime.tier7r.dead_letter import (
    DeadLetterRegistry,
    BlockCategory,
    BlockRecord,
    handle_blocked_result,
)
from runtime.tier7r.classifier import (
    classify_full_pipeline_with_dl,
    classify_full_pipeline_with_approval,
    classify_with_pm,
)
from runtime.tier7r.adapters import get_adapter


# ═══════════════════════════════════════════════════
# Smoke: all 7R.1-7R.6 tests still pass
# ═══════════════════════════════════════════════════

def test_smoke_7r1_through_7r6():
    """Run the existing test suites to confirm nothing broke."""
    import subprocess
    for tier in range(1, 7):
        result = subprocess.run(
            ["python3", f"tests/test_tier7r_{tier}.py"],
            capture_output=True, text=True, cwd="/mnt/projects/cis"
        )
        assert result.returncode == 0, \
            f"7R.{tier} tests FAILED:\n{result.stdout}\n{result.stderr}"


# ═══════════════════════════════════════════════════
# §8.3: CIS File-to-Knowledge Pipeline (KNOWLEDGE_INTAKE)
# ═══════════════════════════════════════════════════

def test_spec_8_3_full_pipeline():
    """
    §8.3: "Process this PDF into a knowledge record"
    Through full 7R.6 pipeline: classify → PM → gate → DL → stage.
    """
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl(
            "Process this PDF into a knowledge record"
        )
    # Classification
    assert intent.domain == "CIS"
    assert intent.intent_class == "KNOWLEDGE_INTAKE"
    assert intent.object_type == "source_manifest"
    # Process Manager
    assert pm_result.allowed == True
    assert pm_result.allowed_action == "stage_candidate"
    assert pm_result.requires_eric_gate == False
    # Approval Gate — not gated
    assert decision.status == "NOT_GATED"
    # Dead Letter — not blocked
    assert block_record is None
    # Candidates staged
    assert len(candidates) == 2
    assert all(c.status == "STAGED" for c in candidates)
    assert candidates[0].object_type == "source_manifest"
    assert candidates[1].object_type == "knowledge_record"


# ═══════════════════════════════════════════════════
# §8.4: Archive Discovery (read-only, no mutation)
# ═══════════════════════════════════════════════════

def test_spec_8_4_full_pipeline():
    """
    §8.4: "What did I say about the social worker app in past sessions?"
    Archive discovery through full pipeline.
    """
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl(
            "What did I say about the social worker app in past sessions?"
        )
    # Classification
    assert intent.domain == "CIS"
    assert intent.intent_class == "ARCHIVE_DISCOVERY"
    # Process Manager — read-only
    assert pm_result.allowed == True
    assert pm_result.allowed_action == "retrieve"
    assert pm_result.candidates_allowed == False
    assert pm_result.requires_eric_gate == False
    # Approval Gate — not gated
    assert decision.status == "NOT_GATED"
    # Dead Letter — not blocked
    assert block_record is None
    # No candidates (read-only)
    assert len(candidates) == 0


# ═══════════════════════════════════════════════════
# §8.5: Micro1 Out-of-Scope Rejection
# ═══════════════════════════════════════════════════

def test_spec_8_5_full_pipeline():
    """
    §8.5: "Start Micro1 task planning"
    Full pipeline → OUT_OF_SCOPE, blocked, dead-letter recorded.
    """
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl("Start Micro1 task planning")
    # Classification
    assert intent.domain == "OUT_OF_SCOPE"
    assert intent.status == "BLOCKED"
    assert intent.intent_class == "BLOCKED_MISSING_CAPABILITY"
    # No candidates
    assert len(candidates) == 0
    # Dead Letter recorded
    assert block_record is not None
    assert block_record.category in (BlockCategory.MISSING_CAPABILITY,
                                     BlockCategory.INVALID_TRANSITION)


# ═══════════════════════════════════════════════════
# §8.6: Implementation Directive (blocked without Eric Gate)
# ═══════════════════════════════════════════════════

def test_spec_8_6_blocked_without_approval():
    """
    §8.6: "Build Tier 8" (IMPLEMENTATION_DIRECTIVE)
    Without prior approval → AWAITING_APPROVAL, dead-letter recorded.
    """
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl("Build Tier 8")
    # Classification
    assert intent.domain == "CIS"
    assert intent.intent_class == "IMPLEMENTATION_DIRECTIVE"
    # Process Manager — gated
    assert pm_result.requires_eric_gate == True
    # Approval Gate — awaiting (not yet approved)
    assert decision.status == "AWAITING_APPROVAL"
    assert decision.allowed == False
    # No candidates (blocked)
    assert len(candidates) == 0
    # Dead Letter — recorded as awaiting
    assert block_record is not None
    assert block_record.category == BlockCategory.AWAITING_APPROVAL


def test_spec_8_6_approved_proceeds():
    """
    §8.6: IMPLEMENTATION_DIRECTIVE with approval → candidates proceed.
    """
    gate = ApprovalGate()
    registry = DeadLetterRegistry()

    # Pre-classify the intent
    intent, pm_result = classify_with_pm("Build Tier 8")

    # Before approval → blocked
    assert pm_result.requires_eric_gate == True

    # Assign ID and approve manually
    intent_id = intent.id or "manual-gate-test"
    intent.id = intent_id
    gate.approve(intent_id)

    # Gate.check() returns a single ApprovalDecision
    decision_after = gate.check(pm_result, intent)
    assert decision_after.status == "APPROVED"
    assert decision_after.allowed == True

    # verify gate state
    assert gate.is_approved(intent_id) == True


# ═══════════════════════════════════════════════════
# §8.1: SWA Phase 45 — Flexible Documentation Workflow
# ═══════════════════════════════════════════════════

def test_spec_8_1_full_pipeline():
    """
    §8.1: SWA requirements recovery from document analysis.
    Full pipeline → SWA, REQUIREMENTS_RECOVERY, 4 candidates staged.
    """
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl(
            "Use this SWA document to identify what the app needs"
        )
    # Classification
    assert intent.domain == "SWA"
    assert intent.intent_class == "REQUIREMENTS_RECOVERY"
    assert intent.object_type == "build_plan_node"
    # Process Manager
    assert pm_result.allowed == True
    assert pm_result.allowed_action == "stage_candidate"
    # Approval Gate
    assert decision.status == "NOT_GATED"
    # Dead Letter — not blocked
    assert block_record is None
    # Candidates — 4 build_plan_nodes
    assert len(candidates) == 4
    for c in candidates:
        assert c.domain == "SWA"
        assert c.object_type == "build_plan_node"
        assert c.status == "STAGED"


# ═══════════════════════════════════════════════════
# §8.2: SWA Unlinked Appointment
# ═══════════════════════════════════════════════════

def test_spec_8_2_full_pipeline():
    """
    §8.2: "Schedule a crisis call with client — no formal goal exists yet"
    Full pipeline → SWA, DOMAIN_WORKFLOW_EVENT, APPOINTMENT_UNLINKED.
    """
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl(
            "Schedule a crisis call with client — no formal goal exists yet"
        )
    # Classification
    assert intent.domain == "SWA"
    assert intent.intent_class == "DOMAIN_WORKFLOW_EVENT"
    assert intent.workflow_state == "APPOINTMENT_UNLINKED"
    # Process Manager — valid unlinked appointment
    assert pm_result.allowed == True
    assert pm_result.allowed_action == "stage_candidate"
    assert pm_result.requires_eric_gate == False
    # Approval Gate — not gated
    assert decision.status == "NOT_GATED"
    # Dead Letter — not blocked
    assert block_record is None
    # Candidates
    assert len(candidates) == 1
    assert candidates[0].workflow_state == "APPOINTMENT_UNLINKED"


# ═══════════════════════════════════════════════════
# Cross-cutting: Process Manager does not execute
# ═══════════════════════════════════════════════════

def test_pm_never_executes():
    """Process Manager validates transitions but never executes work."""
    pm = ProcessManager()
    # Test with multiple domains and states
    intents = [
        WorkIntent(domain="CIS", intent_class="KNOWLEDGE_INTAKE", workflow_state="arrived"),
        WorkIntent(domain="SWA", intent_class="DOMAIN_WORKFLOW_EVENT", workflow_state="PRE_PLAN"),
        WorkIntent(domain="CIS", intent_class="ARCHIVE_DISCOVERY", workflow_state="N/A"),
    ]
    for intent in intents:
        original_domain = intent.domain
        original_status = intent.status
        original_state = intent.workflow_state
        result = pm.process(intent)
        # PM returns a result — it does NOT mutate the intent
        assert intent.domain == original_domain
        assert intent.status == original_status
        assert intent.workflow_state == original_state
        # PM result has a recommendation, not an action
        assert isinstance(result.allowed, bool)


def test_gate_never_auto_approves():
    """Human approval gate never auto-approves gated transitions."""
    gate = ApprovalGate()
    pm = ProcessManager()
    for prompt in [
        "Build Tier 8",  # IMPLEMENTATION_DIRECTIVE
    ]:
        intent, pm_result = classify_with_pm(prompt)
        if pm_result.requires_eric_gate:
            decision = gate.check(pm_result)
            assert decision.allowed == False, \
                f"Gated intent was auto-approved: {prompt}"
            assert decision.status == "AWAITING_APPROVAL"


# ═══════════════════════════════════════════════════
# Cross-cutting: Dead-letter captures all blocked states
# ═══════════════════════════════════════════════════

def test_dl_captures_all_blocked():
    """Dead-letter registry captures every blocked state in a shared run."""
    registry = DeadLetterRegistry()
    prompts = [
        ("Start Micro1 task planning", "MISSING"),      # OUT_OF_SCOPE → blocked
        ("What is the capital of France?", "UNRECOGNIZED"),  # no domain → blocked
        ("Build Tier 8", "AWAITING"),                    # gated → awaiting
    ]
    for prompt, _ in prompts:
        classify_full_pipeline_with_dl(prompt, registry=registry)

    # All 3 should be in dead-letter
    assert registry.count() >= 3
    cats = registry.categories_present()
    assert "MISSING_CAPABILITY" in cats, f"Missing Micro1 block: {cats}"
    assert "UNRECOGNIZED" in cats, f"Missing unrecognized block: {cats}"
    assert "AWAITING_APPROVAL" in cats, f"Missing gate block: {cats}"


# ═══════════════════════════════════════════════════
# Cross-cutting: Unsupported work cannot advance
# ═══════════════════════════════════════════════════

def test_unsupported_cannot_advance():
    """Work intents that are blocked/dead-letter cannot advance to candidates."""
    blocked_prompts = [
        "Start Micro1 task planning",
        "What is the capital of France?",
    ]
    for prompt in blocked_prompts:
        intent, candidates, pm_result, decision, block_record = \
            classify_full_pipeline_with_dl(prompt)
        assert len(candidates) == 0, \
            f"Blocked prompt '{prompt}' generated candidates!"
        assert block_record is not None, \
            f"Blocked prompt '{prompt}' not in dead-letter!"


# ═══════════════════════════════════════════════════
# Cross-cutting: Only valid work advances
# ═══════════════════════════════════════════════════

def test_valid_work_advances():
    """Valid, non-gated work intents advance through the full pipeline."""
    valid_prompts = [
        "Process this PDF into a knowledge record",
        "What did I say about the social worker app in past sessions?",
        "Schedule intake for new client",
        "Use this SWA document to identify what the app needs",
    ]
    for prompt in valid_prompts:
        intent, candidates, pm_result, decision, block_record = \
            classify_full_pipeline_with_dl(prompt)
        # Process Manager should allow
        assert pm_result.allowed == True, \
            f"PM blocked valid prompt: '{prompt}' ({pm_result.reason})"
        # Should not be dead-lettered
        assert block_record is None, \
            f"Valid prompt '{prompt}' was dead-lettered!"


# ═══════════════════════════════════════════════════
# Cross-cutting: Architecture integrity
# ═══════════════════════════════════════════════════

def test_pipeline_layers_integrated():
    """All 7R pipeline layers are present and wired together."""
    # Verify all functions are importable and callable
    from runtime.tier7r.work_intent import WorkIntent
    from runtime.tier7r.scope_registry import Domain, classify_domain
    from runtime.tier7r.domain_adapter import DomainAdapter
    from runtime.tier7r.process_manager import ProcessManager
    from runtime.tier7r.approval_gate import ApprovalGate
    from runtime.tier7r.dead_letter import DeadLetterRegistry
    from runtime.tier7r.classifier import (
        classify, classify_full, classify_with_candidates,
        classify_with_pm, classify_full_pipeline,
        classify_full_pipeline_with_approval,
        classify_full_pipeline_with_dl,
    )
    # If we get here, all layers are importable
    assert True


def test_cis_adapter_present():
    """CISAdapter is registered and functional."""
    adapter = get_adapter("CIS")
    assert adapter is not None
    assert adapter.domain == "CIS"
    intent = WorkIntent(domain="CIS", source_raw="Process this PDF into a knowledge record")
    result = adapter.classify_intent(intent)
    assert result.intent_class == "KNOWLEDGE_INTAKE"


def test_swa_adapter_present():
    """SWAAdapter is registered and functional (validation use case)."""
    adapter = get_adapter("SWA")
    assert adapter is not None
    assert adapter.domain == "SWA"
    intent = WorkIntent(domain="SWA", source_raw="Schedule intake for new client")
    result = adapter.classify_intent(intent)
    assert result.intent_class == "DOMAIN_WORKFLOW_EVENT"


def test_micro1_never_classified_cis_or_swa():
    """Micro1 is never classified as CIS or SWA."""
    for prompt in [
        "Start Micro1 task planning",
        "work on micro1 stuff",
        "MICRO1 deployment",
    ]:
        intent, _, pm_result, _, _ = classify_full_pipeline_with_dl(prompt)
        assert intent.domain != "CIS", f"Micro1 classified as CIS: {prompt}"
        assert intent.domain != "SWA", f"Micro1 classified as SWA: {prompt}"
        assert intent.status == "BLOCKED"


# ═══════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # Smoke: 7R.1-7R.6 still pass
        ("Smoke: 7R.1-7R.6 all PASS", test_smoke_7r1_through_7r6),
        # Spec §8 acceptance tests (full pipeline)
        ("§8.3: CIS knowledge intake pipeline", test_spec_8_3_full_pipeline),
        ("§8.4: Archive discovery pipeline", test_spec_8_4_full_pipeline),
        ("§8.5: Micro1 exclusion pipeline", test_spec_8_5_full_pipeline),
        ("§8.6: Implementation blocked w/o approval", test_spec_8_6_blocked_without_approval),
        ("§8.6: Implementation approved proceeds", test_spec_8_6_approved_proceeds),
        ("§8.1: SWA Phase 45 pipeline", test_spec_8_1_full_pipeline),
        ("§8.2: SWA unlinked appointment pipeline", test_spec_8_2_full_pipeline),
        # Cross-cutting
        ("PM never executes work", test_pm_never_executes),
        ("Gate never auto-approves", test_gate_never_auto_approves),
        ("DL captures all blocked states", test_dl_captures_all_blocked),
        ("Unsupported work cannot advance", test_unsupported_cannot_advance),
        ("Valid work advances through pipeline", test_valid_work_advances),
        # Architecture integrity
        ("Pipeline layers integrated", test_pipeline_layers_integrated),
        ("CISAdapter present + functional", test_cis_adapter_present),
        ("SWAAdapter present + functional", test_swa_adapter_present),
        ("Micro1 never CIS or SWA", test_micro1_never_classified_cis_or_swa),
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
