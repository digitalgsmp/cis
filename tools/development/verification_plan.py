#!/usr/bin/env python3
"""verification_plan.py — incremental verification and evidence reuse for
external development (card XDEV-VERIFY-01).

WHAT THIS IS. One read-only derivation that answers, for the work in front
of the developer right now:

    A. which previously established verification results are still valid
    B. which new checks the changed behaviour actually requires
    C. which gates run regardless of any reuse
    D. which earlier results cannot safely be carried forward
    E. whether the current pushed commit still needs independent acceptance

WHAT THIS IS NOT, and why that matters more than what it is:

- NOT a second workflow controller. It starts nothing, gates nothing, and
  decides no stage transition. `discovery.check_closeout` remains the only
  closeout gate and `close_task` the only sanctioned closeout path.
- NOT a second evidence store. Every item it reports is read from
  `project_state.external_dev_checkpoint` (acceptance authority, ADR-XDEV-001)
  or `dev_continuity_events` (during-work record). `build_plan()` executes no
  SQL write and no `publish_event`, so asking for a plan — however many times
  — can never create a duplicate result record.
- NOT a second verification authority. It reports what an existing authority
  already established, together with WHO established it. The implementing
  developer's own verification is carried as `authority:
  "implementing_developer"` and `is_independent_acceptance: false`,
  permanently. Nothing in this module can promote a pushed commit to
  accepted; only the authorized independent reviewer reading the GitHub
  remote can, which is exactly what ADR-XDEV-001 says and exactly what the
  agent that pushed the commit cannot do for itself.
- NOT a dependency graph, and NOT a maintained test registry. Card section 7
  forbids both. Test selection is DERIVED from the repository's own layout
  (`derive_test_map`, which reads `git ls-files`): the component that owns a
  changed file is the nearest ancestor directory that actually contains
  tests. When that cannot be established the answer is "undetermined", and
  undetermined always widens verification rather than narrowing it.

  AND THAT DERIVATION ANSWERS ONE QUESTION ONLY: which tests live with a
  changed file. It does not — and structurally cannot — say which OTHER
  components depend on that file. Directory layout records no dependency
  edges, so a changed file having a nearby test directory is never treated
  here as proof that the full set of affected components is known. That
  second question is reported separately and explicitly, as
  `changed_scope.dependency_impact`; see the dependency-impact section below.

THE REUSE RULE (card section 3). A prior result is reused only when all five
hold, each checked explicitly and reported per item in `validity_checks`:

    1. its source and verification authority are identifiable
    2. its tested commit/artifact identity is known AND resolvable here
    3. it has not been superseded or invalidated
    4. this task does not change the behaviour or dependencies it covers
    5. no mandatory policy requires fresh execution

Condition 4 is the one that is easy to fake. It is answered from the actual
changed files, not from "the last task said PASS", and it fails closed in
two independent directions:

  - if ANY changed file's owning component cannot be determined, component
    ownership is unresolved and every item is invalidated with that reason;
  - and even when every owner IS resolved, non-overlap with the changed
    components is NOT by itself a reason to reuse. Reuse additionally
    requires that cross-component dependency impact be established — which
    directory structure cannot do (see below). Where it is not established,
    the result is invalidated, verification widens, and the uncertainty is
    stated in `limitations`.

A changed SHA alone still does not invalidate everything: a documentation
commit changes no behaviour any component can depend on, so component test
evidence survives it. Executable change is the case where the honest answer
is "the affected set is not known".

AND CONDITION 4 IS MEASURED FROM THE EVIDENCE, NOT FROM THE BASELINE (card
XDEV-VERIFY-01D). "Is this result still valid" is a question about what has
changed since the result was MEASURED, so the delta condition 4 reads runs
from the item's own `tested_identity` to the state under verification — HEAD
plus the working tree. Anchoring it at the accepted baseline instead was a
defect in both directions: it invalidated evidence measured at the very state
under review, and — once the baseline advanced to that state — it reused
evidence measured against EARLIER implementations as proof of the new one.
The second direction was demonstrated against this module itself, so the
regression is asserted on it. What is REQUIRED is still derived from the
accepted-baseline scope, because the unit an independent reviewer accepts is
the whole unaccepted delta (ADR-XDEV-001), not the increment since a
developer's last test run. See the evidence-currency section below.

WHY THIS IS NOT FOLDED INTO AN EXISTING MODULE. Three near misses, each
rejected for a concrete reason:
  - `packet.py` binds and freshness-checks CONTEXT (queue row, KB rows, file
    evidence). It knows nothing about commits, gates or acceptance, and its
    `check_freshness` contract is "did my inputs move", not "what must I
    verify".
  - `discovery.py` is the closeout gate. Its output is blockers, and the card
    explicitly says not to turn this into another approval hierarchy.
  - `tools/state/build_path.py` is a read-only DISPLAY model for one Workbench
    card and is forbidden by its own contract from doing anything else.
This module is consumed by all three surfaces rather than duplicated into
them: `packet.prepare_packet` carries it at task start, the dev CLI exposes
it, and `tools/state/recovery_packet.py` carries the baseline/pending-review
half of it through the recovery path so a fresh session after `/clear` is
handed the verification baseline instead of re-deriving it.

A NOTE ON THE PENDING EVIDENCE-CLASSIFICATION CORRECTION (card section 11).
That correction concerns one inconsistency in `config/kb_source_policy.yaml`:
the SAME external-development handoff material is classified differently
depending on which root retrieval reaches it through. The local copies under
`data/agent_handoffs/` enter the KB as the `external_dev_handoffs` family and
are classified `authority_class: evidence`; the curated, remotely durable
copies of the same handoffs under `docs/review_packets/<PACKET>/` enter
through the `repository_docs` family, which is classified `authority_class:
mixed`. Local staging and remote durability are the existing convention for
one artifact — `data/agent_handoffs/` is machine-local (.gitignore excludes
/data/*), so a handoff that must survive loss of the VM gets a tracked copy
under docs/ — but the two classifications are not the same claim about how
retrieval should treat it.

This module does not touch that correction and cannot relax it: KB source
coverage is listed in `MANDATORY_CHECKS`, is therefore never reusable under
condition 5, and continues to be enforced where it already was, inside
`discovery._kb_coverage_blockers`. The two tasks stay separate by
construction, not by convention. (Nothing here implements or prejudges the
correction; XDEV-VERIFY-01A forbids that, and the classification decision is
not this module's to make.)
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone

from . import continuity_store as cs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PLAN_KIND = "cis_incremental_verification_plan"
HANDOFF_KIND = "cis_external_review_handoff"
CHECKPOINT_KEY = "external_dev_checkpoint"

AUTHORITY_NOTE = (
    "Acceptance authority: ADR-XDEV-001 (external-developer work is not durable "
    "until independently verified from the remote). Visibility requirement: "
    "ADR-XDEV-002. Evidence sources: project_state.external_dev_checkpoint and "
    "dev_continuity_events. This plan is a projection of those records; it is "
    "not an authority and records nothing."
)

# Cap on how many paths are listed verbatim before the plan reports a count
# instead. Truncation is always reported, never silent.
_MAX_LISTED = 120

# How many of a task's most recent verified_result events are considered as
# reuse candidates. Bounded so the plan stays a readable projection.
_EVENT_SCAN_LIMIT = 25


# ── mandatory gates (card section 4C / section 6) ────────────────────────
#
# These are not a new policy. They are the checks this repository ALREADY
# runs unconditionally — the pre-commit hook runs the export generator and
# gate_export_agreement.sh on every commit, and closeout-check already calls
# the KB coverage gate. Listing them here makes "runs regardless of reuse"
# machine-readable instead of something a developer has to remember, and
# pins them out of reuse via condition 5.

MANDATORY_CHECKS = (
    {
        "id": "gate_export_agreement",
        "command": "tools/gates/gate_export_agreement.sh",
        "when": "every_commit",
        "why": "run by .git/hooks/pre-commit on every commit. A generated "
               "projection disagreeing with the spine is a repository-wide "
               "fact, not a property of the files this task changed.",
    },
    {
        "id": "gate_no_secrets",
        "command": "tools/gates/gate_no_secrets.sh",
        "when": "every_commit",
        "why": "secret exposure is not scoped to the changed component, and a "
               "clean scan at an earlier SHA proves nothing about this index.",
    },
    {
        "id": "gate_build_state_coherence",
        "command": "tools/gates/gate_build_state_coherence.py",
        "when": "every_commit",
        "why": "build-state coherence is derived from the spine, which changes "
               "independently of the worktree.",
    },
    {
        "id": "kb_source_coverage_closeout",
        "command": "python3 -m tools.development.cli closeout-check <task>",
        "when": "every_closeout",
        "why": "already enforced inside the existing closeout gate "
               "(discovery._kb_coverage_blockers), repository-scoped rather "
               "than task-scoped. The inconsistent authority_class of the "
               "external-development handoffs (evidence under "
               "data/agent_handoffs, mixed where the same packets are reached "
               "through repository_docs under docs/review_packets) is the "
               "subject of a separate pending evidence-classification "
               "correction, so this check is never reused and never relaxed "
               "here.",
    },
    {
        "id": "git_push_confirmation",
        "command": "git rev-parse HEAD && git ls-remote origin <branch>",
        "when": "per_new_push",
        "why": "card section 6: a normal push still needs proof that the "
               "intended commit reached the remote. Required once for each new "
               "push; NOT repeated at later stages when the durable record "
               "already establishes the same fact for the same SHA and no new "
               "push has occurred.",
    },
)

MANDATORY_CHECK_IDS = frozenset(c["id"] for c in MANDATORY_CHECKS)


# ── security-sensitive classification (card section 7) ───────────────────
#
# Path patterns, deliberately over-inclusive. Every rule here can only ADD
# required verification depth and REMOVE reuse permission, so a false
# positive costs test time and a false negative would cost safety. That
# asymmetry is why these are matched loosely (a file named `tokenizer.py`
# matching `token` is an acceptable outcome; a credential path that slipped
# through is not).

SECURITY_SENSITIVE_RULES = (
    (r"^runtime/schema/migrations/", "schema_migration"),
    (r"(^|/)(auth|authz|oidc|oauth|login|session_auth)", "authentication"),
    (r"(secret|credential|token|api[_-]?key|passwd|password)", "credential_handling"),
    (r"^enforcement/", "enforcement_gate"),
    (r"^tools/gates/", "enforcement_gate"),
    (r"(^|/)gate_[^/]*\.(sh|py)$", "enforcement_gate"),
    (r"^tools/hooks/|^\.git/hooks/", "commit_time_enforcement"),
    (r"^\.gitignore$", "durability_boundary"),
    (r"(^|/)[^/]*(delete|purge|drop|destroy|reset)[^/]*\.(py|sh)$", "destructive_write_path"),
    (r"^tools/queue/queue_set\.py$", "destructive_write_path"),
    (r"^tools/development/(continuity_store|discovery|card_contract|launcher|"
     r"process_identity|verification_plan)\.py$", "authority_boundary"),
    (r"^tools/state/(canonical_state|build_path|destination_architecture)\.py$", "authority_boundary"),
    (r"^config/kb_source_policy\.yaml$", "source_policy"),
    (r"^runtime/(container_app|workbench_app)\.py$", "authoritative_listener"),
    (r"^runtime/cloudflare|cloudflared|^runtime/ingress", "trust_boundary"),
)

_SECURITY_RES = tuple((re.compile(p, re.I), label) for p, label in SECURITY_SENSITIVE_RULES)

# Suffixes treated as documentation for the purposes of card section 10
# Scenario A. A documentation path that ALSO matches a security rule is not
# documentation — the security rule wins (see `classify_path`).
_DOC_SUFFIXES = (".md", ".txt", ".rst")
# Executable/structured suffixes that are never documentation, even when they
# live under docs/ — a probe script committed into a review packet is still a
# script, and a .yaml under docs/ is still configuration.
_CODE_SUFFIXES = (".py", ".sh", ".bash", ".sql", ".yaml", ".yml", ".json",
                  ".toml", ".ini", ".js", ".ts", ".jsx", ".tsx")

_TEST_FILE_RE = re.compile(r"(?:^|/)(test_[A-Za-z0-9_]+\.py)$")
# Test/gate names as they appear inside free-text evidence prose, e.g.
# "test_canonical_state.py 32/32; gate_export_agreement.sh PASS".
_EVIDENCE_TEST_RE = re.compile(r"\b(test_[A-Za-z0-9_]+\.py)\b")
_EVIDENCE_GATE_RE = re.compile(r"\b(gate_[A-Za-z0-9_]+\.(?:sh|py))\b")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _git(repo_root, *args, timeout=20):
    """Run one read-only git command. Returns (ok, stdout, error).

    Never raises: a plan that cannot read git must say so, because the
    alternative is a plan that silently reports "nothing changed".
    """
    try:
        r = subprocess.run(
            ["git", "-C", repo_root or REPO_ROOT, *args],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return False, "", f"{type(e).__name__}: {e}"
    if r.returncode != 0:
        return False, r.stdout, (r.stderr or f"git exited {r.returncode}").strip()
    return True, r.stdout, None


def _nul_fields(raw):
    """Split a `-z` git payload into fields. Used everywhere a path is read,
    because git's default output QUOTES and octal-escapes any path with a
    space or a non-ASCII byte — and this repository has both. A path mangled
    into `"WB.1 \\342\\200\\224 ..."` matches no pattern and resolves to no
    component, so it would be silently misclassified as undetermined impact.
    """
    return [f for f in (raw or "").split("\0") if f]


def _porcelain_paths(raw):
    """Paths from `git status --porcelain -z`.

    A rename/copy entry is `XY <new>\\0<old>\\0`: BOTH sides are changed
    scope, so both are returned."""
    fields = _nul_fields(raw)
    paths, i = [], 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        if path:
            paths.append(path)
        if status[0] in ("R", "C") and i < len(fields):
            paths.append(fields[i])
            i += 1
    return paths


def _cap(items):
    """Bound a path list, reporting the drop rather than hiding it."""
    items = list(items)
    if len(items) <= _MAX_LISTED:
        return items, 0
    return items[:_MAX_LISTED], len(items) - _MAX_LISTED


# ── derived test-location mapping (card section 7) ───────────────────────

def derive_test_map(repo_root=None):
    """Derive "which component owns which tests" from the repository's own
    layout. No registry, no graph, nothing to maintain.

    Rule, applied to every tracked `test_*.py`:
      - the directory holding it is the test location;
      - if that directory is named `tests`, its PARENT is the component that
        owns those tests, otherwise the directory itself is;
      - a test location owned by the repository ROOT is not a component. It
        is recorded separately as a repository-wide suite, because treating
        the root as a component would make every file on earth "covered" and
        would quietly destroy the undetermined-impact case this module exists
        to protect.

    Returns {"ok", "components": {owner_dir: {...}}, "repo_wide_suites": [...],
             "test_files": {basename: [paths]}, "error"}.
    """
    repo_root = repo_root or REPO_ROOT
    ok, out, err = _git(repo_root, "ls-files", "-z")
    if not ok:
        return {"ok": False, "error": f"could not list tracked files: {err}",
                "components": {}, "repo_wide_suites": [], "test_files": {}}

    components = {}
    repo_wide = set()
    test_files = {}
    for path in _nul_fields(out):
        m = _TEST_FILE_RE.search(path)
        if not m:
            continue
        test_files.setdefault(m.group(1), []).append(path)
        test_dir = os.path.dirname(path)
        owner = os.path.dirname(test_dir) if os.path.basename(test_dir) == "tests" else test_dir
        if owner == "":
            repo_wide.add(test_dir or ".")
            continue
        entry = components.setdefault(owner, {"component": owner, "test_targets": set(),
                                               "test_file_count": 0})
        entry["test_targets"].add(test_dir)
        entry["test_file_count"] += 1

    for entry in components.values():
        entry["test_targets"] = sorted(entry["test_targets"])
    return {
        "ok": True,
        "error": None,
        "components": components,
        "repo_wide_suites": sorted(repo_wide),
        "test_files": {k: sorted(v) for k, v in test_files.items()},
    }


def component_for(path, test_map):
    """The component owning `path`: the NEAREST ancestor directory that
    actually contains tests. None when no ancestor does — reported as
    undetermined, never silently absorbed into a parent."""
    components = test_map.get("components") or {}
    parts = path.split("/")
    for cut in range(len(parts) - 1, 0, -1):
        candidate = "/".join(parts[:cut])
        if candidate in components:
            return candidate
    return None


def security_labels_for(path):
    """Every security-sensitive label `path` matches (card section 7)."""
    return sorted({label for rx, label in _SECURITY_RES if rx.search(path)})


def classify_path(path, test_map):
    """Classify one changed path: owning component, security labels, and
    whether it is documentation.

    Documentation is decided FIRST, by suffix and location, and a
    documentation path carries no security labels. The reason is specific,
    not a convenience: the security rules are matched loosely on purpose, and
    `docs/.../secret_scan.txt` — the *output* of a secret scan — matched
    `credential_handling` and dragged a pure documentation commit into
    repository-wide verification. Prose cannot execute, and the one real
    security risk a document carries (leaking a secret into the index) is
    covered repository-wide by `gate_no_secrets`, which is mandatory and
    never reusable. So this narrowing removes a false positive without
    removing a check.
    """
    is_doc = (not path.endswith(_CODE_SUFFIXES)) and (
        path.endswith(_DOC_SUFFIXES) or path.startswith("docs/")
    )
    labels = [] if is_doc else security_labels_for(path)
    return {
        "path": path,
        "component": component_for(path, test_map),
        "security_labels": labels,
        "documentation": is_doc,
    }


# ── dependency impact (card XDEV-VERIFY-01A, finding 2) ──────────────────
#
# WHAT DIRECTORY STRUCTURE CAN AND CANNOT ESTABLISH. `derive_test_map` answers
# "which tests live with this changed file". Reuse depends on a different
# question: "which OTHER components does this change affect". Nothing in a
# directory layout records that, so the two must not be reported as one
# answer. The first version of this module reported them as one: every
# changed file resolving to a component set `impact_fully_determined` True,
# and condition 4 then reused any evidence whose component simply did not
# appear in the changed set. That is a structural approximation presented as
# proof. It would hold only if no component depended on another, which in
# this repository is false — `tools/state/recovery_packet.py` imports
# `tools/development`, so a change under tools/development can invalidate
# tools/state evidence that structurally "does not overlap" with it.
#
# Dependency impact is therefore its own reported answer, ESTABLISHED only
# where it genuinely can be:
#
#   NO_CHANGE            nothing changed, so nothing can be affected.
#   NO_EXECUTABLE_CHANGE documentation only. Prose is not imported and no
#                        component's behaviour can depend on it. (The two
#                        risks a document does carry — a secret in the index,
#                        a generated projection drifting from the spine — are
#                        covered repository-wide by gate_no_secrets and
#                        gate_export_agreement, both mandatory and never
#                        reusable.)
#   UNDETERMINED         an executable change. Reuse is withheld,
#                        verification widens to the repository-wide suites,
#                        and the uncertainty is stated in `limitations`
#                        instead of being hidden behind a narrower plan.
#   NOT_DETERMINABLE     the changed scope itself could not be established.
#
# One narrower path can still establish it for an individual item while the
# scope-level answer stays UNDETERMINED: an existing record naming the
# dependency fact (`recorded_dependency_evidence`), applied per item inside
# condition 4. No graph is built and no registry is maintained to do any of
# this. Nothing records such a fact in this repository today, so the honest
# answer for an executable change is UNDETERMINED — and saying so, rather
# than deriving a narrower plan from a structural approximation, is the
# correction.

DEPENDENCY_EVIDENCE_KEY = "component_dependency_evidence"

_STRUCTURE_IS_NOT_DEPENDENCY_PROOF = (
    "a changed file having a nearby test directory establishes which tests "
    "live with it, not which other components depend on it; directory layout "
    "records no dependency edges"
)


def recorded_dependency_evidence(baseline):
    """Dependency facts ALREADY recorded in the checkpoint authority, if any.

    This builds no dependency graph and maintains no registry — card section 7
    and card XDEV-VERIFY-01A both forbid that. It reads one OPTIONAL list from
    the existing `project_state.external_dev_checkpoint` packet, the same
    record every other evidence item here is read from, and honours an entry
    only when it is complete:

        {"component": "tools/state",
         "independent_of": ["tools/development"],
         "verified_at_sha": "<sha resolvable in this checkout>",
         "source": "who established it"}

    An entry means: at that SHA, `component` was established not to depend on
    each component in `independent_of`. It is read, never inferred, and never
    strengthened — the plan reports which SHA the fact was established at and
    leaves the reviewer to judge it. An incomplete entry is ignored and
    reported rather than half-applied.

    Nothing in this repository writes this key today, and that is the honest
    answer to "use existing dependency evidence if available": there is none,
    so dependency impact for an executable change is UNDETERMINED and
    verification widens.
    """
    raw = (baseline or {}).get(DEPENDENCY_EVIDENCE_KEY) or []
    if isinstance(raw, dict):
        raw = [raw]
    entries, ignored = [], []
    for item in raw if isinstance(raw, (list, tuple)) else []:
        if not isinstance(item, dict):
            ignored.append({"entry": str(item)[:160], "why": "not an object"})
            continue
        comp = item.get("component")
        indep = item.get("independent_of") or []
        sha = item.get("verified_at_sha")
        if isinstance(indep, str):
            indep = [indep]
        missing = [k for k, v in (("component", comp), ("independent_of", indep),
                                   ("verified_at_sha", sha)) if not v]
        if missing:
            ignored.append({"entry": str(item)[:160],
                            "why": f"incomplete; missing {missing}"})
            continue
        entries.append({"component": comp, "independent_of": sorted(set(indep)),
                        "verified_at_sha": sha,
                        "source": item.get("source") or "source not named"})
    note = (f"{len(entries)} recorded dependency fact(s) read from "
            f"project_state.{CHECKPOINT_KEY}.{DEPENDENCY_EVIDENCE_KEY}"
            if entries else
            f"no dependency evidence is recorded in project_state."
            f"{CHECKPOINT_KEY}.{DEPENDENCY_EVIDENCE_KEY}")
    return {"present": bool(entries), "entries": entries, "ignored": ignored,
            "note": note}


def independence_from_record(covered, changed_components, entries, repo_root=None):
    """Whether a RECORDED fact establishes that `covered` does not depend on
    anything this task changed. Returns (established, detail).

    Deliberately strict: one entry must name the covered component, must list
    every changed component as something it is independent of, and must name a
    commit this checkout can actually resolve. Partial coverage establishes
    nothing."""
    repo_root = repo_root or REPO_ROOT
    changed = set(changed_components or ())
    for entry in entries or ():
        if entry["component"] not in (covered or ()):
            continue
        if not changed <= set(entry["independent_of"]):
            continue
        if not _commit_exists(repo_root, entry["verified_at_sha"]):
            continue
        return True, (
            f"recorded dependency evidence ({entry['source']}) establishes "
            f"{entry['component']} as independent of "
            f"{sorted(changed)} at {entry['verified_at_sha']}")
    return False, None


def dependency_impact(*, determinable, ownership_resolved, documentation_only,
                       changed_file_count, dep_evidence):
    """The dependency half of condition 4, reported as its own answer rather
    than inferred from the test-location mapping. See the section comment
    above for the four states and for the per-item recorded-evidence path."""
    ev_note = (dep_evidence or {}).get("note")
    if not determinable:
        return {"state": "NOT_DETERMINABLE", "established": False,
                "basis": "the changed scope itself could not be established, so "
                         "cross-component dependency impact cannot be assessed",
                "dependency_evidence": ev_note}
    if not ownership_resolved:
        return {"state": "NOT_DETERMINABLE", "established": False,
                "basis": "a changed file has no derivable owning component, so "
                         "cross-component dependency impact cannot be assessed",
                "dependency_evidence": ev_note}
    if not changed_file_count:
        return {"state": "NO_CHANGE", "established": True,
                "basis": "no file changed against the accepted baseline, so no "
                         "component's behaviour or dependencies are affected",
                "dependency_evidence": ev_note}
    if documentation_only:
        return {"state": "NO_EXECUTABLE_CHANGE", "established": True,
                "basis": "the change is documentation only; prose is not imported, "
                         "so no component's behaviour can depend on it (secret "
                         "exposure and projection drift stay covered by the "
                         "mandatory repository-wide gates)",
                "dependency_evidence": ev_note}
    return {
        "state": "UNDETERMINED", "established": False,
        "basis": ("cross-component dependency impact is NOT established: "
                  + _STRUCTURE_IS_NOT_DEPENDENCY_PROOF + ", and "
                  + (ev_note or "no dependency evidence is recorded")
                  + ". Verification is widened to the repository-wide suites and "
                    "no evidence is reused on structural non-overlap alone"),
        "dependency_evidence": ev_note,
    }


# ── accepted baseline (project_state.external_dev_checkpoint) ────────────

def accepted_baseline(conn):
    """The independently accepted baseline, read from the existing
    checkpoint authority. Never re-derived and never written.

    The newest UNSUPERSEDED row wins. If the newest row for the key is
    superseded, that is reported rather than quietly falling back — a
    superseded checkpoint fails reuse condition 3, which is the point.
    """
    base = {"present": False, "superseded": False, "accepted_baseline_sha": None,
            "lifecycle_state": None, "independently_verified": None,
            "error": None, "note": None}
    try:
        row = conn.execute(
            "SELECT id, value, source, created_at, superseded_at FROM project_state "
            "WHERE key = ? AND superseded_at IS NULL "
            "ORDER BY created_at DESC, id DESC LIMIT 1", (CHECKPOINT_KEY,),
        ).fetchone()
        superseded = False
        if row is None:
            row = conn.execute(
                "SELECT id, value, source, created_at, superseded_at FROM project_state "
                "WHERE key = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (CHECKPOINT_KEY,),
            ).fetchone()
            superseded = row is not None
    except Exception as e:  # noqa: BLE001 — a fixture DB without project_state is normal
        base["error"] = f"could not read project_state: {type(e).__name__}: {e}"
        base["note"] = ("no accepted baseline is available on this database, so "
                        "no evidence may be reused")
        return base

    if row is None:
        base["note"] = (f"no project_state row with key={CHECKPOINT_KEY!r}; there is "
                        "no accepted baseline to reuse evidence against")
        return base

    try:
        packet = json.loads(row["value"])
    except (TypeError, ValueError) as e:
        base.update({"present": True, "superseded": superseded, "row_id": row["id"],
                     "recorded_at": row["created_at"],
                     "error": f"checkpoint value is not JSON: {e}"})
        return base

    verification_source = packet.get("verification_source") or ""
    pushed_by = packet.get("pushed_by") or ""
    base.update({
        "present": True,
        "superseded": superseded,
        "row_id": row["id"],
        "recorded_at": row["created_at"],
        "recorded_by": row["source"],
        "lifecycle_state": packet.get("lifecycle_state"),
        "accepted_baseline_sha": packet.get("latest_remote_verified_sha"),
        "checkpoint_pushed_sha": packet.get("latest_pushed_sha"),
        "checkpoint_local_sha": packet.get("latest_local_sha"),
        "independently_verified": packet.get("independently_verified"),
        "remote_review_required": packet.get("remote_review_required"),
        "remote_ref": packet.get("remote_ref"),
        "verification_source": verification_source,
        "pushed_by": pushed_by,
        "review_result": packet.get("review_result"),
        "verified_scope": packet.get("verified_scope"),
        "evidence_at_this_sha": packet.get("evidence_at_this_sha") or "",
        "live_gates_at_record_time": packet.get("live_gates_at_record_time") or "",
        "continuity_refs": packet.get("continuity_refs"),
        "authority": packet.get("authority"),
        # Optional, and absent on every row written to date. Read-only input to
        # `recorded_dependency_evidence`; nothing here writes or maintains it.
        DEPENDENCY_EVIDENCE_KEY: packet.get(DEPENDENCY_EVIDENCE_KEY),
    })
    if superseded:
        base["note"] = ("the newest checkpoint row for this key is marked "
                        "superseded; its evidence fails reuse condition 3")
    return base


# ── observed git facts ───────────────────────────────────────────────────

def observed_git(repo_root=None, include_remote=False):
    """Local, read-only git observation.

    `include_remote` is OFF by default and that is deliberate. `git ls-remote`
    is the only thing that actually proves a commit reached the remote, and it
    touches the network — so this module REQUIRES that proof (see
    `git_push_confirmation` in MANDATORY_CHECKS) rather than performing it on
    every plan build. A remote-TRACKING ref (`origin/master`) is only as fresh
    as the last fetch, so it is reported as what it is and never presented as
    push proof.
    """
    repo_root = repo_root or REPO_ROOT
    out = {"ok": False, "repo_root": repo_root, "head": None, "branch": None,
           "upstream_ref": None, "upstream_sha": None, "ls_remote_sha": None,
           "ls_remote_performed": bool(include_remote),
           "dirty_files": [], "dirty_file_count": 0, "error": None,
           "note": ("upstream_sha is a remote-tracking ref, only as fresh as the "
                    "last fetch. It is NOT proof that a commit reached the remote; "
                    "git ls-remote is.")}

    ok, head, err = _git(repo_root, "rev-parse", "HEAD")
    if not ok:
        out["error"] = f"could not read HEAD: {err}"
        return out
    out["head"] = head.strip()
    out["ok"] = True

    ok, branch, _ = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    if ok:
        out["branch"] = branch.strip()
    ok, upstream, _ = _git(repo_root, "rev-parse", "--abbrev-ref", "@{upstream}")
    if ok and upstream.strip():
        out["upstream_ref"] = upstream.strip()
        ok2, usha, _ = _git(repo_root, "rev-parse", out["upstream_ref"])
        if ok2:
            out["upstream_sha"] = usha.strip()

    ok, status, _ = _git(repo_root, "status", "--porcelain", "-z")
    if ok:
        dirty = sorted(set(_porcelain_paths(status)))
        kept, dropped = _cap(dirty)
        out["dirty_files"] = kept
        out["dirty_files_truncated"] = dropped
        out["dirty_file_count"] = len(dirty)

    if include_remote and out["branch"]:
        ok, ls, err = _git(repo_root, "ls-remote", "origin",
                            f"refs/heads/{out['branch']}", timeout=45)
        if ok and ls.strip():
            out["ls_remote_sha"] = ls.split()[0]
        else:
            out["ls_remote_error"] = err or "no ref returned"
    return out


def _commit_exists(repo_root, sha):
    if not sha or not _SHA_RE.match(str(sha)):
        return False
    ok, _, _ = _git(repo_root, "cat-file", "-e", f"{sha}^{{commit}}")
    return ok


def _resolve_commit(repo_root, sha):
    """The full 40-character SHA for a commit-ish token, or None.

    Needed to tell genuine ambiguity from mere abbreviation: this
    repository's records routinely name one commit in both short and long
    form in the same sentence ("pushed at 280723da ... 280723da8d43..."),
    and counting those as two commits would invent ambiguity that is not
    there. Resolution is what makes them one.
    """
    if not sha or not _SHA_RE.match(str(sha)):
        return None
    ok, out, _ = _git(repo_root, "rev-parse", "--verify", f"{sha}^{{commit}}")
    if not ok:
        return None
    full = (out or "").strip()
    return full or None


def _is_ancestor(repo_root, maybe_ancestor, descendant="HEAD"):
    """Whether `maybe_ancestor` is reachable from `descendant`.

    Used to establish that an evidence item was measured at a state the
    current one actually descends from. A commit that is NOT an ancestor —
    a later commit, or one on a diverged branch — cannot have its delta to
    HEAD read as "what changed since this evidence was taken", so reuse
    fails closed rather than diffing two unrelated states.
    """
    if not maybe_ancestor or not _SHA_RE.match(str(maybe_ancestor)):
        return False
    ok, _, _ = _git(repo_root, "merge-base", "--is-ancestor",
                    maybe_ancestor, descendant)
    return ok


# ── changed scope (card section 4, section 7) ────────────────────────────

def changed_scope(baseline_sha, repo_root=None, include_worktree=True, test_map=None,
                   dep_evidence=None, worktree_paths=None):
    """What this task actually changes, relative to the accepted baseline.

    Fails closed in every direction:
      - no baseline SHA, or a baseline SHA this checkout does not contain
        -> determinable=False. Impact unknown, so nothing may be reused.
      - a changed file whose owning component cannot be derived
        -> component_ownership_resolved=False, and that file's name is
           reported.
      - an executable change with no recorded dependency evidence
        -> dependency_impact.state=UNDETERMINED. Ownership being fully
           resolved is NOT upgraded to "the affected set is known"; see the
           dependency-impact section above.

    `impact_fully_determined` means BOTH halves hold, and is the only field
    condition 4 may read as "impact is known". Each half is also reported on
    its own so a reader can see which one is missing.
    """
    repo_root = repo_root or REPO_ROOT
    test_map = test_map or derive_test_map(repo_root)
    dep_evidence = dep_evidence if dep_evidence is not None else \
        {"present": False, "entries": [], "ignored": [],
         "note": "no dependency evidence was supplied to this derivation"}

    scope = {
        "baseline_sha": baseline_sha,
        "compared_to": "HEAD + working tree" if include_worktree else "HEAD",
        "determinable": False,
        "reason": None,
        "changed_files": [],
        "changed_files_truncated": 0,
        "changed_file_count": 0,
        "components": {},
        "undetermined_files": [],
        "security_sensitive": [],
        "security_labels": [],
        "documentation_only": False,
        "component_ownership_resolved": False,
        "dependency_impact": None,
        "impact_fully_determined": False,
        "test_map_ok": test_map.get("ok", False),
        "repo_wide_suites": test_map.get("repo_wide_suites", []),
        # The uncommitted paths this derivation actually used, UNCAPPED and
        # kept verbatim so a per-item currency scope (see evidence_currency)
        # measures the same working tree instead of re-reading a tree that
        # may have moved underneath it mid-derivation.
        "include_worktree": bool(include_worktree),
        "worktree_paths": [],
    }

    def _finish():
        """Fill in the dependency half and the combined answer, on every exit
        path — including the early failures, so no caller can read a scope
        whose dependency_impact was never computed."""
        scope["dependency_impact"] = dependency_impact(
            determinable=scope["determinable"],
            ownership_resolved=scope["component_ownership_resolved"],
            documentation_only=scope["documentation_only"],
            changed_file_count=scope["changed_file_count"],
            dep_evidence=dep_evidence,
        )
        scope["impact_fully_determined"] = bool(
            scope["component_ownership_resolved"]
            and scope["dependency_impact"]["established"])
        return scope

    if not baseline_sha:
        scope["reason"] = ("no accepted baseline SHA is recorded, so the changed "
                           "scope cannot be established")
        return _finish()
    if not _commit_exists(repo_root, baseline_sha):
        scope["reason"] = (f"accepted baseline {baseline_sha} is not present in this "
                           "checkout, so the changed scope cannot be established")
        return _finish()
    if not test_map.get("ok"):
        scope["reason"] = f"test-location mapping unavailable: {test_map.get('error')}"
        return _finish()

    ok, out, err = _git(repo_root, "diff", "--name-only", "-z",
                        f"{baseline_sha}..HEAD")
    if not ok:
        scope["reason"] = f"git diff against the baseline failed: {err}"
        return _finish()
    changed = set(_nul_fields(out))

    if include_worktree:
        if worktree_paths is None:
            ok, status, err = _git(repo_root, "status", "--porcelain", "-z")
            if not ok:
                scope["reason"] = f"working-tree status unavailable: {err}"
                return _finish()
            worktree_paths = _porcelain_paths(status)
        scope["worktree_paths"] = list(worktree_paths)
        changed.update(worktree_paths)

    scope["determinable"] = True
    scope["changed_file_count"] = len(changed)
    kept, dropped = _cap(sorted(changed))
    scope["changed_files"] = kept
    scope["changed_files_truncated"] = dropped

    classified = [classify_path(p, test_map) for p in sorted(changed)]
    undetermined = []
    labels = set()
    for item in classified:
        for label in item["security_labels"]:
            labels.add(label)
            scope["security_sensitive"].append({"path": item["path"], "label": label})
        comp = item["component"]
        if comp is None:
            # A documentation file with no owning component is not an unknown
            # dependency — there is nothing to depend on it. Anything else is.
            if not item["documentation"]:
                undetermined.append(item["path"])
            continue
        entry = scope["components"].setdefault(comp, {
            "component": comp,
            "test_targets": test_map["components"][comp]["test_targets"],
            "files": [],
            "security_labels": [],
        })
        entry["files"].append(item["path"])
        for label in item["security_labels"]:
            if label not in entry["security_labels"]:
                entry["security_labels"].append(label)

    scope["undetermined_files"], scope["undetermined_truncated"] = _cap(undetermined)
    scope["undetermined_file_count"] = len(undetermined)
    scope["security_labels"] = sorted(labels)
    scope["documentation_only"] = bool(classified) and all(
        c["documentation"] for c in classified
    )
    scope["component_ownership_resolved"] = not undetermined
    if undetermined:
        scope["reason"] = (
            f"{len(undetermined)} changed file(s) have no derivable owning "
            "component, so their impact cannot be established; broader "
            "verification is required and no evidence may be reused"
        )
    return _finish()


# ── evidence candidates, read from existing records ──────────────────────

def _authority_of(verification_source, pushed_by, independently_verified):
    """Who established a checkpoint's evidence.

    Independent acceptance is credited ONLY when the checkpoint says it was
    independently verified AND names a verification source that is not the
    pushing agent. Anything else is the implementing developer's own
    verification, which is useful evidence and is never acceptance.
    """
    src = (verification_source or "").lower()
    if not independently_verified:
        return "implementing_developer", "checkpoint does not claim independent verification"
    if not src:
        return "implementing_developer", "checkpoint claims verification but names no source"
    pusher = (pushed_by or "").lower()
    if pusher and pusher.split(",")[0].strip() and pusher.split(",")[0].strip() in src:
        return ("implementing_developer",
                "named verification source is the pushing agent itself")
    return "independent_reviewer", f"verification_source: {verification_source[:200]}"


def evidence_candidates(conn, task, baseline, test_map, repo_root=None, dev_conn=None):
    """Collect previously established results from the two existing records.

    Checkpoint evidence is bound to the accepted baseline SHA and may carry
    independent authority. Continuity `verified_result` evidence is the
    implementing developer's own and is marked as such permanently.

    Each item's `covered_components` is derived by locating the named test
    file in the repository and mapping it through the same structural rule
    used for changed files. A test name that matches no tracked file, or more
    than one, leaves coverage UNKNOWN — which fails reuse condition 4.
    """
    repo_root = repo_root or REPO_ROOT
    dev_conn = dev_conn or conn
    items = []
    tracked_tests = test_map.get("test_files") or {}

    def _coverage(name):
        paths = tracked_tests.get(name) or []
        if len(paths) != 1:
            return None, (f"{name} matches {len(paths)} tracked files; its coverage "
                          "cannot be resolved")
        comp = component_for(paths[0], test_map)
        if comp is None:
            return None, f"{name} resolves to {paths[0]}, which has no owning component"
        return [comp], None

    if baseline.get("present"):
        # WHICH SHA DOES THIS ROW'S EVIDENCE DESCRIBE? The checkpoint's
        # `evidence_at_this_sha` describes the SHA the ROW is about — its
        # latest_pushed_sha — which equals latest_remote_verified_sha only
        # when the row records an ACCEPTANCE. A row that records a PUSH
        # awaiting review has them differ, and binding its evidence to the
        # accepted baseline SHA would attribute a developer's fresh test run
        # to a commit an independent reviewer passed. So the evidence is
        # bound to the row's own subject SHA, and independent authority is
        # credited only when that subject IS the accepted baseline.
        subject_sha = (baseline.get("checkpoint_pushed_sha")
                       or baseline.get("checkpoint_local_sha")
                       or baseline.get("accepted_baseline_sha"))
        accepted_sha = baseline.get("accepted_baseline_sha")
        authority, authority_basis = _authority_of(
            baseline.get("verification_source"), baseline.get("pushed_by"),
            baseline.get("independently_verified"),
        )
        if authority == "independent_reviewer" and subject_sha != accepted_sha:
            authority = "implementing_developer"
            authority_basis = (
                f"this checkpoint row's evidence describes {subject_sha}, which is "
                f"not the independently accepted baseline {accepted_sha}; the row "
                "records a push, not an acceptance (ADR-XDEV-001)")
        prose = " ".join(filter(None, [
            baseline.get("evidence_at_this_sha"),
            baseline.get("live_gates_at_record_time"),
        ]))
        seen = set()
        for rx, kind in ((_EVIDENCE_TEST_RE, "test_suite"), (_EVIDENCE_GATE_RE, "gate")):
            for name in rx.findall(prose):
                if name in seen:
                    continue
                seen.add(name)
                if kind == "test_suite":
                    covered, cov_note = _coverage(name)
                    check_id = name
                else:
                    # A gate's blast radius is the repository, not a component,
                    # and every gate named in MANDATORY_CHECKS is pinned out of
                    # reuse anyway. Coverage stays unknown on purpose.
                    covered, cov_note = None, (
                        f"{name} is a repository-wide gate; its result is not "
                        "scoped to a component")
                    check_id = os.path.splitext(name)[0]
                items.append({
                    "id": f"checkpoint:{baseline.get('row_id')}:{name}",
                    "check_id": check_id,
                    "kind": kind,
                    "name": name,
                    "source": (f"project_state.{CHECKPOINT_KEY} row "
                               f"{baseline.get('row_id')}"),
                    "authority": authority,
                    "authority_basis": authority_basis,
                    "is_independent_acceptance": authority == "independent_reviewer",
                    "tested_identity": subject_sha,
                    "tested_identity_is_accepted_baseline": subject_sha == accepted_sha,
                    # A checkpoint row names ONE subject SHA, so its evidence
                    # has unambiguous provenance by construction.
                    "tested_identity_candidates": [subject_sha] if subject_sha else [],
                    "tested_identity_ambiguous": False,
                    "superseded": bool(baseline.get("superseded")),
                    "covered_components": covered,
                    "coverage_note": cov_note,
                    "result_excerpt": _excerpt(prose, name),
                })

    # Continuity-recorded results for this task. Always the implementing
    # developer's own, regardless of what their prose claims.
    if task and cs.is_initialized(dev_conn):
        try:
            events = cs.list_events(dev_conn, task)
        except cs.ContinuityError:
            events = []
        reconciled = {
            e["against_revision"] for e in events
            if e["kind"] == "reconciliation" and e.get("against_revision") is not None
        }
        for e in reversed(events[-_EVENT_SCAN_LIMIT:]):
            if e["kind"] != "verified_result":
                continue
            refs = e.get("evidence_refs") or []
            if isinstance(refs, str):
                try:
                    refs = json.loads(refs)
                except ValueError:
                    refs = [refs]
            prose = " ".join([e.get("summary") or ""] + [str(r) for r in refs])
            names = set(_EVIDENCE_TEST_RE.findall(prose))
            if not names:
                continue
            # WHICH COMMIT DID THIS EVENT MEASURE AT? A continuity event records
            # WHEN, not against which commit, so the identity is read from its
            # own prose. An event naming several resolvable commits does not say
            # which one its results came from; that is recorded as ambiguous and
            # fails reuse closed rather than crediting the first token found.
            prose_shas = _shas_in(prose)
            resolved, resolvable = [], []
            for s in prose_shas:
                full = _resolve_commit(repo_root, s)
                if full and full not in resolved:
                    resolved.append(full)
                    resolvable.append(s)
            for name in sorted(names):
                covered, cov_note = _coverage(name)
                items.append({
                    "id": f"dev_continuity_events:{e['revision']}:{name}",
                    "check_id": name,
                    "kind": "test_suite",
                    "name": name,
                    "source": (f"dev_continuity_events revision {e['revision']} "
                               f"(task {task}, actor {e.get('actor')})"),
                    "authority": "implementing_developer",
                    "authority_basis": ("recorded by the implementing developer; "
                                        "ADR-XDEV-001 disqualifies it as acceptance"),
                    "is_independent_acceptance": False,
                    # A continuity event records WHEN, not against which commit.
                    # Absent an explicit SHA in its own prose, its tested
                    # identity is unknown, and condition 2 fails.
                    "tested_identity": prose_shas[0] if prose_shas else None,
                    "tested_identity_candidates": resolvable,
                    "tested_identity_ambiguous": len(resolvable) > 1,
                    "superseded": e["revision"] in reconciled,
                    "covered_components": covered,
                    "coverage_note": cov_note,
                    "result_excerpt": _excerpt(prose, name),
                })
    return items


def _excerpt(prose, name, width=70):
    i = prose.find(name)
    if i < 0:
        return None
    return prose[max(0, i - 10):i + width].strip()


def _shas_in(text):
    """Every DISTINCT commit-shaped token in an event's prose, in order.

    An event naming more than one resolvable commit does not say which one its
    test results were measured at. That is ambiguous provenance, and condition
    4 fails closed on it rather than picking the first token and hoping.
    """
    seen, out = set(), []
    for token in re.findall(r"\b[0-9a-f]{7,40}\b", text or ""):
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


def _sha_in(text):
    shas = _shas_in(text)
    return shas[0] if shas else None


# ── evidence currency (card XDEV-VERIFY-01D) ─────────────────────────────
#
# THE DEFECT THIS CORRECTS. Condition 4 used to compare an item's covered
# components against the scope changed since the ACCEPTED BASELINE, and never
# against the item's own `tested_identity`. The module DERIVED correct
# provenance (see evidence_candidates, where checkpoint evidence is bound to
# the row's own subject SHA) and then ignored it in the one check whose job is
# to decide whether that provenance is still good enough. That single omission
# failed in both directions:
#
#   - evidence measured AT the state under review was invalidated exactly like
#     evidence from an older commit, because its component appears in the
#     baseline delta. Avoidable re-runs; fails safe.
#   - and when the baseline ADVANCED to the reviewed SHA, the baseline delta
#     became empty, dependency impact read NO_CHANGE, and evidence measured at
#     EARLIER implementations was reused as proof for the new one. Fails
#     UNSAFE, and it was demonstrated against this very module: a
#     test_verification_plan.py result measured at 280723da was reported
#     reusable for b1a757a9, across three commits that rewrote
#     verification_plan.py itself.
#
# THE CORRECTION. Reuse is judged against the delta from the state the evidence
# was MEASURED at to the state now under verification, which is what "is this
# result still valid" actually means. The question is answered by calling
# `changed_scope` with the item's own tested identity as the baseline, so there
# is ONE classification rule, not a second parallel one: the same -z path
# readers, the same documentation rule, the same ownership gate and the same
# `dependency_impact` states apply. Nothing about what verification is REQUIRED
# changes — `required_new_evidence` still derives from the accepted-baseline
# scope, because the unit an independent reviewer accepts is the whole
# unaccepted delta (ADR-XDEV-001), not the increment since a developer's last
# test run.
#
# WHAT STILL FAILS CLOSED, unchanged or newly:
#   - the scope-level component-ownership gate still blocks every item first;
#     this correction never relaxes it and resolves no ownership gap.
#   - absent identity (condition 2's case) now also fails condition 4.
#   - AMBIGUOUS identity — an event naming more than one resolvable commit —
#     fails closed instead of silently crediting the first token found.
#   - an identity that is NOT an ancestor of the state under verification
#     (a later commit, a diverged branch) fails closed: its delta to HEAD
#     cannot be read as "what changed since this evidence was taken".
#   - a matching SHA is NOT sufficient on its own. Uncommitted changes are
#     part of the state under verification, so an item measured at HEAD with
#     relevant working-tree modifications is still invalidated.
#   - gates keep `covered_components = None` and are refused before any of
#     this, and mandatory gates additionally fail condition 5.

_CURRENCY_CACHE_KEY = "_currency_cache"


def evidence_currency(item, scope, repo_root=None, test_map=None, dep_evidence=None,
                       cache=None):
    """What changed between the state an item was MEASURED at and the state
    now under verification. Returns a dict with:

        established  whether the delta could be established at all
        basis        why, in the item's own terms, always populated
        scope        the full `changed_scope` result for that delta, or None

    Establishing the delta is NOT the same as permitting reuse; the caller
    still applies the overlap and dependency-impact rules to `scope`.
    """
    repo_root = repo_root or REPO_ROOT
    identity = item.get("tested_identity")

    if not identity:
        return {"established": False, "scope": None,
                "basis": "no tested commit identity is recorded, so what has "
                         "changed since this result was measured cannot be "
                         "established"}
    if item.get("tested_identity_ambiguous"):
        candidates = item.get("tested_identity_candidates") or []
        return {"established": False, "scope": None,
                "basis": ("the record this result came from names "
                          f"{len(candidates)} resolvable commits "
                          f"({', '.join(c[:12] for c in candidates[:4])}"
                          f"{' ...' if len(candidates) > 4 else ''}), so the "
                          "commit it was measured at is ambiguous")}
    if not _commit_exists(repo_root, identity):
        return {"established": False, "scope": None,
                "basis": (f"recorded identity {identity} is not resolvable in this "
                          "checkout, so the change since it cannot be established")}
    if not _is_ancestor(repo_root, identity):
        return {"established": False, "scope": None,
                "basis": (f"this result was measured at {identity}, which is not an "
                          "ancestor of the state under verification; the change "
                          "between them cannot be read as what happened since")}

    key = (identity, bool(scope.get("include_worktree")))
    cache = cache if cache is not None else {}
    if key not in cache:
        # Same derivation, different baseline. The working-tree paths are the
        # ones the accepted-baseline scope already read, so both measure one
        # tree even if the real tree changes mid-derivation.
        cache[key] = changed_scope(
            identity, repo_root=repo_root,
            include_worktree=bool(scope.get("include_worktree")),
            test_map=test_map, dep_evidence=dep_evidence,
            worktree_paths=scope.get("worktree_paths"),
        )
    since = cache[key]

    if not since.get("determinable"):
        return {"established": False, "scope": since,
                "basis": (f"the change since {identity} could not be established: "
                          + (since.get("reason") or "reason not reported"))}
    if not since.get("component_ownership_resolved"):
        return {"established": False, "scope": since,
                "basis": (f"since {identity}, "
                          + (since.get("reason") or
                             "a changed file has no derivable owning component"))}
    return {"established": True, "scope": since,
            "basis": (f"measured at {identity}; "
                      f"{since.get('changed_file_count')} file(s) changed between "
                      "it and the state under verification")}


# ── validity classification (card section 3) ─────────────────────────────

def classify_evidence(items, scope, repo_root=None, dep_evidence=None,
                       test_map=None):
    """Apply the five reuse conditions to each candidate, and report which
    one failed. Returns (reusable, invalidated).

    Condition 4 has two independent halves and both must hold (card
    XDEV-VERIFY-01A, finding 2): the changed files' owning components must be
    resolved, AND the item's covered components must be established as
    unaffected. Structural non-overlap answers only the first half; it is
    reported as what it is and never as the second.

    The second half is measured from the item's OWN tested identity, not from
    the accepted baseline (card XDEV-VERIFY-01D); see evidence_currency."""
    repo_root = repo_root or REPO_ROOT
    test_map = test_map or derive_test_map(repo_root)
    ownership_ok = (bool(scope.get("determinable"))
                    and bool(scope.get("component_ownership_resolved")))
    dep_entries = (dep_evidence or {}).get("entries") or []
    active_labels = set(scope.get("security_labels") or [])
    currency_cache = {}

    reusable, invalidated = [], []
    for item in items:
        checks = []

        checks.append({
            "condition": 1,
            "rule": "source and verification authority are identifiable",
            "ok": bool(item.get("source")) and bool(item.get("authority")),
            "detail": f"{item.get('source')} / {item.get('authority')}",
        })

        identity = item.get("tested_identity")
        identity_ok = bool(identity) and _commit_exists(repo_root, identity)
        checks.append({
            "condition": 2,
            "rule": "tested commit/artifact identity is known and resolvable",
            "ok": identity_ok,
            "detail": (f"tested at {identity}" if identity_ok else
                       (f"recorded identity {identity} is not resolvable in this checkout"
                        if identity else "no tested commit identity recorded")),
        })

        checks.append({
            "condition": 3,
            "rule": "result has not been superseded or invalidated",
            "ok": not item.get("superseded"),
            "detail": "superseded record" if item.get("superseded") else "not superseded",
        })

        covered = item.get("covered_components")
        currency = None
        if not ownership_ok:
            # The scope-level ownership gate is unchanged and still comes
            # first: if any changed file in the reviewed delta has no owning
            # component, nothing is reusable regardless of provenance.
            cond4_ok = False
            cond4_detail = (scope.get("reason") or
                            "the changed scope could not be fully established")
        elif covered is None:
            cond4_ok = False
            cond4_detail = (item.get("coverage_note") or
                            "what this result covers cannot be established")
        else:
            # CARD XDEV-VERIFY-01D. Judge the item against the change since it
            # was MEASURED, not since the accepted baseline. Absent, ambiguous,
            # unresolvable, non-ancestor or unownable provenance fails closed.
            currency = evidence_currency(item, scope, repo_root=repo_root,
                                         test_map=test_map, dep_evidence=dep_evidence,
                                         cache=currency_cache)
            if not currency["established"]:
                cond4_ok, cond4_detail = False, currency["basis"]
            else:
                since = currency["scope"]
                since_components = set(since.get("components") or {})
                since_dep = since.get("dependency_impact") or {}
                changed_list = sorted(since_components)
                overlap = sorted(set(covered) & since_components)
                prefix = (f"covers {covered}; since this result was measured at "
                          f"{item.get('tested_identity')} the state under "
                          f"verification changes {changed_list}")
                if overlap:
                    cond4_ok, cond4_detail = False, (
                        f"{prefix} — overlap {overlap}, so this result does not "
                        "describe the implementation now under verification")
                elif since_dep.get("established"):
                    cond4_ok = True
                    cond4_detail = f"{prefix} — no overlap, and {since_dep.get('basis')}"
                else:
                    recorded, why = independence_from_record(
                        covered, since_components, dep_entries, repo_root)
                    if recorded:
                        cond4_ok, cond4_detail = True, f"{prefix} — no overlap, and {why}"
                    else:
                        # CARD XDEV-VERIFY-01A, FINDING 2, preserved verbatim in
                        # effect: absence of overlap in a directory-derived
                        # component map is not evidence of independence.
                        cond4_ok = False
                        cond4_detail = (
                            f"{prefix} — no overlap, but non-overlap is not proof "
                            f"that those changes leave {covered} unaffected: "
                            + (since_dep.get("basis")
                               or _STRUCTURE_IS_NOT_DEPENDENCY_PROOF))
        checks.append({
            "condition": 4,
            "rule": "this task does not change the behaviour or dependencies covered",
            "ok": cond4_ok, "detail": cond4_detail,
        })

        mandatory = item.get("check_id") in MANDATORY_CHECK_IDS
        if mandatory:
            cond5_ok, cond5_detail = False, (
                f"{item.get('check_id')} is a mandatory gate and always runs fresh")
        elif active_labels:
            cond5_ok, cond5_detail = False, (
                "this task carries security-sensitive changes "
                f"({sorted(active_labels)}); required verification depth is retained")
        else:
            cond5_ok, cond5_detail = True, "no mandatory policy requires fresh execution"
        checks.append({
            "condition": 5,
            "rule": "no mandatory policy requires fresh execution",
            "ok": cond5_ok, "detail": cond5_detail,
        })

        failed = [c for c in checks if not c["ok"]]
        record = dict(item)
        record["validity_checks"] = checks
        # Provenance is reported, never just consumed: the reader can see which
        # state this result was measured at and what moved since.
        record["evidence_currency"] = None if currency is None else {
            "established": currency["established"],
            "basis": currency["basis"],
            "measured_at": item.get("tested_identity"),
            "changed_since_measurement": sorted(
                (currency["scope"] or {}).get("components") or {}),
            "changed_file_count_since_measurement": (
                (currency["scope"] or {}).get("changed_file_count")),
        }
        if failed:
            record["invalidation_reason"] = "; ".join(
                f"condition {c['condition']} ({c['rule']}): {c['detail']}" for c in failed
            )
            invalidated.append(record)
        else:
            record["reuse_basis"] = "; ".join(c["detail"] for c in checks)
            reusable.append(record)
    return reusable, invalidated


# ── required new evidence (card section 4B / 7) ───────────────────────────

def required_new_evidence(scope, test_map):
    """What must actually be run. Widens on every unknown."""
    required = []
    repo_wide = scope.get("repo_wide_suites") or test_map.get("repo_wide_suites") or []

    def _repo_wide(why):
        required.append({
            "check": "repository-wide test suites",
            "targets": repo_wide,
            "scope": "repository",
            "why": why,
            "reuse_permitted": False,
            "basis": "broader verification preserved where impact is not established",
        })

    if not scope.get("determinable"):
        _repo_wide(scope.get("reason") or "changed scope could not be established")
        return required

    for comp, entry in sorted(scope["components"].items()):
        required.append({
            "check": f"tests for {comp}",
            "targets": entry["test_targets"],
            "scope": comp,
            "why": (f"{len(entry['files'])} changed file(s) in this component: "
                    + ", ".join(entry["files"][:8])
                    + (" ..." if len(entry["files"]) > 8 else "")),
            "reuse_permitted": False,
            "basis": ("test-location mapping derived from the repository's own "
                      "layout (git ls-files), not a maintained registry. It "
                      "names the tests that live with the changed files; it "
                      "does NOT establish which other components depend on "
                      "them — see dependency_impact"),
            "security_labels": entry["security_labels"],
        })

    if scope.get("undetermined_files"):
        _repo_wide(
            f"{scope.get('undetermined_file_count')} changed file(s) have no "
            "derivable owning component: "
            + ", ".join(scope["undetermined_files"][:8])
            + (" ..." if scope.get("undetermined_truncated") else "")
        )

    # Card XDEV-VERIFY-01A, finding 2: ownership fully resolved still leaves
    # "which other components does this affect" unanswered. Widen rather than
    # let the component list read as the complete affected set. (Unreachable
    # when ownership is unresolved — that case widened immediately above.)
    dep = scope.get("dependency_impact") or {}
    if scope.get("component_ownership_resolved") and not dep.get("established"):
        _repo_wide(dep.get("basis") or
                   "cross-component dependency impact is not established")

    for label in scope.get("security_labels") or []:
        paths = sorted({s["path"] for s in scope["security_sensitive"]
                        if s["label"] == label})
        required.append({
            "check": f"required verification depth for {label}",
            "targets": ["the component suites above, at full depth",
                        "the enforcement gates covering this area"],
            "scope": label,
            "why": ("security-sensitive, destructive, migration, authentication or "
                    "authority-boundary change; card section 7 retains its "
                    "required depth regardless of reuse. Paths: "
                    + ", ".join(paths[:6]) + (" ..." if len(paths) > 6 else "")),
            "reuse_permitted": False,
            "basis": "card section 7 — efficiency must not weaken safety",
        })

    return required


# ── mandatory gates, with the one honest exemption card section 6 allows ─

def mandatory_gates(baseline, git_state):
    """MANDATORY_CHECKS, each annotated with whether the existing durable
    record already establishes it for THIS SHA.

    Only `git_push_confirmation` can ever be annotated ESTABLISHED, and only
    when the checkpoint's own recorded push SHA equals the observed HEAD and
    the observed upstream ref — i.e. the exact fact is already proved for the
    exact commit and no new push has happened since. Every other gate runs.
    """
    head = git_state.get("head")
    recorded_push = baseline.get("checkpoint_pushed_sha")
    upstream = git_state.get("upstream_sha")

    out = []
    for check in MANDATORY_CHECKS:
        entry = dict(check)
        entry["status"] = "REQUIRED"
        entry["reuse_permitted"] = False
        if check["id"] == "git_push_confirmation":
            if head and recorded_push == head and upstream == head:
                entry["status"] = "ESTABLISHED_BY_DURABLE_RECORD"
                entry["established_by"] = (
                    f"project_state.{CHECKPOINT_KEY} row {baseline.get('row_id')} "
                    f"records latest_pushed_sha={recorded_push}, which equals the "
                    f"observed HEAD and the observed {git_state.get('upstream_ref')}"
                )
                entry["why_not_repeated"] = (
                    "card section 6: the durable result already establishes the same "
                    "fact for the same commit and no new push has occurred"
                )
            else:
                entry["status"] = "REQUIRED"
                entry["detail"] = (
                    f"observed HEAD {head} is not established as pushed by the "
                    f"durable record (checkpoint latest_pushed_sha={recorded_push}, "
                    f"observed upstream {upstream}); run git ls-remote at push time"
                )
        out.append(entry)
    return out


# ── independent review (card section 4E / 6 / 9) ─────────────────────────

def independent_review_status(baseline, git_state):
    """Whether the current commit still needs external acceptance.

    This function has exactly one hard-coded answer: `may_claim_acceptance`
    is always False. Nothing computed here, and nothing a developer reports,
    can promote a pushed commit to independently accepted — that transition
    is the authorized independent reviewer's alone (ADR-XDEV-001).
    """
    head = git_state.get("head")
    accepted = baseline.get("accepted_baseline_sha")
    recorded_push = baseline.get("checkpoint_pushed_sha")
    upstream = git_state.get("upstream_sha")

    status = {
        "accepted_baseline_sha": accepted,
        "observed_head": head,
        "observed_upstream_ref": git_state.get("upstream_ref"),
        "observed_upstream_sha": upstream,
        "checkpoint_pushed_sha": recorded_push,
        "may_claim_acceptance": False,
        "acceptance_authority": (
            "only the authorized independent reviewer, reading the GitHub remote, "
            "can establish acceptance. The implementing developer — including the "
            "agent that produced this plan — is structurally disqualified from "
            "verifying its own push (ADR-XDEV-001)."
        ),
        "checkpoint_behind_observed_state": bool(
            head and recorded_push and recorded_push != head
        ),
    }

    if not baseline.get("present"):
        status.update({
            "required": True,
            "state": "NO_ACCEPTED_BASELINE_RECORDED",
            "basis": baseline.get("note") or "no checkpoint row is available",
        })
        return status
    if not head:
        status.update({
            "required": True,
            "state": "UNKNOWN_LOCAL_STATE",
            "basis": git_state.get("error") or "HEAD could not be observed",
        })
        return status
    if accepted == head and not baseline.get("superseded"):
        status.update({
            "required": False,
            "state": "ACCEPTED_AT_THIS_COMMIT",
            "basis": (f"the accepted baseline SHA equals the observed HEAD ({head}); "
                      f"lifecycle_state={baseline.get('lifecycle_state')}, recorded "
                      f"{baseline.get('recorded_at')}"),
        })
        return status

    status.update({
        "required": True,
        "state": "PENDING_INDEPENDENT_REVIEW",
        "basis": (f"observed HEAD {head} differs from the accepted baseline "
                  f"{accepted}; the delta has not been independently accepted"),
    })
    return status


# ── the plan ─────────────────────────────────────────────────────────────

def build_plan(conn, *, task=None, repo_root=None, include_worktree=True,
                include_remote=False, dev_conn=None):
    """The whole derivation: A-E of card section 4, in one read-only pass.

    `conn` holds project_state (the checkpoint authority); `dev_conn` holds
    dev_continuity_events, defaulting to `conn` exactly as prepare_packet
    does, so a fixture can point the two at different databases.

    Writes nothing. Calling it twice produces no record, duplicate or
    otherwise — which is what card section 10 Scenario E requires of reused
    evidence.
    """
    repo_root = repo_root or REPO_ROOT
    dev_conn = dev_conn or conn
    test_map = derive_test_map(repo_root)
    baseline = accepted_baseline(conn)
    dep_evidence = recorded_dependency_evidence(baseline)
    git_state = observed_git(repo_root, include_remote=include_remote)
    scope = changed_scope(baseline.get("accepted_baseline_sha"), repo_root=repo_root,
                          include_worktree=include_worktree, test_map=test_map,
                          dep_evidence=dep_evidence)
    candidates = evidence_candidates(conn, task, baseline, test_map,
                                      repo_root=repo_root, dev_conn=dev_conn)
    reusable, invalidated = classify_evidence(candidates, scope, repo_root=repo_root,
                                               dep_evidence=dep_evidence,
                                               test_map=test_map)

    limitations = []
    if not test_map.get("ok"):
        limitations.append(f"test-location mapping unavailable: {test_map.get('error')}")
    if not baseline.get("present"):
        limitations.append(
            "no accepted baseline is recorded on this database, so no evidence can "
            "be reused and full verification is required")
    if baseline.get("superseded"):
        limitations.append(baseline.get("note"))
    if baseline.get("error"):
        limitations.append(baseline["error"])
    if not git_state.get("ok"):
        limitations.append(f"git state unavailable: {git_state.get('error')}")
    if not scope.get("determinable"):
        limitations.append(f"changed scope not determinable: {scope.get('reason')}")
    elif not scope.get("component_ownership_resolved"):
        limitations.append(scope.get("reason"))
    elif not (scope.get("dependency_impact") or {}).get("established"):
        # Reported, never silently absorbed: the plan is narrower than the
        # truth it can establish, and the reader is told which part is open.
        limitations.append((scope.get("dependency_impact") or {}).get("basis"))
    for ignored in dep_evidence.get("ignored") or []:
        limitations.append(
            f"a recorded dependency-evidence entry was ignored ({ignored['why']}): "
            f"{ignored['entry']}")
    if not include_remote:
        limitations.append(
            "push confirmation was NOT performed by this plan (no network call). "
            "git_push_confirmation reports whether it is still required.")
    if git_state.get("dirty_file_count"):
        limitations.append(
            f"{git_state['dirty_file_count']} uncommitted working-tree path(s) are "
            "included in the changed scope; they are not part of any commit yet")

    return {
        "plan_kind": PLAN_KIND,
        "generated_at": _now(),
        "task": task,
        "authority": AUTHORITY_NOTE,
        "records_nothing": True,
        "accepted_baseline": baseline,
        "observed_git": git_state,
        "changed_scope": scope,
        "reusable_evidence": reusable,
        "invalidated_evidence": invalidated,
        "required_new_evidence": required_new_evidence(scope, test_map),
        "mandatory_gates": mandatory_gates(baseline, git_state),
        "independent_review": independent_review_status(baseline, git_state),
        "limitations": [l for l in limitations if l],
    }


# ── external-review handoff (card sections 8 and 9) ──────────────────────

DEFAULT_REVIEW_QUESTION = (
    "Does the delta between the accepted baseline SHA and the pushed SHA satisfy "
    "ADR-XDEV-001 for independent acceptance at the pushed SHA?"
)


def review_handoff(conn, *, task=None, repo_root=None, question=None,
                    include_worktree=True, include_remote=False, plan=None,
                    dev_conn=None):
    """The §9 handoff: the delta an independent reviewer needs, and nothing
    they can already read for themselves.

    A projection of the plan plus the task's own open items. It is not a
    second authoritative store, it creates no record, and it never asserts
    acceptance — `independent_review.may_claim_acceptance` stays False and
    `status` stays PENDING until the reviewer themselves says otherwise.
    """
    dev_conn = dev_conn or conn
    plan = plan or build_plan(conn, task=task, repo_root=repo_root,
                              include_worktree=include_worktree,
                              include_remote=include_remote, dev_conn=dev_conn)
    scope = plan["changed_scope"]
    review = plan["independent_review"]

    open_items = []
    if task and cs.is_initialized(dev_conn):
        try:
            from . import discovery as _discovery
            closeout = _discovery.check_closeout(conn, task, dev_conn=dev_conn)
            open_items = closeout.get("blockers", [])
        except Exception as e:  # noqa: BLE001 — a handoff must still be produced
            open_items = [{"type": "closeout_check_unavailable",
                           "summary": f"{type(e).__name__}: {e}"}]

    return {
        "handoff_kind": HANDOFF_KIND,
        "generated_at": plan["generated_at"],
        "task": task,
        "authority": AUTHORITY_NOTE,
        "pushed_sha": plan["observed_git"].get("head"),
        "pushed_sha_confirmed_on_remote": plan["observed_git"].get("ls_remote_sha")
            if plan["observed_git"].get("ls_remote_performed") else None,
        "accepted_baseline_sha": review.get("accepted_baseline_sha"),
        "changed_files": scope.get("changed_files"),
        "changed_file_count": scope.get("changed_file_count"),
        "changed_files_truncated": scope.get("changed_files_truncated"),
        # Card section 9 asks for "components and dependencies affected". Only
        # the first half is derivable here, so it is reported as the first half
        # and the second is reported as an explicit state rather than implied
        # by a list that cannot contain it (card XDEV-VERIFY-01A, finding 2).
        "changed_components": sorted(scope.get("components") or {}),
        "dependency_impact": (scope.get("dependency_impact") or {}).get("state"),
        "dependency_impact_established":
            (scope.get("dependency_impact") or {}).get("established"),
        "dependency_impact_basis": (scope.get("dependency_impact") or {}).get("basis"),
        "undetermined_impact_files": scope.get("undetermined_files"),
        "required_new_evidence": plan["required_new_evidence"],
        "reused_evidence": [
            {"id": i["id"], "name": i.get("name"), "source": i["source"],
             "authority": i["authority"], "tested_identity": i.get("tested_identity"),
             "validity_basis": i.get("reuse_basis")}
            for i in plan["reusable_evidence"]
        ],
        "invalidated_evidence": [
            {"id": i["id"], "name": i.get("name"), "source": i["source"],
             "reason": i["invalidation_reason"]}
            for i in plan["invalidated_evidence"]
        ],
        "mandatory_gates": plan["mandatory_gates"],
        "security_sensitive_changes": scope.get("security_sensitive"),
        "security_labels": scope.get("security_labels"),
        "open_items_from_closeout_gate": open_items,
        "question_requiring_independent_judgment": question or DEFAULT_REVIEW_QUESTION,
        "question_supplied_by_developer": bool(question),
        "independent_review_status": review.get("state"),
        "independent_review_required": review.get("required"),
        "may_claim_acceptance": False,
        "acceptance_authority": review.get("acceptance_authority"),
        "limitations": plan["limitations"],
    }


# ── the short return packet (card section 8) ─────────────────────────────

def render_return_packet(handoff, *, status=None, next_action=None, what_changed=None):
    """The eight-section human-readable return packet, generated from the
    handoff projection.

    Deliberately short. It reproduces no prior report and repeats no
    architecture history; reused evidence appears as a REFERENCE to the
    record that holds it, never as a copy of its contents. This is a
    projection, not a second authoritative store.
    """
    g = handoff
    lines = []

    lines.append("1. STATUS")
    lines.append(f"   {status or 'see independent-review status below'}")

    lines.append("2. SHAs")
    lines.append(f"   accepted baseline: {g.get('accepted_baseline_sha') or 'none recorded'}")
    lines.append(f"   pushed/current HEAD: {g.get('pushed_sha') or 'unknown'}")

    lines.append("3. WHAT CHANGED")
    if what_changed:
        lines.append(f"   {what_changed}")
    n = g.get("changed_file_count") or 0
    comps = g.get("changed_components") or []
    lines.append(f"   {n} file(s) across {len(comps)} changed component(s): "
                 f"{', '.join(comps) if comps else 'no component resolved'}")
    lines.append(f"   cross-component dependency impact: {g.get('dependency_impact')}"
                 + ("" if g.get("dependency_impact_established")
                    else " — the changed components are NOT established as the "
                         "complete affected set"))
    if g.get("undetermined_impact_files"):
        lines.append(f"   impact undetermined for: "
                     f"{', '.join(g['undetermined_impact_files'][:6])}")

    lines.append("4. NEW VERIFICATION REQUIRED")
    if g.get("required_new_evidence"):
        for r in g["required_new_evidence"]:
            lines.append(f"   - {r['check']} [{r['scope']}]")
    else:
        lines.append("   - none beyond the mandatory gates")
    for gate in g.get("mandatory_gates") or []:
        lines.append(f"   - {gate['id']}: {gate['status']}")

    lines.append("5. REUSED EVIDENCE (by reference)")
    if g.get("reused_evidence"):
        for r in g["reused_evidence"]:
            lines.append(f"   - {r['name']} @ {r['tested_identity']} "
                         f"[{r['authority']}] — {r['source']}")
    else:
        lines.append("   - none reused")

    lines.append("6. EXCEPTIONS / BLOCKERS / UNRESOLVED")
    items = (g.get("open_items_from_closeout_gate") or []) + [
        {"type": "limitation", "summary": l} for l in (g.get("limitations") or [])
    ]
    if items:
        for it in items:
            lines.append(f"   - {it.get('type')}: {str(it.get('summary'))[:160]}")
    else:
        lines.append("   - none")

    lines.append("7. INDEPENDENT REVIEW")
    lines.append(f"   {g.get('independent_review_status')} "
                 f"(required: {g.get('independent_review_required')})")
    lines.append("   acceptance may NOT be claimed by the implementing developer")

    lines.append("8. EXACT NEXT ACTION")
    lines.append(f"   {next_action or g.get('question_requiring_independent_judgment')}")

    return "\n".join(lines)
