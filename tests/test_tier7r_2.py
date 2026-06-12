"""
7R.2 acceptance tests — CISAdapter (CIS domain only).

Tests the content-based router + CISAdapter pipeline:
classify_domain_router → CISAdapter.classify_intent →
CISAdapter.validate_state → CISAdapter.resolve_objects →
CISAdapter.stage_candidates

Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.3 and §8.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.scope_registry import Domain, classify_domain, is_out_of_scope
from runtime.tier7r.adapters import get_adapter, is_cis_domain, CIS_DOMAIN_KEYWORDS
from runtime.tier7r.adapters.cis_adapter import CISAdapter
from runtime.tier7r.classifier import (
    classify,
    classify_domain_router,
    classify_full,
    classify_with_candidates,
)


# ═══════════════════════════════════════════════════
# 7R.1 back-compat tests
# ═══════════════════════════════════════════════════

def test_7r1_classify_still_works():
    """classify() still rejects Micro1 (backward compat)."""
    wi = classify("Start Micro1 task planning")
    assert wi.domain == "OUT_OF_SCOPE"
    assert wi.status == "BLOCKED"


def test_7r1_classify_passthrough():
    """classify() still returns domain='' for unclassified prompts (backward compat)."""
    wi = classify("What did I say about the social worker app?")
    assert wi.domain == ""


# ═══════════════════════════════════════════════════
# Domain Router tests
# ═══════════════════════════════════════════════════

def test_router_micro1_rejected():
    """classify_domain_router() rejects Micro1 as OUT_OF_SCOPE."""
    assert classify_domain_router("Start Micro1 task planning") == "OUT_OF_SCOPE"


def test_router_cis_detected_archive():
    """CIS archive/session recall prompts detected."""
    assert classify_domain_router("What did I say about the social worker app?") == "CIS"


def test_router_cis_detected_intake():
    """CIS knowledge intake prompts detected."""
    assert classify_domain_router("Process this PDF into a knowledge record") == "CIS"


def test_router_cis_detected_retrieval():
    """CIS knowledge retrieval prompts detected."""
    assert classify_domain_router("Find everything about cloth simulation in Houdini") == "CIS"


def test_router_cis_detected_recovery():
    """CIS requirements recovery prompts detected."""
    assert classify_domain_router("Use this document to identify what the app needs") == "CIS"


def test_router_cis_detected_implement():
    """CIS implementation directive prompts detected."""
    assert classify_domain_router("Implement Phase 45") == "CIS"


def test_router_unrecognized_passthrough():
    """Non-CIS, non-Micro1 prompts return empty string."""
    result = classify_domain_router("What's the weather?")
    assert result == ""


def test_router_micro1_case_insensitive():
    """Micro1 detection is case-insensitive."""
    assert classify_domain_router("lets work on MICRO1 stuff") == "OUT_OF_SCOPE"


# ═══════════════════════════════════════════════════
# CISAdapter.classify_intent tests
# ═══════════════════════════════════════════════════

def _mk_cis_intent(prompt: str) -> WorkIntent:
    """Create a WorkIntent for CIS adapter testing."""
    wi = WorkIntent(domain="CIS", source_raw=prompt, source_type="prompt")
    return wi


def test_cis_adapter_exists():
    """CISAdapter is registered and instantiable."""
    adapter = get_adapter("CIS")
    assert adapter is not None
    assert isinstance(adapter, CISAdapter)
    assert adapter.domain == "CIS"


def test_cis_adapter_archive_discovery():
    """C2: ARCHIVE_DISCOVERY → retrieve, no mutation."""
    adapter = get_adapter("CIS")
    wi = _mk_cis_intent("What did I say about the social worker app in past sessions?")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "ARCHIVE_DISCOVERY"
    assert result.allowed_action == "retrieve"
    assert result.requires_eric_gate == False
    assert result.status == "CLASSIFIED"


def test_cis_adapter_knowledge_intake():
    """C1: KNOWLEDGE_INTAKE → stage_candidate."""
    adapter = get_adapter("CIS")
    wi = _mk_cis_intent("Process this PDF into a knowledge record")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "KNOWLEDGE_INTAKE"
    assert result.object_type == "source_manifest"
    assert result.allowed_action == "stage_candidate"
    assert result.status == "CLASSIFIED"


def test_cis_adapter_knowledge_intake_with_evidence():
    """C1: KNOWLEDGE_INTAKE with file evidence → object_refs populated."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(
        domain="CIS",
        source_raw="Process this PDF into a knowledge record",
        source_type="prompt",
        evidence_refs=["/path/to/doc.pdf"],
    )
    result = adapter.classify_intent(wi)
    assert result.intent_class == "KNOWLEDGE_INTAKE"
    # Evidence refs moved to object_refs by resolve_objects
    assert result.evidence_refs == ["/path/to/doc.pdf"]


