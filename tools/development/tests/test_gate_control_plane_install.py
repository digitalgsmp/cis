#!/usr/bin/env python3
import os
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.development.gate_control_plane_install import evaluate


def _fixture(tmp):
    source_root = os.path.join(tmp, "source")
    control_root = os.path.join(tmp, "control")
    os.makedirs(os.path.join(source_root, "src"))
    os.makedirs(os.path.join(control_root, "bin"))
    os.chmod(control_root, 0o755)
    os.chmod(os.path.join(control_root, "bin"), 0o755)
    source = os.path.join(source_root, "src", "dispatch.py")
    installed = os.path.join(control_root, "bin", "cis-dispatch")
    for path in (source, installed):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("reviewed bytes\n")
    os.chmod(installed, 0o555)
    manifest = {
        "manifest_version": "cis-control-plane-release-v1",
        "control_root": "/opt/cis-control",
        "artifacts": [{"source": "src/dispatch.py",
                       "destination": "bin/cis-dispatch", "mode": "0555"}],
    }
    return manifest, source_root, control_root, installed


def _evaluate(manifest, source_root, control_root):
    return evaluate(manifest, source_root=source_root, control_root=control_root,
                    expected_uid=os.getuid(), expected_gid=os.getgid())


def test_matching_release_passes():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, source_root, control_root, _ = _fixture(tmp)
        assert _evaluate(manifest, source_root, control_root)["passed"] is True


def test_changed_installed_bytes_fail():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, source_root, control_root, installed = _fixture(tmp)
        os.chmod(installed, 0o755)
        with open(installed, "a", encoding="utf-8") as handle:
            handle.write("changed\n")
        os.chmod(installed, 0o555)
        result = _evaluate(manifest, source_root, control_root)
        assert result["passed"] is False
        assert any("bytes differ" in reason for reason in result["failures"])


def test_writable_installed_mode_fails():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, source_root, control_root, installed = _fixture(tmp)
        os.chmod(installed, 0o775)
        result = _evaluate(manifest, source_root, control_root)
        assert result["passed"] is False
        assert any("mode mismatch" in reason for reason in result["failures"])
        assert any("group/world-writable" in reason for reason in result["failures"])


def _tree_fixture(tmp):
    source_root = os.path.join(tmp, "source")
    control_root = os.path.join(tmp, "control")
    source_tree = os.path.join(source_root, "gates")
    installed_tree = os.path.join(control_root, "runtime", "gates")
    os.makedirs(source_tree)
    os.makedirs(installed_tree)
    for directory in (control_root, os.path.join(control_root, "runtime")):
        os.chmod(directory, 0o755)
    for name in ("gate_one.py", "gate_two.sh"):
        for root in (source_tree, installed_tree):
            path = os.path.join(root, name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(f"reviewed {name}\n")
        os.chmod(os.path.join(installed_tree, name), 0o555)
    os.chmod(installed_tree, 0o555)
    manifest = {
        "manifest_version": "cis-control-plane-release-v2",
        "control_root": "/opt/cis-control",
        "artifacts": [{
            "source": "gates",
            "destination": "runtime/gates",
            "kind": "tree",
            "include_suffixes": [".py", ".sh"],
            "allowed_extra_files": [],
            "file_mode": "0555",
            "dir_mode": "0555",
        }],
    }
    return manifest, source_root, control_root, installed_tree


def test_matching_tree_release_passes():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, source_root, control_root, _ = _tree_fixture(tmp)
        assert _evaluate(manifest, source_root, control_root)["passed"] is True


def test_tree_release_rejects_undeclared_file():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, source_root, control_root, installed_tree = _tree_fixture(tmp)
        os.chmod(installed_tree, 0o755)
        extra = os.path.join(installed_tree, "stale_gate.py")
        with open(extra, "w", encoding="utf-8") as handle:
            handle.write("stale\n")
        os.chmod(extra, 0o444)
        os.chmod(installed_tree, 0o555)
        result = _evaluate(manifest, source_root, control_root)
        assert result["passed"] is False
        assert any("undeclared installed tree file" in reason
                   for reason in result["failures"])


def run():
    tests = [test_matching_release_passes, test_changed_installed_bytes_fail,
             test_writable_installed_mode_fails,
             test_matching_tree_release_passes,
             test_tree_release_rejects_undeclared_file]
    rows = []
    for test in tests:
        try:
            test()
            rows.append(f"{test.__name__}: PASS")
        except Exception as exc:
            rows.append(f"{test.__name__}: FAIL — {exc}")
    print("\n".join(rows))
    failed = [row for row in rows if ": FAIL" in row]
    print(f"\n{len(rows)-len(failed)}/{len(rows)} passed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
