"""
7R.1 acceptance tests — WorkIntent schema + scope registry + Micro1 exclusion.
Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §8.5 and §11.2.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.tier7r.work_intent import WorkIntent
from runtime.tier7r.scope_registry import (
    Domain,
    IN_SCOPE,
    OUT_OF_SCOPE_LIST,
    classify_domain,
    is_out_of_scope,
    is_in_scope,
)
from runtime.tier7r.domain_adapter import DomainAdapter
from runtime.tier7r.classifier import classify


# ── Test 1: WorkIntent dataclass ──

def test_workintent_construction():
    """WorkIntent can be constructed with minimal fields."""
    wi = WorkIntent(domain="CIS")
    assert wi.domain == "CIS"
    assert wi.intent_class is None
    assert wi.object_refs == []
    assert wi.evidence_refs == []
    assert wi.status is None  # not set for in-scope domains


def test_workintent_out_of_scope_auto_status():
    """OUT_OF_SCOPE domain auto-sets status=BLOCKED."""
    wi = WorkIntent(domain="OUT_OF_SCOPE")
    assert wi.status == "BLOCKED"


def test_workintent_to_dict():
    """to_dict() serializes all fields."""
    wi = WorkIntent(domain="CIS", intent_class="ARCHIVE_DISCOVERY",
                    source_raw="find my notes", source_type="prompt")
    d = wi.to_dict()
    assert d["domain"] == "CIS"
    assert d["intent_class"] == "ARCHIVE_DISCOVERY"
    assert d["source_raw"] == "find my notes"


# ── Test 2: Scope registry ──

def test_scope_registry_in_scope():
    """CIS, SWA, WIAS are in scope."""
    assert is_in_scope("CIS")
    assert is_in_scope("SWA")
    assert is_in_scope("WIAS")


def test_scope_registry_out_of_scope():
    """Micro1 is in OUT_OF_SCOPE_LIST."""
    assert "Micro1" in OUT_OF_SCOPE_LIST
    assert not is_in_scope("OUT_OF_SCOPE")


def test_scope_registry_unknown():
    """Unknown domains are not in scope."""
    assert not is_in_scope("BOGUS")


# ── Test 3: Micro1 rejection ──

def test_micro1_rejected_direct():
    """'Start Micro1 task planning' → OUT_OF_SCOPE."""
    prompt = "Start Micro1 task planning"
    domain = classify_domain(prompt)
    assert domain == "OUT_OF_SCOPE"
    assert is_out_of_scope(domain)


def test_micro1_rejected_case_insensitive():
    """'micro1' case-insensitive match."""
    prompt = "let's work on micro1 stuff"
    domain = classify_domain(prompt)
    assert domain == "OUT_OF_SCOPE"


def test_micro1_classifier_workintent():
    """Classifier returns BLOCKED WorkIntent for Micro1."""
    wi = classify("Start Micro1 task planning")
    assert wi.domain == "OUT_OF_SCOPE"
    assert wi.intent_class == "BLOCKED_MISSING_CAPABILITY"
    assert wi.allowed_action == "block"
    assert wi.status == "BLOCKED"


# ── Test 4: Unclassified passthrough ──

def test_unclassified_passthrough():
    """Non-Micro1 prompts pass through unclassified (deferred to 7R.2+)."""
    prompt = "What did I say about the social worker app?"
    wi = classify(prompt)
    assert wi.domain == ""  # unclassified — domain adapters handle in 7R.2+
    assert wi.source_raw == prompt
    assert wi.source_type == "prompt"
    assert wi.allowed_action is None  # not classified yet


def test_cis_prompt_not_classified_yet():
    """CIS prompts are not classified in 7R.1 (deferred)."""
    wi = classify("Process this PDF into a knowledge record")
    assert wi.domain == ""  # unclassified


# ── Test 5: DomainAdapter ABC ──

def test_domain_adapter_is_abstract():
    """DomainAdapter cannot be instantiated directly."""
    try:
        DomainAdapter()  # type: ignore
        assert False, "Should have raised TypeError"
    except TypeError:
        pass  # Expected — ABC with abstract methods


# ── Test 6: Verify no SWA codebase touched ──

def test_no_swa_codebase_touch():
    """7R.1 does not import or reference the SWA project."""
    import importlib
    for module_name in ["runtime.tier7r.work_intent",
                         "runtime.tier7r.scope_registry",
                         "runtime.tier7r.classifier",
                         "runtime.tier7r.domain_adapter"]:
        mod = importlib.import_module(module_name)
        src = str(getattr(mod, "__file__", ""))
        # Read source to verify no SWA path reference
        with open(src) as f:
            content = f.read()
        assert "/mnt/projects/swa/" not in content, \
            f"{module_name} references SWA codebase"


# ── Runner ──

if __name__ == "__main__":
    tests = [
        ("WorkIntent construction", test_workintent_construction),
        ("WorkIntent OUT_OF_SCOPE auto-status", test_workintent_out_of_scope_auto_status),
        ("WorkIntent to_dict", test_workintent_to_dict),
        ("Scope registry in-scope", test_scope_registry_in_scope),
        ("Scope registry out-of-scope", test_scope_registry_out_of_scope),
        ("Scope registry unknown", test_scope_registry_unknown),
        ("Micro1 rejected (direct)", test_micro1_rejected_direct),
        ("Micro1 rejected (case-insensitive)", test_micro1_rejected_case_insensitive),
        ("Micro1 classifier WorkIntent", test_micro1_classifier_workintent),
        ("Unclassified passthrough", test_unclassified_passthrough),
        ("CIS prompt not classified yet", test_cis_prompt_not_classified_yet),
        ("DomainAdapter is abstract", test_domain_adapter_is_abstract),
        ("No SWA codebase touch", test_no_swa_codebase_touch),
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