def test_cis_adapter_knowledge_retrieval():
    """C6: KNOWLEDGE_RETRIEVAL → retrieve."""
    adapter = get_adapter("CIS")
    wi = _mk_cis_intent("Find everything about cloth simulation in Houdini")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "KNOWLEDGE_RETRIEVAL"
    assert result.allowed_action == "retrieve"
    assert result.requires_eric_gate == False


def test_cis_adapter_requirements_recovery():
    """C3: REQUIREMENTS_RECOVERY → stage_candidate."""
    adapter = get_adapter("CIS")
    wi = _mk_cis_intent("Use this SWA document to identify what the app needs")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "REQUIREMENTS_RECOVERY"
    assert result.object_type == "build_plan_node"
    assert result.allowed_action == "stage_candidate"
    assert result.status == "CLASSIFIED"


def test_cis_adapter_implementation_directive():
    """C4: IMPLEMENTATION_DIRECTIVE → request_approval, eric_gate=true."""
    adapter = get_adapter("CIS")
    wi = _mk_cis_intent("Implement Phase 45")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "IMPLEMENTATION_DIRECTIVE"
    assert result.object_type == "build_plan_node"
    assert result.allowed_action == "request_approval"
    assert result.requires_eric_gate == True
    assert result.status == "CLASSIFIED"


def test_cis_adapter_unrecognized():
    """C5: Unrecognized CIS prompt → BLOCKED."""
    adapter = get_adapter("CIS")
    wi = _mk_cis_intent("something completely unrelated to any known intent")
    result = adapter.classify_intent(wi)
    assert result.intent_class == "BLOCKED_MISSING_CAPABILITY"
    assert result.allowed_action == "block"
    assert result.status == "BLOCKED"


# ═══════════════════════════════════════════════════
# CISAdapter.validate_state tests
# ═══════════════════════════════════════════════════

def test_validate_archive_discovery():
    """ARCHIVE_DISCOVERY → workflow_state=N/A, retrieve only."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="ARCHIVE_DISCOVERY")
    result = adapter.validate_state(wi)
    assert result.workflow_state == "N/A"
    assert result.allowed_action == "retrieve"


def test_validate_knowledge_intake():
    """KNOWLEDGE_INTAKE → workflow_state=arrived."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="KNOWLEDGE_INTAKE")
    result = adapter.validate_state(wi)
    assert result.workflow_state == "arrived"
    assert result.allowed_action == "stage_candidate"


def test_validate_knowledge_retrieval():
    """KNOWLEDGE_RETRIEVAL → workflow_state=N/A."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="KNOWLEDGE_RETRIEVAL")
    result = adapter.validate_state(wi)
    assert result.workflow_state == "N/A"
    assert result.allowed_action == "retrieve"


def test_validate_requirements_recovery():
    """REQUIREMENTS_RECOVERY → workflow_state=draft."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="REQUIREMENTS_RECOVERY")
    result = adapter.validate_state(wi)
    assert result.workflow_state == "draft"


def test_validate_implementation_directive():
    """IMPLEMENTATION_DIRECTIVE → workflow_state=PENDING, eric_gate=true."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="IMPLEMENTATION_DIRECTIVE")
    result = adapter.validate_state(wi)
    assert result.workflow_state == "PENDING"
    assert result.allowed_action == "request_approval"
    assert result.requires_eric_gate == True


def test_validate_blocked():
    """BLOCKED → status remains BLOCKED."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="BLOCKED_MISSING_CAPABILITY", status="BLOCKED")
    result = adapter.validate_state(wi)
    assert result.allowed_action == "block"
    assert result.status == "BLOCKED"


# ═══════════════════════════════════════════════════
# CISAdapter.stage_candidates tests
# ═══════════════════════════════════════════════════

