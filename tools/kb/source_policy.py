#!/usr/bin/env python3
"""source_policy.py — read config/kb_source_policy.yaml and measure it.

Deterministic throughout. No model judgement, no heuristics: eligibility comes
from the filesystem, presence from knowledge_messages.source_key, and drift from
sha256. Every number this module reports can be re-derived by hand from the same
three places.

Why the policy file and not a table: the question "what is supposed to be in the
KB" is answered by a declaration a human reviews, and the question "what is in
the KB" is answered by the KB. Keeping the first in the database next to the
second would make the corpus measure itself.
"""
import fnmatch
import hashlib
import json
import os
import re
import sqlite3
import time

import yaml

REPO = os.environ.get("CIS_REPO", "/mnt/projects/cis")
POLICY_PATH = os.path.join(REPO, "config/kb_source_policy.yaml")
MANIFEST_PATH = os.path.join(REPO, "runtime/manifests/KB_SOURCE_MANIFEST.json")
DB_PATH = os.environ.get("CIS_SPINE_PATH", os.path.join(REPO, "data/cis_memory.db"))

# 'docs/x.md:12' is the original loader's key; 'docs/x.md:12#r0' is the same row
# after tools/rechunk_for_embedding.py split it to fit the embedding model. Both
# name the same source file, so both must reduce to the same identity — otherwise
# a fully re-chunked document reads as never ingested.
_TRAILING_INDEX = re.compile(r":\d+(#r\d+)?$")
# Anchored at the end, because a filename may itself contain '#' — cis_kernel holds
# "# CIS HANDOFF — Phase D Automation Start.md", and splitting on the first '#'
# turned its key into the directory it sits in, so six ingested handoffs read as
# never ingested.
_TRAILING_RECHUNK = re.compile(r"#r\d+$")


def load_policy(path=None):
    with open(path or POLICY_PATH) as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or "families" not in doc:
        raise ValueError(f"{path or POLICY_PATH}: no 'families' key")
    return doc


def load_manifest(path=None):
    """The ingestion receipt. Absent is not an error — it means nothing has been
    ingested through the sanctioned path yet, which the gate reports as missing
    provenance rather than as a clean run."""
    try:
        with open(path or MANIFEST_PATH) as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"families": {}}


def save_manifest(manifest, path=None):
    path = path or MANIFEST_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --------------------------------------------------------------- discovery ----

def family_root(fam):
    root = fam.get("root")
    if not root:
        return None
    root = os.path.expanduser(root)
    return root if os.path.isabs(root) else os.path.join(REPO, root)


def discover(fam):
    """Eligible source files for one family, as paths relative to its root.

    Exclusions are matched against the relative path with fnmatch, so a pattern
    may name a file ("*secret*") or a subtree ("**/backups/**").
    """
    root = family_root(fam)
    if not root or not os.path.isdir(root):
        return []
    includes = fam.get("include") or []
    excludes = fam.get("exclude") or []
    # A source too small to hold a finding is not a coverage failure when it is
    # absent — it is a file with nothing in it. Without this, two 2.5KB /clear
    # transcripts would hold the gate red forever and teach everyone to ignore it.
    min_bytes = int(fam.get("min_bytes", 0))
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if not any(_match(rel, pat) for pat in includes):
                continue
            if any(_match(rel, pat) for pat in excludes):
                continue
            if min_bytes and os.path.getsize(full) < min_bytes:
                continue
            found.append(rel)
    return sorted(found)


def _match(rel, pattern):
    """fnmatch, with '**/x/**' also matching a top-level 'x/...'.

    fnmatch has no notion of path depth, so "**/diagrams/**" alone would miss
    "diagrams/a.md" at the root of the tree. Both forms are tried.
    """
    if fnmatch.fnmatch(rel, pattern):
        return True
    if pattern.startswith("**/") and fnmatch.fnmatch(rel, pattern[3:]):
        return True
    return False


# ------------------------------------------------------- what the KB holds ----

def ingested_identities(conn, fam):
    """The set of source identities the KB already holds for this family.

    An identity is whatever the family's source_key convention makes stable per
    source file. Returns {identity: newest_created_at}.
    """
    source = fam.get("kb_source")
    if not source:
        return {}
    style = fam.get("key_style", "path_colon_index")
    out = {}
    rows = conn.execute(
        "SELECT source_key, MAX(created_at) FROM knowledge_messages "
        "WHERE source = ? AND source_key IS NOT NULL GROUP BY source_key",
        (source,),
    )
    for key, created in rows:
        ident = identity_of(key, style, fam)
        if ident is None:
            continue
        if ident not in out or (created or "") > out[ident]:
            out[ident] = created
    return out


