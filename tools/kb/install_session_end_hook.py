#!/usr/bin/env python3
"""install_session_end_hook.py — make the CIS SessionEnd ingestion hook
reproducible from the repository, without the repository ever holding Eric's
Claude Code settings.

WHY THIS EXISTS
---------------
tools/kb/session_end_ingest.sh is the mechanism; it is tracked. But the hook
only fires because ~/.claude/settings.json names it, and that file is MACHINE-
LOCAL: it carries a model choice, a theme and a permissions allowlist that are
nobody else's business and must never enter Git. So a clean recovery would get
the script and silently not get the behaviour — the coverage gate would turn
claude_code_sessions red two days later and nobody would know why.

This script closes that gap from the other direction: the repository carries
the REGISTRATION, not the settings. It merges one SessionEnd entry into whatever
settings.json already exists and leaves every other key untouched.

WHAT IT GUARANTEES
------------------
  - idempotent: re-running makes no change once the hook is present, and
    --check exits non-zero only when registration is actually missing, so it
    is safe in a recovery script or a cron.
  - additive: unrelated top-level keys (model, theme, permissions, ...) and
    unrelated hook events are read, preserved and written back verbatim. Other
    SessionEnd hooks someone else registered are kept alongside ours.
  - never destructive: the previous file is copied to settings.json.bak-<utc>
    before the first write, and the new content is written to a temp file in
    the same directory and os.replace()d in, so an interrupted run cannot
    leave a truncated settings.json behind.
  - refuses rather than guesses: settings.json that is present but not valid
    JSON, or whose "hooks"/"SessionEnd" shape is not what Claude Code
    documents, is reported and left alone. Repairing a malformed personal
    config is not this script's business.

  python3 tools/kb/install_session_end_hook.py            # install / verify
  python3 tools/kb/install_session_end_hook.py --check    # report only, exit 1 if absent
  python3 tools/kb/install_session_end_hook.py --dry-run  # print the merge, write nothing
  python3 tools/kb/install_session_end_hook.py --settings PATH

Exit codes: 0 registered (or installed), 1 not registered (--check), 2 refused.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK_SCRIPT = os.path.join(REPO, "tools/kb/session_end_ingest.sh")
DEFAULT_SETTINGS = os.path.expanduser("~/.claude/settings.json")
EVENT = "SessionEnd"

# The single entry this script owns. Timeout is deliberately above the script's
# own BUDGET=240 ceiling so session_end_ingest.sh always gets to write its own
# FAIL line rather than being killed mid-run; see the comment there.
ENTRY = {
    "type": "command",
    "command": HOOK_SCRIPT,
    "timeout": 300,
    "statusMessage": "Ingesting session into CIS knowledge base...",
}

REFUSED, MISSING, OK = 2, 1, 0


def load(path):
    """(settings, error). A file that does not exist is {} and no error — a
    first-time install is the normal case, not a problem."""
    if not os.path.exists(path):
        return {}, None
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return None, f"cannot read {path}: {exc}"
    if not text.strip():
        return {}, None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"{path} is not valid JSON ({exc}); refusing to rewrite it"
    if not isinstance(data, dict):
        return None, f"{path} is not a JSON object; refusing to rewrite it"
    return data, None


def registered(settings):
    """Is our command already registered under SessionEnd?

    Matched on the command string only. A registration that points at our
    script but carries a different timeout or status message is still a
    registration — rewriting someone's deliberate timeout would be exactly the
    kind of silent overreach this script exists to avoid.
    """
    hooks = settings.get("hooks")
    events = hooks.get(EVENT) if isinstance(hooks, dict) else None
    for group in events if isinstance(events, list) else []:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks") or []:
            if isinstance(hook, dict) and hook.get("command") == HOOK_SCRIPT:
                return True
    return False


def shape_error(settings):
    """Whether "hooks"/SessionEnd is a shape we can safely extend."""
    hooks = settings.get("hooks")
    if hooks is not None and not isinstance(hooks, dict):
        return 'settings "hooks" is not an object; refusing to rewrite it'
    events = (hooks or {}).get(EVENT)
    if events is not None and not isinstance(events, list):
        return f'settings hooks["{EVENT}"] is not a list; refusing to rewrite it'
    for group in events or []:
        if not isinstance(group, dict):
            return (f'settings hooks["{EVENT}"] holds a non-object entry; '
                    "refusing to rewrite it")
        inner = group.get("hooks")
        if inner is not None and not isinstance(inner, list):
            return (f'settings hooks["{EVENT}"] holds a group whose "hooks" is '
                    "not a list; refusing to rewrite it")
    return None


def merge(settings):
    """settings with our entry added. Appends a new matcher group rather than
    editing an existing one, so a group someone else configured — possibly with
    its own matcher — is never reshaped by us."""
    out = dict(settings)
    hooks = dict(out.get("hooks") or {})
    events = list(hooks.get(EVENT) or [])
    events.append({"hooks": [dict(ENTRY)]})
    hooks[EVENT] = events
    out["hooks"] = hooks
    return out


def write_atomic(path, settings):
    """Back up, then replace in one atomic step. Returns the backup path or None."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    backup = None
    if os.path.exists(path):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = f"{path}.bak-{stamp}"
        shutil.copy2(path, backup)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return backup


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--settings", default=DEFAULT_SETTINGS,
                    help=f"settings file to register in (default {DEFAULT_SETTINGS})")
    ap.add_argument("--check", action="store_true",
                    help="report registration status only; exit 1 if absent")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be written; change nothing")
    args = ap.parse_args()

    if not os.path.exists(HOOK_SCRIPT):
        print(f"REFUSED: hook script missing: {HOOK_SCRIPT}", file=sys.stderr)
        return REFUSED
    if not os.access(HOOK_SCRIPT, os.X_OK):
        # Git preserves the executable bit, so this normally means a checkout
        # through an archive or a filesystem that dropped the mode.
        print(f"REFUSED: hook script is not executable: {HOOK_SCRIPT}\n"
              f"  fix with: chmod +x {HOOK_SCRIPT}", file=sys.stderr)
        return REFUSED

    settings, err = load(args.settings)
    if err:
        print(f"REFUSED: {err}", file=sys.stderr)
        return REFUSED

    # Shape BEFORE registration, in every mode including --check: "is our hook
    # registered?" is not a question that can be answered honestly against a
    # structure we do not recognise, and answering it anyway is how a reporting
    # mode turns into a traceback.
    err = shape_error(settings)
    if err:
        print(f"REFUSED: {err}", file=sys.stderr)
        return REFUSED

    if registered(settings):
        print(f"ALREADY REGISTERED: {EVENT} -> {HOOK_SCRIPT}")
        print(f"  settings: {args.settings}")
        return OK

    if args.check:
        print(f"NOT REGISTERED: {EVENT} -> {HOOK_SCRIPT}")
        print(f"  settings: {args.settings}")
        print("  install with: python3 tools/kb/install_session_end_hook.py")
        return MISSING

    merged = merge(settings)

    if args.dry_run:
        print(f"DRY RUN — would add to {args.settings}:")
        print(json.dumps({"hooks": {EVENT: merged["hooks"][EVENT]}}, indent=2))
        kept = sorted(k for k in settings if k != "hooks")
        print(f"  preserved top-level keys: {', '.join(kept) or '(none)'}")
        return OK

    backup = write_atomic(args.settings, merged)
    print(f"INSTALLED: {EVENT} -> {HOOK_SCRIPT}")
    print(f"  settings: {args.settings}")
    if backup:
        print(f"  backup:   {backup}")
    print("  takes effect for sessions started after this point.")
    return OK


if __name__ == "__main__":
    sys.exit(main())