def test_stage_knowledge_intake():
    """Stage source_manifest + knowledge_record for KNOWLEDGE_INTAKE."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(
        domain="CIS",
        intent_class="KNOWLEDGE_INTAKE",
        source_raw="Process PDF into knowledge record",
        evidence_refs=["/tmp/doc.pdf"],
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 2
    # First candidate should be source_manifest
    sm = candidates[0]
    assert sm.object_type == "source_manifest"
    assert sm.status == "STAGED"
    assert sm.domain == "CIS"
    # Second candidate should be knowledge_record
    kr = candidates[1]
    assert kr.object_type == "knowledge_record"
    assert kr.status == "STAGED"
    assert kr.domain == "CIS"


def test_stage_requirements_recovery():
    """Stage build_plan_node candidate for REQUIREMENTS_RECOVERY."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(
        domain="CIS",
        intent_class="REQUIREMENTS_RECOVERY",
        source_raw="Analyze doc for requirements",
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 1
    assert candidates[0].object_type == "build_plan_node"
    assert candidates[0].status == "STAGED"
    assert candidates[0].requires_eric_gate == True


def test_stage_implementation_directive():
    """Stage for Eric Gate approval for IMPLEMENTATION_DIRECTIVE."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(
        domain="CIS",
        intent_class="IMPLEMENTATION_DIRECTIVE",
        source_raw="Implement Phase 45",
    )
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 1
    assert candidates[0].object_type == "build_plan_node"
    assert candidates[0].status == "STAGED"
    assert candidates[0].requires_eric_gate == True
    assert candidates[0].allowed_action == "request_approval"


def test_stage_archive_discovery_no_candidates():
    """ARCHIVE_DISCOVERY produces zero candidates (read-only)."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="ARCHIVE_DISCOVERY")
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 0


def test_stage_knowledge_retrieval_no_candidates():
    """KNOWLEDGE_RETRIEVAL produces zero candidates (read-only)."""
    adapter = get_adapter("CIS")
    wi = WorkIntent(domain="CIS", intent_class="KNOWLEDGE_RETRIEVAL")
    candidates = adapter.stage_candidates(wi)
    assert len(candidates) == 0


# ═══════════════════════════════════════════════════
# classify_full pipeline tests (end-to-end)
# ═══════════════════════════════════════════════════

def test_full_micro1_blocked():
    """classify_full() → Micro1 blocked."""
    wi = classify_full("Start Micro1 task planning")
    assert wi.domain == "OUT_OF_SCOPE"
    assert wi.intent_class == "BLOCKED_MISSING_CAPABILITY"
    assert wi.allowed_action == "block"
    assert wi.status == "BLOCKED"


def test_full_archive_discovery():
    """classify_full() → archive discovery pipeline."""
    wi = classify_full("What did I say about the social worker app in past sessions?")
    assert wi.domain == "CIS"
    assert wi.intent_class == "ARCHIVE_DISCOVERY"
    assert wi.allowed_action == "retrieve"
    assert wi.requires_eric_gate == False
    assert wi.status == "CLASSIFIED"
    assert wi.workflow_state == "N/A"


def test_full_knowledge_intake():
    """classify_full() → knowledge intake pipeline."""
    wi = classify_full("Process this PDF into a knowledge record")
    assert wi.domain == "CIS"
    assert wi.intent_class == "KNOWLEDGE_INTAKE"
    assert wi.object_type == "source_manifest"
    assert wi.allowed_action == "stage_candidate"
    assert wi.workflow_state == "arrived"
    assert wi.status == "CLASSIFIED"


def test_full_knowledge_retrieval():
    """classify_full() → knowledge retrieval pipeline."""
    wi = classify_full("Find everything about cloth simulation in Houdini")
    assert wi.domain == "CIS"
    assert wi.intent_class == "KNOWLEDGE_RETRIEVAL"
    assert wi.allowed_action == "retrieve"
    assert wi.workflow_state == "N/A"


def test_full_requirements_recovery():
    """classify_full() → requirements recovery pipeline."""
    wi = classify_full("Use this document to identify what the app needs")
    assert wi.domain == "CIS"
    assert wi.intent_class == "REQUIREMENTS_RECOVERY"
    assert wi.object_type == "build_plan_node"
    assert wi.allowed_action == "stage_candidate"
    assert wi.workflow_state == "draft"


def test_full_implementation_directive():
    """classify_full() → implementation directive pipeline (blocked without gate)."""
    wi = classify_full("Implement Phase 45")
    assert wi.domain == "CIS"
    assert wi.intent_class == "IMPLEMENTATION_DIRECTIVE"
    assert wi.object_type == "build_plan_node"
    assert wi.allowed_action == "request_approval"
    assert wi.requires_eric_gate == True
    assert wi.workflow_state == "PENDING"


def test_full_unrecognized():
    """classify_full() → unrecognized prompt returns domain=''."""
    wi = classify_full("What is the capital of France?")
    assert wi.domain == ""
    assert wi.status is None  # not classified, not blocked


