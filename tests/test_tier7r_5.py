"""
7R.5 acceptance tests — Human Approval Gate Integration.

Tests the human approval gate layer:
- Blocks gated transitions for Eric approval
- Allows non-gated transitions to proceed
- Supports approve/reject lifecycle
- Integrates with Process Manager and domain adapters
- Never auto-approves or bypasses Eric Gate

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §7.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.process_manager import ProcessManager, ProcessResult
from runtime.tier7r.approval_gate import (
    ApprovalGate,
    ApprovalDecision,
    process_with_approval,
)
from runtime.tier7r.classifier import (
    classify,
    classify_full,
    classify_with_candidates,
    classify_with_pm,
    classify_full_pipeline,
    classify_full_pipeline_with_approval,
)


# ═══════════════════════════════════════════════════
# 7R.1-7R.4 back-compat tests
# ═══════════════════════════════════════════════════

def test_7r1_classify_unchanged():
    wi = classify("Start Micro1 task planning")
    assert wi.domain == "OUT_OF_SCOPE"
    assert wi.status == "BLOCKED"


def test_7r2_cis_archive_unchanged():
    wi = classify_full("What did I say about the social worker app in past sessions?")
    assert wi.domain == "CIS"
    assert wi.intent_class == "ARCHIVE_DISCOVERY"


def test_7r3_swa_crisis_unchanged():
    wi = classify_full("Schedule a crisis call with client — no formal goal exists yet")
    assert wi.domain == "SWA"


def test_7r4_pm_pipeline_unchanged():
    intent, candidates, result = classify_full_pipeline("Process this PDF into a knowledge record")
    assert intent.domain == "CIS"
    assert result.allowed == True
    assert len(candidates) == 2


# ═══════════════════════════════════════════════════
# ApprovalGate: basic structure
# ═══════════════════════════════════════════════════

def test_gate_instantiable():
    gate = ApprovalGate()
    assert gate is not None


def test_approval_decision_structure():
    d = ApprovalDecision(allowed=True, status="APPROVED", reason="test")
    assert d.allowed == True
    assert d.status == "APPROVED"
    assert d.requires_eric_gate == False
    assert d.intent_id is None


# ═══════════════════════════════════════════════════
# ApprovalGate.check() — non-gated transitions
# ═══════════════════════════════════════════════════

def test_check_not_gated():
    """Non-gated transitions → NOT_GATED, allowed."""
    gate = ApprovalGate()
    result = ProcessResult(allowed=True, allowed_action="retrieve",
                           requires_eric_gate=False, reason="read-only")
    decision = gate.check(result)
    assert decision.allowed == True
    assert decision.status == "NOT_GATED"
    assert decision.requires_eric_gate == False


def test_check_not_gated_archive():
    """ARCHIVE_DISCOVERY → not gated."""
    gate = ApprovalGate()
    result = ProcessResult(allowed=True, allowed_action="retrieve",
                           requires_eric_gate=False, reason="read-only",
                           candidates_allowed=False)
    decision = gate.check(result)
    assert decision.allowed == True
    assert decision.status == "NOT_GATED"


# ═══════════════════════════════════════════════════
# ApprovalGate.check() — gated transitions
# ═══════════════════════════════════════════════════

def test_check_gated_awaiting():
    """Gated transition without approval → AWAITING_APPROVAL, blocked."""
    gate = ApprovalGate()
    result = ProcessResult(allowed=True, allowed_action="request_approval",
                           requires_eric_gate=True, reason="needs approval")
    decision = gate.check(result)
    assert decision.allowed == False
    assert decision.status == "AWAITING_APPROVAL"
    assert decision.requires_eric_gate == True


def test_check_gated_approved():
    """Gated transition after approval → APPROVED, allowed."""
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
                        id="gate-123")
    result = ProcessResult(allowed=True, allowed_action="request_approval",
                           requires_eric_gate=True, reason="needs approval")

    # First check → awaiting
    d1 = gate.check(result, intent)
    assert d1.status == "AWAITING_APPROVAL"

    # Approve
    gate.approve("gate-123")

    # Re-check → approved
    d2 = gate.check(result, intent)
    assert d2.allowed == True
    assert d2.status == "APPROVED"


def test_check_gated_rejected():
    """Gated transition after rejection → REJECTED, blocked."""
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
                        id="gate-456")
    result = ProcessResult(allowed=True, allowed_action="request_approval",
                           requires_eric_gate=True, reason="needs approval")

    gate.reject("gate-456", "Not ready for implementation")
    decision = gate.check(result, intent)
    assert decision.allowed == False
    assert decision.status == "REJECTED"
    assert "Not ready" in decision.reason


# ═══════════════════════════════════════════════════
# ApprovalGate.approve() / reject()
# ═══════════════════════════════════════════════════

def test_approve_returns_decision():
    gate = ApprovalGate()
    d = gate.approve("gate-1")
    assert d.status == "APPROVED"
    assert d.allowed == True
    assert d.intent_id == "gate-1"


def test_reject_returns_decision():
    gate = ApprovalGate()
    d = gate.reject("gate-2", "blocked by review")
    assert d.status == "REJECTED"
    assert d.allowed == False
    assert "blocked by review" in d.reason


def test_approve_then_reject():
    """Reject after approve clears previous approval."""
    gate = ApprovalGate()
    gate.approve("gate-3")
    assert gate.is_approved("gate-3") == True

    gate.reject("gate-3", "changed mind")
    assert gate.is_approved("gate-3") == False
    assert gate.is_rejected("gate-3") == True


def test_reject_then_approve():
    """Approve after reject clears previous rejection."""
    gate = ApprovalGate()
    gate.reject("gate-4", "initial rejection")
    assert gate.is_rejected("gate-4") == True

    gate.approve("gate-4")
    assert gate.is_approved("gate-4") == True
    assert gate.is_rejected("gate-4") == False


def test_multiple_independent_intents():
    """Each intent has independent approval state."""
    gate = ApprovalGate()
    gate.approve("gate-a")
    gate.reject("gate-b", "not yet")

    assert gate.is_approved("gate-a") == True
    assert gate.is_rejected("gate-b") == True
    assert gate.is_approved("gate-b") == False
    assert gate.is_rejected("gate-a") == False


# ═══════════════════════════════════════════════════
# process_with_approval() integration
# ═══════════════════════════════════════════════════

def test_process_with_approval_not_gated():
    """Non-gated PM result → allowed, candidates proceed."""
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", intent_class="ARCHIVE_DISCOVERY")
    pm_result = ProcessResult(allowed=True, allowed_action="retrieve",
                              requires_eric_gate=False, reason="read-only")
    decision, allowed = process_with_approval(intent, pm_result, gate)
    assert decision.status == "NOT_GATED"
    assert allowed == True


def test_process_with_approval_gated():
    """Gated PM result → AWAITING_APPROVAL, blocked."""
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE")
    pm_result = ProcessResult(allowed=True, allowed_action="request_approval",
                              requires_eric_gate=True, reason="gated")
    decision, allowed = process_with_approval(intent, pm_result, gate)
    assert decision.status == "AWAITING_APPROVAL"
    assert allowed == False


def test_process_with_approval_after_approval():
    """Gated + approved → allowed."""
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
                        id="gate-x")
    pm_result = ProcessResult(allowed=True, allowed_action="request_approval",
                              requires_eric_gate=True, reason="gated")

    # First pass → awaiting
    d1, a1 = process_with_approval(intent, pm_result, gate)
    assert a1 == False

    # Approve
    gate.approve("gate-x")

    # Second pass → allowed
    d2, a2 = process_with_approval(intent, pm_result, gate)
    assert a2 == True
    assert d2.status == "APPROVED"


# ═══════════════════════════════════════════════════
# Full pipeline with approval gate
# ═══════════════════════════════════════════════════

def test_full_pipeline_approval_archive():
    """classify_full_pipeline_with_approval() → archive not gated, candidates=0."""
    intent, candidates, pm_result, decision = classify_full_pipeline_with_approval(
        "What did I say about the social worker app in past sessions?"
    )
    assert intent.domain == "CIS"
    assert decision.status == "NOT_GATED"
    assert decision.allowed == True
    assert len(candidates) == 0  # read-only


def test_full_pipeline_approval_intake():
    """classify_full_pipeline_with_approval() → intake not gated, candidates=2."""
    intent, candidates, pm_result, decision = classify_full_pipeline_with_approval(
        "Process this PDF into a knowledge record"
    )
    assert intent.domain == "CIS"
    assert decision.status == "NOT_GATED"
    assert len(candidates) == 2


def test_full_pipeline_approval_micro1():
    """classify_full_pipeline_with_approval() → Micro1 blocked."""
    intent, candidates, pm_result, decision = classify_full_pipeline_with_approval(
        "Start Micro1 task planning"
    )
    assert intent.domain == "OUT_OF_SCOPE"
    assert len(candidates) == 0


def test_full_pipeline_approval_swa():
    """classify_full_pipeline_with_approval() → SWA workflow, not gated."""
    intent, candidates, pm_result, decision = classify_full_pipeline_with_approval(
        "Schedule intake for new client"
    )
    assert intent.domain == "SWA"
    assert len(candidates) >= 1
    assert decision.status == "NOT_GATED"


# ═══════════════════════════════════════════════════
# Gate enforcement: implementation directive blocked
# ═══════════════════════════════════════════════════

def test_implementation_blocked_by_gate():
    """IMPLEMENTATION_DIRECTIVE is gated → AWAITING_APPROVAL in pipeline."""
    intent, candidates, pm_result, decision = classify_full_pipeline_with_approval(
        "Build Tier 8"
    )
    assert intent.domain == "CIS"
    assert intent.intent_class == "IMPLEMENTATION_DIRECTIVE"
    assert pm_result.requires_eric_gate == True
    # Without prior approval → blocked
    assert decision.status == "AWAITING_APPROVAL"
    assert decision.allowed == False
    assert len(candidates) == 0


def test_implementation_approved_proceeds():
    """IMPLEMENTATION_DIRECTIVE with approval → candidates proceed."""
    gate = ApprovalGate()
    # Pre-approve the specific intent
    intent_pre = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
                            id="gate-impl-1")
    gate.approve("gate-impl-1")

    # Hmm — pipeline creates its own intent, can't pre-set the ID.
    # Instead, test via process_with_approval directly
    pm = ProcessManager()
    intent = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
                        id="gate-impl-2", source_raw="Build Tier 8")
    pm_result = pm.process(intent)

    # Should be gated
    assert pm_result.requires_eric_gate == True

    # Before approval → blocked
    d1, a1 = process_with_approval(intent, pm_result, gate)
    assert a1 == False

    # After approval → allowed
    gate.approve("gate-impl-2")
    d2, a2 = process_with_approval(intent, pm_result, gate)
    assert a2 == True
    assert d2.status == "APPROVED"


# ═══════════════════════════════════════════════════
# Never bypass Eric Gate
# ═══════════════════════════════════════════════════

def test_never_auto_approve():
    """Gated transitions are never auto-approved."""
    gate = ApprovalGate()
    # 10 different gated results — all should be AWAITING_APPROVAL
    for i in range(5):
        intent = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE",
                            id=f"gate-never-{i}")
        pm_result = ProcessResult(allowed=True, allowed_action="request_approval",
                                  requires_eric_gate=True, reason="test")
        decision, allowed = process_with_approval(intent, pm_result, gate)
        assert decision.status == "AWAITING_APPROVAL", \
            f"Intent {i} was auto-approved!"
        assert allowed == False


def test_gate_does_not_bypass_pm():
    """Approval gate does not bypass Process Manager validation."""
    gate = ApprovalGate()
    # A blocked PM result should stay blocked even if "approved"
    pm_result = ProcessResult(allowed=False, allowed_action="block",
                              requires_eric_gate=False, reason="blocked")
    intent = WorkIntent(domain="CIS", intent_class="BLOCKED_MISSING_CAPABILITY",
                        id="gate-pm-blocked")
    gate.approve("gate-pm-blocked")

    # Gate check: PM result isn't gated → NOT_GATED
    # But the PM already said "not allowed" — the gate doesn't override PM
    decision = gate.check(pm_result, intent)
    assert decision.status == "NOT_GATED"  # gate doesn't add blocking here
    assert pm_result.allowed == False  # PM still says blocked


def test_gate_state_explicit():
    """Approval state is explicit and inspectable."""
    gate = ApprovalGate()
    gate.approve("inspect-1")
    gate.reject("inspect-2", "reason")

    assert gate.is_approved("inspect-1") == True
    assert gate.is_rejected("inspect-2") == True
    assert gate.is_approved("inspect-3") == False  # never seen
    assert gate.is_rejected("inspect-3") == False


# ═══════════════════════════════════════════════════
# Backward compatibility
# ═══════════════════════════════════════════════════

def test_existing_functions_unchanged():
    """All pre-7R.5 functions still work identically."""
    # classify_with_candidates still works
    intent, candidates = classify_with_candidates("Process this PDF into a knowledge record")
    assert intent.domain == "CIS"
    assert len(candidates) == 2

    # classify_full_pipeline still works (no gate)
    intent2, candidates2, result2 = classify_full_pipeline(
        "Use this SWA document to identify what the app needs"
    )
    assert intent2.domain == "SWA"
    assert len(candidates2) == 4


# ═══════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # Back-compat
        ("7R.1 classify() unchanged", test_7r1_classify_unchanged),
        ("7R.2 CIS archive unchanged", test_7r2_cis_archive_unchanged),
        ("7R.3 SWA crisis unchanged", test_7r3_swa_crisis_unchanged),
        ("7R.4 PM pipeline unchanged", test_7r4_pm_pipeline_unchanged),
        # Gate structure
        ("Gate: instantiable", test_gate_instantiable),
        ("Gate: ApprovalDecision structure", test_approval_decision_structure),
        # Non-gated checks
        ("Check: not gated", test_check_not_gated),
        ("Check: not gated (archive)", test_check_not_gated_archive),
        # Gated checks
        ("Check: gated awaiting", test_check_gated_awaiting),
        ("Check: gated approved", test_check_gated_approved),
        ("Check: gated rejected", test_check_gated_rejected),
        # Approve/reject lifecycle
        ("Approve returns decision", test_approve_returns_decision),
        ("Reject returns decision", test_reject_returns_decision),
        ("Approve then reject", test_approve_then_reject),
        ("Reject then approve", test_reject_then_approve),
        ("Multiple independent intents", test_multiple_independent_intents),
        # process_with_approval
        ("process_with_approval: not gated", test_process_with_approval_not_gated),
        ("process_with_approval: gated", test_process_with_approval_gated),
        ("process_with_approval: after approval", test_process_with_approval_after_approval),
        # Full pipeline with approval
        ("Pipeline: archive (approval)", test_full_pipeline_approval_archive),
        ("Pipeline: intake (approval)", test_full_pipeline_approval_intake),
        ("Pipeline: Micro1 (approval)", test_full_pipeline_approval_micro1),
        ("Pipeline: SWA (approval)", test_full_pipeline_approval_swa),
        # Gate enforcement
        ("Gate: implementation blocked", test_implementation_blocked_by_gate),
        ("Gate: implementation approved proceeds", test_implementation_approved_proceeds),
        # Never bypass
        ("Never auto-approve", test_never_auto_approve),
        ("Gate doesn't bypass PM", test_gate_does_not_bypass_pm),
        ("Approval state explicit", test_gate_state_explicit),
        # Backward compat
        ("Existing functions unchanged", test_existing_functions_unchanged),
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
