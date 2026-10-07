#!/usr/bin/env python3
"""test_install_session_end_hook.py — the SessionEnd hook installer.

The installer's whole job is to add one line of registration to a file it does
not own. Every case here is a way that could go wrong: losing an unrelated key,
duplicating on re-run, reshaping someone else's hook, or rewriting a file it
cannot parse. None of them touch ~/.claude/settings.json — each builds its own
settings file in a temp dir, so a pass means the MERGE is right rather than that
this machine happens to be configured correctly.

Plain-python, no pytest — the convention test_kb_coverage.py uses, and pytest is
not installed on either interpreter here.

  python3 tools/kb/tests/test_install_session_end_hook.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from kb import install_session_end_hook as ih  # noqa: E402

SCRIPT = os.path.join(REPO, "tools/kb/install_session_end_hook.py")

RESULTS = []


def check(name, ok):
    RESULTS.append((name, ok))
    print(f"{name}: {'PASS' if ok else 'FAIL'}")


def run(settings, *args):
    """Invoke the installer as a subprocess — the way a recovery script will."""
    return subprocess.run([sys.executable, SCRIPT, "--settings", settings, *args],
                          capture_output=True, text=True)


def write(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=2)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def session_end_commands(settings):
    return [h.get("command")
            for g in (settings.get("hooks") or {}).get("SessionEnd") or []
            for h in g.get("hooks") or []]


def main():
    with tempfile.TemporaryDirectory(prefix="cis-hookinstall-") as tmp:
        p = lambda n: os.path.join(tmp, n)  # noqa: E731

        # ── A file that does not exist yet is a first install, not an error ──
        a = p("absent.json")
        r = run(a, "--check")
        check("absent settings reports NOT REGISTERED", r.returncode == ih.MISSING)
        r = run(a)
        check("installs into a nonexistent settings file", r.returncode == ih.OK)
        check("installed registration names the tracked hook script",
              session_end_commands(read(a)) == [ih.HOOK_SCRIPT])

        # ── Re-running must not stack a second copy ──
        r = run(a)
        check("second run is a reported no-op",
              r.returncode == ih.OK and "ALREADY REGISTERED" in r.stdout)
        check("re-run does not duplicate the entry",
              session_end_commands(read(a)) == [ih.HOOK_SCRIPT])
        r = run(a, "--check")
        check("--check exits 0 once registered", r.returncode == ih.OK)

        # ── The machine-local keys are the whole reason this script exists ──
        b = p("personal.json")
        write(b, {
            "model": "opus",
            "theme": "dark",
            "autoMemoryEnabled": True,
            "permissions": {"allow": ["Bash(ls:*)"], "deny": ["Bash(rm:*)"]},
            "hooks": {
                "PreToolUse": [{"matcher": "Bash",
                                "hooks": [{"type": "command",
                                           "command": "/usr/local/bin/audit.sh"}]}],
                "SessionEnd": [{"hooks": [{"type": "command",
                                           "command": "/opt/other/thing.sh",
                                           "timeout": 10}]}],
            },
        })
        before = read(b)
        r = run(b)
        after = read(b)
        check("install into a populated settings file succeeds", r.returncode == ih.OK)
        check("unrelated top-level keys survive byte-for-byte",
              all(after.get(k) == before.get(k)
                  for k in ("model", "theme", "autoMemoryEnabled", "permissions")))
        check("an unrelated hook EVENT survives",
              after["hooks"]["PreToolUse"] == before["hooks"]["PreToolUse"])
        check("another SessionEnd hook is kept alongside ours",
              session_end_commands(after) == ["/opt/other/thing.sh", ih.HOOK_SCRIPT])
        check("the foreign SessionEnd group is not reshaped",
              after["hooks"]["SessionEnd"][0] == before["hooks"]["SessionEnd"][0])
        check("a backup of the previous settings was written",
              any(f.startswith("personal.json.bak-") for f in os.listdir(tmp)))

        # ── A config it cannot parse is not a config it may rewrite ──
        c = p("malformed.json")
        write(c, '{ "model": "opus", oops')
        raw = open(c, encoding="utf-8").read()
        r = run(c)
        check("malformed JSON is refused", r.returncode == ih.REFUSED)
        check("malformed JSON is left untouched",
              open(c, encoding="utf-8").read() == raw)

        d = p("badshape.json")
        write(d, {"hooks": {"SessionEnd": "not-a-list"}})
        raw = open(d, encoding="utf-8").read()
        r = run(d)
        check("an unexpected SessionEnd shape is refused", r.returncode == ih.REFUSED)
        check("an unexpected SessionEnd shape is left untouched",
              open(d, encoding="utf-8").read() == raw)

        e = p("badhooks.json")
        write(e, {"hooks": [1, 2, 3]})
        r = run(e)
        check('a non-object "hooks" is refused', r.returncode == ih.REFUSED)

        # ── Shapes that are odd but legal ──
        f = p("empty.json")
        write(f, "")
        r = run(f)
        check("an empty file installs cleanly", r.returncode == ih.OK
              and session_end_commands(read(f)) == [ih.HOOK_SCRIPT])

        g = p("otherevent.json")
        write(g, {"hooks": {"Stop": [{"hooks": [{"type": "command",
                                                 "command": "/x.sh"}]}]}})
        r = run(g)
        after = read(g)
        check("SessionEnd is created beside an existing event",
              r.returncode == ih.OK
              and session_end_commands(after) == [ih.HOOK_SCRIPT]
              and after["hooks"]["Stop"][0]["hooks"][0]["command"] == "/x.sh")

        # ── --dry-run must be exactly that ──
        h = p("dry.json")
        write(h, {"model": "opus"})
        raw = open(h, encoding="utf-8").read()
        r = run(h, "--dry-run")
        check("--dry-run writes nothing",
              r.returncode == ih.OK and open(h, encoding="utf-8").read() == raw)
        check("--dry-run names the keys it would preserve", "model" in r.stdout)

        # ── A registration with a hand-edited timeout is still a registration ──
        i = p("custom.json")
        write(i, {"hooks": {"SessionEnd": [{"hooks": [
            {"type": "command", "command": ih.HOOK_SCRIPT, "timeout": 60}]}]}})
        raw = open(i, encoding="utf-8").read()
        r = run(i)
        check("a deliberately customised registration is not overwritten",
              r.returncode == ih.OK and open(i, encoding="utf-8").read() == raw)

    # ── The thing being registered must actually exist and be runnable ──
    check("the hook script this installer registers is tracked and present",
          os.path.exists(ih.HOOK_SCRIPT))
    check("the hook script is executable", os.access(ih.HOOK_SCRIPT, os.X_OK))
    check("the registered timeout exceeds the script's own budget",
          ih.ENTRY["timeout"] > 240)

    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\n{passed}/{len(RESULTS)} passed.")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