def identity_of(key, style, fam=None):
    if style == "path_colon_index":
        # Three conventions, one source file. 'x.md:3' is the original loader,
        # 'x.md:3#r0' is that row after rechunking, and 'x.md#r0' is a row the
        # rechunker produced from a doc the loader stored whole. Stripping only
        # the first two made 2,269 ingested documents read as orphans and the
        # pre-recovery docs coverage read 15 points lower than it was.
        return _TRAILING_INDEX.sub("", _TRAILING_RECHUNK.sub("", key))
    if style == "path_hash_index":
        base = _TRAILING_RECHUNK.sub("", key)
        # keys carry the family directory; the measurement is relative to root
        prefix = (fam or {}).get("root", "")
        if prefix and base.startswith(prefix.rstrip("/") + "/"):
            base = base[len(prefix.rstrip("/")) + 1:]
        return base
    if style == "session_triplet":
        # claude_code/<dir>/<session>/<idx>.<part>. The identity is the session id
        # alone: <dir> is whatever directory the transcript happened to sit in
        # ("-home-eric", or "subagents" for a delegated run), and a session uuid
        # is already unique without it.
        parts = key.split("/")
        return parts[2] if len(parts) >= 3 else None
    return None  # 'opaque' — not measurable by key


def path_identity(fam, rel):
    """The same identity, computed from a discovered file instead of a stored key."""
    if fam.get("key_style") == "session_triplet":
        return os.path.basename(rel)[:-len(".jsonl")] if rel.endswith(".jsonl") else rel
    return rel


# ----------------------------------------------------------- measurement ----

def measure_family(name, fam, conn, manifest, now=None):
    """One row of the coverage matrix, plus the violations it implies."""
    now = now or time.time()
    root = family_root(fam)
    rec = {
        "family": name,
        "expected": bool(fam.get("required")),
        "location": fam.get("root") or "(no filesystem root)",
        "kb_source": fam.get("kb_source"),
        "authority_class": fam.get("authority_class"),
        "ingestion": fam.get("ingest") or ("MISSING" if fam.get("ingestion_path") == "MISSING" else None),
        "measurable": fam.get("measurable", True),
        "violations": [],
    }

    if not rec["measurable"]:
        rec["coverage"] = None
        rec["status"] = ("COVERAGE NOT CURRENTLY MEASURABLE: "
                         + (fam.get("note") or "no filesystem denominator").strip().split("\n")[0])
        if fam.get("required") and fam.get("ingestion_path") == "MISSING":
            rec["violations"].append("INGESTION PATH MISSING — ARCHITECTURE DECISION REQUIRED")
        return rec

    eligible = discover(fam)
    ingested = ingested_identities(conn, fam)
    present = [f for f in eligible if path_identity(fam, f) in ingested]
    grace = float(fam.get("grace_hours", 0)) * 3600
    missing, in_grace = [], []
    for f in eligible:
        if path_identity(fam, f) in ingested:
            continue
        age = now - os.path.getmtime(os.path.join(root, f))
        (in_grace if age < grace else missing).append(f)

    rec["total_eligible"] = len(eligible)
    rec["ingested"] = len(present)
    rec["missing"] = len(missing)
    rec["in_grace"] = len(in_grace)
    rec["missing_files"] = missing
    # A source still inside its write window is not yet expected, so it belongs in
    # neither half of the ratio. Counting it as un-ingested drove coverage to 0%
    # for a family whose only file was three minutes old — a true statement about
    # the corpus and a useless one about the system.
    denom = len(eligible) - len(in_grace)
    rec["coverage"] = (len(present) / denom) if denom else 1.0
    rec["newest_source"] = _newest(root, eligible)
    rec["newest_ingested"] = max(
        (ingested[path_identity(fam, f)] for f in present
         if ingested.get(path_identity(fam, f))), default=None)

    # Drift: a file whose bytes no longer match what was ingested.
    fmani = (manifest.get("families", {}).get(name) or {}).get("files", {})
    changed, no_prov = [], []
    for f in present:
        entry = fmani.get(f)
        if not entry:
            no_prov.append(f)
            continue
        if entry.get("sha256") != sha256_file(os.path.join(root, f)):
            changed.append(f)
    rec["changed_since_ingest"] = changed
    rec["provenance_missing"] = no_prov

    if not fam.get("required"):
        rec["status"] = "NOT REQUIRED"
        return rec

    floor = float(fam.get("min_coverage", 1.0))
    if not eligible:
        rec["violations"].append("required family has no eligible sources — "
                                 "root missing or every file excluded")
    if rec["coverage"] < floor:
        rec["violations"].append(
            f"coverage {rec['coverage']:.1%} below required {floor:.0%} "
            f"({len(missing)} source(s) never ingested)")
    if fam.get("freshness") == "current" and changed:
        rec["violations"].append(
            f"{len(changed)} source(s) changed without re-ingestion")
    elif changed:
        rec["violations"].append(
            f"{len(changed)} source(s) changed without re-ingestion (freshness=bounded)")
    if fam.get("require_provenance") and no_prov:
        rec["violations"].append(
            f"{len(no_prov)} ingested source(s) have no provenance record")
    max_age = fam.get("max_age_days")
    if max_age and missing:
        newest_missing = max(os.path.getmtime(os.path.join(root, f)) for f in missing)
        lag_days = (now - newest_missing) / 86400
        if lag_days < float(max_age):
            rec["violations"].append(
                f"newest un-ingested source is {lag_days:.1f}d old, "
                f"inside the {max_age}d freshness bound — ingestion is not running")

    rec["status"] = "OK" if not rec["violations"] else "VIOLATION"
    return rec