# ═══════════════════════════════════════════════════
# classify_with_candidates tests
# ═══════════════════════════════════════════════════

def test_with_candidates_intake():
    """classify_with_candidates() → 2 candidates for intake."""
    intent, candidates = classify_with_candidates("Process this PDF into a knowledge record")
    assert intent.intent_class == "KNOWLEDGE_INTAKE"
    assert len(candidates) == 2
    assert all(c.status == "STAGED" for c in candidates)


def test_with_candidates_archive():
    """classify_with_candidates() → 0 candidates for archive (read-only)."""
    intent, candidates = classify_with_candidates(
        "What did I say about the social worker app in past sessions?"
    )
    assert intent.intent_class == "ARCHIVE_DISCOVERY"
    assert len(candidates) == 0


def test_with_candidates_implement():
    """classify_with_candidates() → 1 candidate for implementation."""
    intent, candidates = classify_with_candidates("Implement Phase 45")
    assert intent.intent_class == "IMPLEMENTATION_DIRECTIVE"
    assert len(candidates) == 1
    assert candidates[0].requires_eric_gate == True


def test_with_candidates_micro1():
    """classify_with_candidates() → 0 candidates for Micro1 (blocked)."""
    intent, candidates = classify_with_candidates("Start Micro1 task planning")
    assert intent.domain == "OUT_OF_SCOPE"
    assert intent.status == "BLOCKED"
    assert len(candidates) == 0


# ═══════════════════════════════════════════════════
# Spec acceptance tests (from docs §8)
# ═══════════════════════════════════════════════════

def test_spec_8_3_cis_knowledge_intake():
    """
    §8.3: CIS File-to-Knowledge Pipeline
    Input: "Process this PDF into a knowledge record"
    Expected: CIS, KNOWLEDGE_INTAKE, source_manifest, arrived,
              stage_candidate, requires_eric_gate=false
    """
    wi = classify_full("Process this PDF into a knowledge record",
                       evidence_refs=["/docs/somefile.pdf"])
    assert wi.domain == "CIS"
    assert wi.intent_class == "KNOWLEDGE_INTAKE"
    assert wi.object_type == "source_manifest"
    assert wi.workflow_state == "arrived"
    assert wi.allowed_action == "stage_candidate"
    assert wi.requires_eric_gate == False


def test_spec_8_4_archive_discovery():
    """
    §8.4: Archive Discovery
    Input: "What did I say about the social worker app in past sessions?"
    Expected: CIS, ARCHIVE_DISCOVERY, session_record, N/A, retrieve,
              requires_eric_gate=false, no build_plan_nodes
    """
    intent, candidates = classify_with_candidates(
        "What did I say about the social worker app in past sessions?"
    )
    assert intent.domain == "CIS"
    assert intent.intent_class == "ARCHIVE_DISCOVERY"
    assert intent.object_type == "session_record"
    assert intent.workflow_state == "N/A"
    assert intent.allowed_action == "retrieve"
    assert intent.requires_eric_gate == False
    assert len(candidates) == 0  # no build_plan_nodes created


def test_spec_8_6_implementation_blocked():
    """
    §8.6: Implementation Directive (blocked without Eric Gate)
    Input: "Implement Phase 45"
    Expected: CIS, IMPLEMENTATION_DIRECTIVE, request_approval,
              requires_eric_gate=true, staged candidate with eric_gate
    """
    intent, candidates = classify_with_candidates("Implement Phase 45")
    assert intent.domain == "CIS"
    assert intent.intent_class == "IMPLEMENTATION_DIRECTIVE"
    assert intent.allowed_action == "request_approval"
    assert intent.requires_eric_gate == True
    assert len(candidates) == 1
    assert candidates[0].requires_eric_gate == True
    assert candidates[0].allowed_action == "request_approval"


# ═══════════════════════════════════════════════════
# Scope boundary tests
# ═══════════════════════════════════════════════════

def test_no_swa_touch():
    """CISAdapter does not reference the SWA codebase."""
    import importlib
    for module_name in [
        "runtime.tier7r.adapters",
        "runtime.tier7r.adapters.cis_adapter",
        "runtime.tier7r.classifier",
    ]:
        mod = importlib.import_module(module_name)
        src = str(getattr(mod, "__file__", ""))
        with open(src) as f:
            content = f.read()
        assert "/mnt/projects/swa/" not in content, \
            f"{module_name} references SWA codebase"


