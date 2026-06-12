"""
7R.6 acceptance tests — Dead Letter / Blocked Handling.

Tests the dead-letter registry for capturing blocked intents:
- Records blocked intents by category
- Integrates with Process Manager and Approval Gate
- Provides inspection and query methods
- Supports dismissal
- Pipeline integration records blocked states

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §2.1 and §11.4.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.process_manager import ProcessManager, ProcessResult
from runtime.tier7r.approval_gate import ApprovalGate, process_with_approval
from runtime.tier7r.dead_letter import (
    BlockCategory,
    BlockRecord,
    DeadLetterRegistry,
    handle_blocked_result,
)
from runtime.tier7r.classifier import (
    classify,
    classify_full,
    classify_with_candidates,
    classify_with_pm,
    classify_full_pipeline,
    classify_full_pipeline_with_approval,
    classify_full_pipeline_with_dl,
)


# ═══════════════════════════════════════════════════
# 7R.1-7R.5 back-compat tests
# ═══════════════════════════════════════════════════

def test_all_layers_unchanged():
    """Pre-7R.6 functions still work identically."""
    wi = classify("Start Micro1 task planning")
    assert wi.status == "BLOCKED"

    wi2 = classify_full("What did I say about the social worker app in past sessions?")
    assert wi2.intent_class == "ARCHIVE_DISCOVERY"

    intent, candidates = classify_with_candidates("Process this PDF into a knowledge record")
    assert len(candidates) == 2

    intent2, result = classify_with_pm("Process this PDF into a knowledge record")
    assert result.allowed == True

    intent3, candidates3, result3 = classify_full_pipeline("Schedule intake for new client")
    assert result3.allowed == True

    intent4, candidates4, result4, decision4 = classify_full_pipeline_with_approval(
        "What did I say about the social worker app in past sessions?"
    )
    assert decision4.status == "NOT_GATED"


# ═══════════════════════════════════════════════════
# DeadLetterRegistry: basic structure
# ═══════════════════════════════════════════════════

def test_registry_instantiable():
    registry = DeadLetterRegistry()
    assert registry is not None
    assert registry.count() == 0


def test_block_record_structure():
    record = BlockRecord(
        intent_id="test-1",
        category=BlockCategory.OUT_OF_SCOPE,
        reason="test reason",
        source="test",
    )
    d = record.to_dict()
    assert d["intent_id"] == "test-1"
    assert d["category"] == "OUT_OF_SCOPE"
    assert d["reason"] == "test reason"
    assert d["source"] == "test"


def test_block_categories_defined():
    categories = [c.value for c in BlockCategory]
    assert "OUT_OF_SCOPE" in categories
    assert "UNSUPPORTED_DOMAIN" in categories
    assert "INVALID_TRANSITION" in categories
    assert "REJECTED_BY_GATE" in categories
    assert "AWAITING_APPROVAL" in categories
    assert "MISSING_CAPABILITY" in categories
    assert "UNRECOGNIZED" in categories


# ═══════════════════════════════════════════════════
# DeadLetterRegistry: record methods
# ═══════════════════════════════════════════════════

def test_record_out_of_scope():
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="OUT_OF_SCOPE", source_raw="Micro1 task",
                        intent_class="BLOCKED_MISSING_CAPABILITY")
    record = registry.record_out_of_scope(intent, "Micro1 excluded")
    assert registry.count() == 1
    assert record.category == BlockCategory.OUT_OF_SCOPE
    assert "Micro1" in record.reason


def test_record_unsupported_domain():
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="BOGUS", source_raw="unknown prompt")
    record = registry.record_unsupported_domain(intent)
    assert record.category == BlockCategory.UNSUPPORTED_DOMAIN
    assert "BOGUS" in record.reason


def test_record_unrecognized():
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="", source_raw="random text")
    record = registry.record_unrecognized(intent)
    assert record.category == BlockCategory.UNRECOGNIZED


def test_record_from_pm():
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="CIS", intent_class="KNOWLEDGE_INTAKE",
                        workflow_state="INVALID")
    pm_result = ProcessResult(allowed=False, allowed_action="block",
                              requires_eric_gate=False,
                              reason="No valid transition")
    record = registry.record_from_pm(intent, pm_result)
    assert record.category == BlockCategory.INVALID_TRANSITION
    assert "No valid transition" in record.reason
    assert record.source == "process_manager"


def test_record_from_gate_rejected():
    registry = DeadLetterRegistry()
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", id="gate-dl-1",
                        intent_class="IMPLEMENTATION_DIRECTIVE")
    gate.reject("gate-dl-1", "Not approved for execution")
    decision = gate.check(
        ProcessResult(allowed=True, allowed_action="request_approval",
                      requires_eric_gate=True, reason="gated"),
        intent,
    )
    assert decision.status == "REJECTED"
    record = registry.record_from_gate(intent, decision)
    assert record is not None
    assert record.category == BlockCategory.REJECTED_BY_GATE
    assert "Not approved" in record.reason


def test_record_multiple_categories():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="OUT_OF_SCOPE"), BlockCategory.OUT_OF_SCOPE, "r1", "s1")
    registry.record(WorkIntent(domain="BOGUS"), BlockCategory.UNSUPPORTED_DOMAIN, "r2", "s2")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.INVALID_TRANSITION, "r3", "s3")
    assert registry.count() == 3


# ═══════════════════════════════════════════════════
# DeadLetterRegistry: query methods
# ═══════════════════════════════════════════════════

def test_get_all():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="CIS"), BlockCategory.OUT_OF_SCOPE, "r1", "s")
    registry.record(WorkIntent(domain="SWA"), BlockCategory.UNSUPPORTED_DOMAIN, "r2", "s")
    assert len(registry.get_all()) == 2


def test_get_by_category():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="CIS"), BlockCategory.OUT_OF_SCOPE, "r1", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.INVALID_TRANSITION, "r2", "s")
    registry.record(WorkIntent(domain="SWA"), BlockCategory.OUT_OF_SCOPE, "r3", "s")

    out_of_scope = registry.get_by_category(BlockCategory.OUT_OF_SCOPE)
    assert len(out_of_scope) == 2
    invalid = registry.get_by_category(BlockCategory.INVALID_TRANSITION)
    assert len(invalid) == 1


def test_get_by_id():
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="CIS", id="my-id")
    registry.record(intent, BlockCategory.OUT_OF_SCOPE, "reason", "source")
    record = registry.get_by_id("my-id")
    assert record is not None
    assert record.intent_id == "my-id"


def test_get_by_id_missing():
    registry = DeadLetterRegistry()
    assert registry.get_by_id("nonexistent") is None


def test_count_by_category():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="CIS"), BlockCategory.UNRECOGNIZED, "r1", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.UNRECOGNIZED, "r2", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.MISSING_CAPABILITY, "r3", "s")
    assert registry.count_by_category(BlockCategory.UNRECOGNIZED) == 2
    assert registry.count_by_category(BlockCategory.MISSING_CAPABILITY) == 1
    assert registry.count_by_category(BlockCategory.OUT_OF_SCOPE) == 0


def test_categories_present():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="CIS"), BlockCategory.OUT_OF_SCOPE, "r", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.INVALID_TRANSITION, "r", "s")
    cats = registry.categories_present()
    assert "INVALID_TRANSITION" in cats
    assert "OUT_OF_SCOPE" in cats


# ═══════════════════════════════════════════════════
# DeadLetterRegistry: dismissal
# ═══════════════════════════════════════════════════

def test_dismiss_by_id():
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="CIS", id="dismiss-me")
    registry.record(intent, BlockCategory.UNRECOGNIZED, "reason", "source")
    assert registry.count() == 1

    result = registry.dismiss("dismiss-me")
    assert result == True
    assert registry.count() == 0
    assert registry.get_by_id("dismiss-me") is None


def test_dismiss_missing():
    registry = DeadLetterRegistry()
    result = registry.dismiss("nonexistent")
    assert result == False


def test_dismiss_by_category():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="CIS"), BlockCategory.UNRECOGNIZED, "r1", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.UNRECOGNIZED, "r2", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.OUT_OF_SCOPE, "r3", "s")
    assert registry.count() == 3

    removed = registry.dismiss_by_category(BlockCategory.UNRECOGNIZED)
    assert removed == 2
    assert registry.count() == 1
    assert registry.count_by_category(BlockCategory.UNRECOGNIZED) == 0


def test_clear():
    registry = DeadLetterRegistry()
    registry.record(WorkIntent(domain="CIS"), BlockCategory.UNRECOGNIZED, "r1", "s")
    registry.record(WorkIntent(domain="CIS"), BlockCategory.UNRECOGNIZED, "r2", "s")
    count = registry.clear()
    assert count == 2
    assert registry.count() == 0


# ═══════════════════════════════════════════════════
# handle_blocked_result integration
# ═══════════════════════════════════════════════════

def test_handle_blocked_no_registry():
    """Returns None if no registry provided."""
    intent = WorkIntent(domain="OUT_OF_SCOPE", status="BLOCKED")
    pm_result = ProcessResult(allowed=True, allowed_action="retrieve",
                              requires_eric_gate=False, reason="ok")
    record = handle_blocked_result(intent, pm_result)
    assert record is None


def test_handle_blocked_pm():
    """Process Manager blocked → INVALID_TRANSITION recorded."""
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="CIS", intent_class="KNOWLEDGE_INTAKE",
                        workflow_state="NONEXISTENT")
    pm_result = ProcessResult(allowed=False, allowed_action="block",
                              requires_eric_gate=False,
                              reason="No valid transition")
    record = handle_blocked_result(intent, pm_result, registry=registry)
    assert record is not None
    assert record.category == BlockCategory.INVALID_TRANSITION
    assert registry.count() == 1


def test_handle_blocked_gate_rejected():
    """Gate rejected → REJECTED_BY_GATE recorded."""
    registry = DeadLetterRegistry()
    gate = ApprovalGate()
    intent = WorkIntent(domain="CIS", id="gate-hb-1",
                        intent_class="IMPLEMENTATION_DIRECTIVE")
    gate.reject("gate-hb-1", "blocked by review")
    decision = gate.check(
        ProcessResult(allowed=True, allowed_action="request_approval",
                      requires_eric_gate=True, reason="gated"),
        intent,
    )
    record = handle_blocked_result(
        intent,
        ProcessResult(allowed=True, allowed_action="request_approval",
                      requires_eric_gate=True, reason="gated"),
        gate_decision=decision,
        registry=registry,
    )
    assert record is not None
    assert record.category == BlockCategory.REJECTED_BY_GATE


def test_handle_blocked_micro1():
    """OUT_OF_SCOPE → appropriate category recorded."""
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="OUT_OF_SCOPE", status="BLOCKED",
                        intent_class="BLOCKED_MISSING_CAPABILITY",
                        source_raw="Start Micro1 task")
    pm_result = ProcessResult(allowed=True, allowed_action="retrieve",
                              requires_eric_gate=False, reason="ok")
    record = handle_blocked_result(intent, pm_result, registry=registry)
    assert record is not None
    assert record.category == BlockCategory.MISSING_CAPABILITY


def test_handle_blocked_unrecognized():
    """No domain → UNRECOGNIZED recorded."""
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="", source_raw="random text")
    pm_result = ProcessResult(allowed=True, allowed_action="retrieve",
                              requires_eric_gate=False, reason="ok")
    record = handle_blocked_result(intent, pm_result, registry=registry)
    assert record is not None
    assert record.category == BlockCategory.UNRECOGNIZED


# ═══════════════════════════════════════════════════
# classify_full_pipeline_with_dl integration
# ═══════════════════════════════════════════════════

def test_dl_pipeline_archive():
    """Non-blocked pipeline → no block record, candidates proceed."""
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl(
            "What did I say about the social worker app in past sessions?"
        )
    assert intent.domain == "CIS"
    assert block_record is None  # not blocked
    assert decision.status == "NOT_GATED"


def test_dl_pipeline_intake():
    """Non-blocked intake → no block record."""
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl(
            "Process this PDF into a knowledge record"
        )
    assert len(candidates) == 2
    assert block_record is None


def test_dl_pipeline_micro1_blocked():
    """Micro1 → blocked, recorded in dead-letter."""
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl("Start Micro1 task planning")
    assert intent.status == "BLOCKED"
    assert len(candidates) == 0
    assert block_record is not None
    assert block_record.category == BlockCategory.MISSING_CAPABILITY


def test_dl_pipeline_unrecognized():
    """Unrecognized prompt → blocked, UNRECOGNIZED."""
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl("What is the capital of France?")
    assert intent.domain == ""
    assert len(candidates) == 0
    assert block_record is not None
    assert block_record.category == BlockCategory.UNRECOGNIZED


def test_dl_pipeline_implementation_blocked():
    """IMPLEMENTATION_DIRECTIVE → AWAITING_APPROVAL, recorded."""
    intent, candidates, pm_result, decision, block_record = \
        classify_full_pipeline_with_dl("Build Tier 8")
    assert pm_result.requires_eric_gate == True
    assert decision.status == "AWAITING_APPROVAL"
    assert len(candidates) == 0
    assert block_record is not None
    assert block_record.category == BlockCategory.AWAITING_APPROVAL


def test_dl_pipeline_shared_registry():
    """Multiple blocked intents accumulate in shared registry."""
    registry = DeadLetterRegistry()
    for prompt in [
        "Start Micro1 task planning",
        "What is the capital of France?",
        "Build Tier 8",
    ]:
        classify_full_pipeline_with_dl(prompt, registry=registry)
    assert registry.count() >= 3
    cats = registry.categories_present()
    assert "MISSING_CAPABILITY" in cats  # Micro1
    assert "UNRECOGNIZED" in cats  # France
    assert "AWAITING_APPROVAL" in cats  # Build Tier 8


# ═══════════════════════════════════════════════════
# Dead letter does not execute recovery
# ═══════════════════════════════════════════════════

def test_no_auto_recovery():
    """Dead-letter never auto-recovers or re-routes."""
    registry = DeadLetterRegistry()
    intent = WorkIntent(domain="OUT_OF_SCOPE", status="BLOCKED")
    registry.record(intent, BlockCategory.OUT_OF_SCOPE, "excluded", "test")

    # After recording, intent is still blocked
    records = registry.get_by_category(BlockCategory.OUT_OF_SCOPE)
    assert len(records) == 1
    assert records[0].category == BlockCategory.OUT_OF_SCOPE

    # Dismiss it → removed, but no recovery action
    registry.dismiss(records[0].intent_id)
    assert registry.count() == 0
    # The original intent is unchanged — dead-letter only records


def test_dl_explicit_inspectable():
    """All dead-letter entries are explicit and inspectable."""
    registry = DeadLetterRegistry()
    for i in range(3):
        intent = WorkIntent(domain="CIS", id=f"dl-{i}",
                            source_raw=f"blocked prompt {i}")
        registry.record(intent, BlockCategory.INVALID_TRANSITION,
                        f"reason {i}", "test")

    entries = registry.get_all()
    assert len(entries) == 3
    for e in entries:
        d = e.to_dict()
        assert "intent_id" in d
        assert "category" in d
        assert "reason" in d
        assert "source" in d
        assert "timestamp" in d
        assert d["category"] == "INVALID_TRANSITION"


# ═══════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # Back-compat
        ("All layers unchanged", test_all_layers_unchanged),
        # Structure
        ("Registry: instantiable", test_registry_instantiable),
        ("BlockRecord: structure", test_block_record_structure),
        ("BlockCategory: defined", test_block_categories_defined),
        # Record methods
        ("Record: OUT_OF_SCOPE", test_record_out_of_scope),
        ("Record: UNSUPPORTED_DOMAIN", test_record_unsupported_domain),
        ("Record: UNRECOGNIZED", test_record_unrecognized),
        ("Record: from_pm", test_record_from_pm),
        ("Record: from_gate rejected", test_record_from_gate_rejected),
        ("Record: multiple categories", test_record_multiple_categories),
        # Query methods
        ("Query: get_all", test_get_all),
        ("Query: get_by_category", test_get_by_category),
        ("Query: get_by_id", test_get_by_id),
        ("Query: get_by_id missing", test_get_by_id_missing),
        ("Query: count_by_category", test_count_by_category),
        ("Query: categories_present", test_categories_present),
        # Dismissal
        ("Dismiss: by id", test_dismiss_by_id),
        ("Dismiss: missing", test_dismiss_missing),
        ("Dismiss: by category", test_dismiss_by_category),
        ("Dismiss: clear", test_clear),
        # handle_blocked_result
        ("handle: no registry", test_handle_blocked_no_registry),
        ("handle: PM blocked", test_handle_blocked_pm),
        ("handle: gate rejected", test_handle_blocked_gate_rejected),
        ("handle: Micro1", test_handle_blocked_micro1),
        ("handle: unrecognized", test_handle_blocked_unrecognized),
        # Pipeline integration
        ("DL pipeline: archive (clean)", test_dl_pipeline_archive),
        ("DL pipeline: intake (clean)", test_dl_pipeline_intake),
        ("DL pipeline: Micro1 blocked", test_dl_pipeline_micro1_blocked),
        ("DL pipeline: unrecognized", test_dl_pipeline_unrecognized),
        ("DL pipeline: implementation awaiting", test_dl_pipeline_implementation_blocked),
        ("DL pipeline: shared registry", test_dl_pipeline_shared_registry),
        # No auto-recovery
        ("No auto-recovery", test_no_auto_recovery),
        ("DL explicit + inspectable", test_dl_explicit_inspectable),
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