def _newest(root, rels):
    if not rels:
        return None
    path = max(rels, key=lambda r: os.path.getmtime(os.path.join(root, r)))
    stamp = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(os.path.join(root, path))))
    return f"{stamp} {path}"


def measure_all(policy=None, db_path=None, manifest=None):
    policy = policy or load_policy()
    manifest = manifest if manifest is not None else load_manifest()
    conn = sqlite3.connect(f"file:{db_path or DB_PATH}?mode=ro", uri=True)
    try:
        return [measure_family(n, f or {}, conn, manifest)
                for n, f in policy["families"].items()]
    finally:
        conn.close()


# ── Closeout verdict ──────────────────────────────────────────────────────────
# One measurement, two consumers: gate_kb_source_coverage.py --closeout prints it
# and tools/development/cli.py closeout-check blocks on it. Written here rather
# than in either caller so there is no second place that decides which families
# may block a closeout.
#
# The split it makes is the one the POLICY ALREADY DECLARES, not a new judgement:
#
#   blocking         required AND measurable — a hole we can see and could have
#                    filled. chatgpt/claude_ai are not here.
#   policy_undecided required but measurable: false with ingestion_path: MISSING —
#                    there is no supported way to ingest them, so failing a
#                    closeout on them would be a gate that can never go green,
#                    and a gate that can never go green is a gate people learn to
#                    ignore. Reported loudly, every time, and never silently
#                    dropped: the family's own note says ARCHITECTURE DECISION
#                    REQUIRED, and until that decision exists this is the honest
#                    verdict.
#   unmeasurable     not required and not measurable — Layer-1 records, Hermes
#                    sessions, cards, runtime logs. Informational only.
#
# This function does NOT change any family's `required` flag, and the default
# gate mode still fails on policy_undecided, so the standing conflict stays
# visible instead of being resolved by a closeout convenience.
def closeout_verdict(policy=None, db_path=None, manifest=None):
    """Which KB source families may block a development-stage closeout.

    Fails closed: if the policy, the spine or a declared root cannot be read,
    that is returned as a blocker, because coverage that cannot be established
    is not coverage.
    """
    out = {"blocking": [], "policy_undecided": [], "unmeasurable": [],
           "ok": [], "ready": False}
    try:
        rows = measure_all(policy=policy, db_path=db_path, manifest=manifest)
    except Exception as exc:                       # unreadable policy/spine/root
        out["blocking"].append({
            "family": "(measurement)", "measurable": None,
            "violations": [f"KB coverage could not be measured — {exc}"]})
        return out

    for r in rows:
        entry = {"family": r["family"], "coverage": r.get("coverage"),
                 "measurable": r.get("measurable", True),
                 "violations": list(r.get("violations", [])),
                 "note_status": r.get("status")}
        if not r.get("expected"):
            out["unmeasurable" if not entry["measurable"] else "ok"].append(entry)
        elif not entry["measurable"]:
            out["policy_undecided"].append(entry)
        elif entry["violations"]:
            out["blocking"].append(entry)
        else:
            out["ok"].append(entry)

    out["ready"] = not out["blocking"]
    return out
