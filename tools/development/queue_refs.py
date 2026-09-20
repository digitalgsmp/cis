#!/usr/bin/env python3
"""queue_refs.py — bounded extraction of source/evidence references already
present in a queue item's body_md (WB.1C-R1 remediation 4).

Historical KB/source material named here is EVIDENCE a caller may choose to
follow, never instruction — nothing in this module executes anything it
finds; it only reads knowledge_messages rows and repository files.

Two reference forms are recognized, matching the actual conventions already
used in docs/UNIFIED_BUILD_LIST.md's WB.1 body text (inspected before writing
this, per the task's instruction not to guess the convention):

  - KB numeric ids: "KB 41270", "KB rows 300459 and 889678",
    "KB 41971-41979" or "KB 41971–41979" (a range, hyphen or en-dash).
    Resolved via knowledge_messages.id.
  - Repository file paths: "docs/SPEC_KNOWLEDGE_SURFACE_AGENT.md",
    "runtime/workbench_app.py" — resolved by reading the file, bounded and
    path-contained to the repository root.

A recognized-but-out-of-scope form (a cross-reference to another queue item,
e.g. "queue item 1.10") is reported as recognized_unsupported rather than
silently dropped or, worse, resolved by pulling in that item's own body and
its own references recursively — that has no natural bound and is out of
this task's scope.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Bounded: "KB 1-999999" must not try to resolve 999999 ids.
MAX_RANGE_EXPANSION = 50

_KB_CLUSTER_RE = re.compile(
    r"\bKB\b\s+(?:rows?\s+)?(\d+(?:\s*(?:,|and)\s*\d+(?:[-–]\d+)?|[-–]\d+)*)\b"
)
_KB_NUM_RE = re.compile(r"(\d+)(?:[-–](\d+))?")
_QUEUE_ITEM_RE = re.compile(r"\bqueue item\s+(\d+\.\d+)\b", re.IGNORECASE)
_PATH_RE = re.compile(
    r"\b(?:docs|runtime|tools|cards|enforcement|config)/[\w\-./]+\."
    r"(?:md|py|sql|txt|yaml|yml|sh|jsx?|tsx?)\b"
)


def _expand_kb_cluster(cluster_text):
    ids = []
    for m in _KB_NUM_RE.finditer(cluster_text):
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        if hi < lo:
            lo, hi = hi, lo
        if hi - lo + 1 > MAX_RANGE_EXPANSION:
            hi = lo + MAX_RANGE_EXPANSION - 1
        ids.extend(range(lo, hi + 1))
    return ids


def extract_references(body_md):
    """Return every detected reference in body_md as a dict with at least
    `literal` (the exact text matched) and `type` (kb_id | queue_item |
    file_path). Does not resolve anything — resolution is a separate step
    (resolve_file_reference / the caller's own kb_read.fetch_by_ids) so this
    function stays a pure, side-effect-free parse."""
    body_md = body_md or ""
    refs = []

    for m in _KB_CLUSTER_RE.finditer(body_md):
        ids = sorted(set(_expand_kb_cluster(m.group(1))))
        refs.append({
            "literal": m.group(0), "type": "kb_id",
            "parsed_ids": ids, "malformed": not ids,
        })

    for m in _QUEUE_ITEM_RE.finditer(body_md):
        refs.append({
            "literal": m.group(0), "type": "queue_item",
            "parsed_item_num": m.group(1), "malformed": False,
        })

    for m in _PATH_RE.finditer(body_md):
        refs.append({
            "literal": m.group(0), "type": "file_path",
            "parsed_path": m.group(0), "malformed": False,
        })

    return refs


def resolve_file_reference(path):
    """Read a bounded excerpt of a repository-relative path, path-contained
    to REPO_ROOT. Never raises — a missing/unreadable/escaping path is a
    reported state, not an exception, matching kb_read's "distinguish, don't
    crash" convention."""
    candidate = os.path.abspath(os.path.join(REPO_ROOT, path))
    try:
        contained = os.path.commonpath([candidate, REPO_ROOT]) == REPO_ROOT
    except ValueError:
        contained = False  # different drive on some platforms; never here, but be safe
    if not contained:
        return {"resolution": "malformed", "reason": "path escapes repository root"}
    if not os.path.isfile(candidate):
        return {"resolution": "missing", "reason": "file not found", "path": path}
    try:
        with open(candidate, encoding="utf-8", errors="replace") as f:
            content = f.read(900)
    except OSError as e:
        return {"resolution": "unavailable", "reason": f"{type(e).__name__}: {e}", "path": path}
    return {"resolution": "resolved", "path": path, "content": content}