def test_no_micro1_in_scope():
    """Micro1 is never classified as CIS."""
    assert not is_cis_domain("Start Micro1 task planning")
    assert not is_cis_domain("work on micro1 stuff")


def test_cis_domain_keywords_are_non_empty():
    """CIS_DOMAIN_KEYWORDS list is populated."""
    assert len(CIS_DOMAIN_KEYWORDS) > 0


# ═══════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # 7R.1 back-compat
        ("7R.1 classify() still rejects Micro1", test_7r1_classify_still_works),
        ("7R.1 classify() passthrough", test_7r1_classify_passthrough),
        # Domain router
        ("Router: Micro1 rejected", test_router_micro1_rejected),
        ("Router: CIS detected (archive)", test_router_cis_detected_archive),
        ("Router: CIS detected (intake)", test_router_cis_detected_intake),
        ("Router: CIS detected (retrieval)", test_router_cis_detected_retrieval),
        ("Router: CIS detected (recovery)", test_router_cis_detected_recovery),
        ("Router: CIS detected (implement)", test_router_cis_detected_implement),
        ("Router: unrecognized passthrough", test_router_unrecognized_passthrough),
        ("Router: Micro1 case-insensitive", test_router_micro1_case_insensitive),
        # CISAdapter existence
        ("CISAdapter: registered + instantiable", test_cis_adapter_exists),
        # classify_intent
        ("Classify: ARCHIVE_DISCOVERY", test_cis_adapter_archive_discovery),
        ("Classify: KNOWLEDGE_INTAKE", test_cis_adapter_knowledge_intake),
        ("Classify: KNOWLEDGE_INTAKE + evidence", test_cis_adapter_knowledge_intake_with_evidence),
        ("Classify: KNOWLEDGE_RETRIEVAL", test_cis_adapter_knowledge_retrieval),
        ("Classify: REQUIREMENTS_RECOVERY", test_cis_adapter_requirements_recovery),
        ("Classify: IMPLEMENTATION_DIRECTIVE", test_cis_adapter_implementation_directive),
        ("Classify: unrecognized → BLOCKED", test_cis_adapter_unrecognized),
        # validate_state
        ("Validate: ARCHIVE_DISCOVERY → N/A", test_validate_archive_discovery),
        ("Validate: KNOWLEDGE_INTAKE → arrived", test_validate_knowledge_intake),
        ("Validate: KNOWLEDGE_RETRIEVAL → N/A", test_validate_knowledge_retrieval),
        ("Validate: REQUIREMENTS_RECOVERY → draft", test_validate_requirements_recovery),
        ("Validate: IMPLEMENTATION → PENDING", test_validate_implementation_directive),
        ("Validate: BLOCKED → block", test_validate_blocked),
        # stage_candidates
        ("Stage: intake → 2 candidates", test_stage_knowledge_intake),
        ("Stage: recovery → 1 candidate", test_stage_requirements_recovery),
        ("Stage: implement → 1 candidate", test_stage_implementation_directive),
        ("Stage: archive → 0 candidates", test_stage_archive_discovery_no_candidates),
        ("Stage: retrieval → 0 candidates", test_stage_knowledge_retrieval_no_candidates),
        # classify_full pipeline (end-to-end)
        ("Full: Micro1 blocked", test_full_micro1_blocked),
        ("Full: archive discovery", test_full_archive_discovery),
        ("Full: knowledge intake", test_full_knowledge_intake),
        ("Full: knowledge retrieval", test_full_knowledge_retrieval),
        ("Full: requirements recovery", test_full_requirements_recovery),
        ("Full: implementation directive", test_full_implementation_directive),
        ("Full: unrecognized passthrough", test_full_unrecognized),
        # classify_with_candidates
        ("Candidates: intake", test_with_candidates_intake),
        ("Candidates: archive (0)", test_with_candidates_archive),
        ("Candidates: implement", test_with_candidates_implement),
        ("Candidates: Micro1 (0)", test_with_candidates_micro1),
        # Spec acceptance tests
        ("Spec §8.3: CIS knowledge intake", test_spec_8_3_cis_knowledge_intake),
        ("Spec §8.4: Archive discovery", test_spec_8_4_archive_discovery),
        ("Spec §8.6: Implementation blocked", test_spec_8_6_implementation_blocked),
        # Scope boundary
        ("Scope: no SWA codebase touch", test_no_swa_touch),
        ("Scope: Micro1 not in CIS", test_no_micro1_in_scope),
        ("Scope: CIS keywords populated", test_cis_domain_keywords_are_non_empty),
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
