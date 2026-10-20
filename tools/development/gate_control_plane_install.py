#!/usr/bin/env python3
"""Read-only verifier for promotion into the host trust root."""
import argparse
import hashlib
import json
import os
import stat
import sys

MANIFEST_VERSIONS = {
    "cis-control-plane-release-v1",
    "cis-control-plane-release-v2",
}


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contained(base, relative):
    if not isinstance(relative, str) or not relative or os.path.isabs(relative):
        return None
    base_real = os.path.realpath(base)
    candidate = os.path.realpath(os.path.join(base_real, relative))
    if candidate == base_real or not candidate.startswith(base_real + os.sep):
        return None
    return candidate


def _ownership_chain(path, root, expected_uid, expected_gid):
    failures = []
    current = os.path.realpath(path)
    root_real = os.path.realpath(root)
    while True:
        try:
            info = os.stat(current)
        except OSError as exc:
            failures.append(f"cannot stat ownership chain {current}: {exc}")
            break
        if info.st_uid != expected_uid or info.st_gid != expected_gid:
            failures.append(
                f"ownership mismatch: {current} is {info.st_uid}:{info.st_gid}, "
                f"expected {expected_uid}:{expected_gid}")
        if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            failures.append(f"group/world-writable control path: {current}")
        if current == root_real:
            break
        parent = os.path.dirname(current)
        if parent == current or not current.startswith(root_real + os.sep):
            failures.append(f"ownership chain escaped control root: {current}")
            break
        current = parent
    return failures


def _selected_tree_files(root, suffixes, ignored_directories=()):
    """Return a deterministic relative-path inventory for a reviewed tree."""
    inventory = {}
    relative_directories = set()
    rejected = []
    for current, directories, files in os.walk(root, followlinks=False):
        kept_directories = []
        for name in sorted(directories):
            path = os.path.join(current, name)
            if os.path.islink(path):
                rejected.append(f"symlinked directory in tree: {path}")
            elif name not in ignored_directories:
                kept_directories.append(name)
                relative_directories.add(os.path.relpath(path, root))
        directories[:] = kept_directories
        for name in sorted(files):
            path = os.path.join(current, name)
            if os.path.islink(path) or not os.path.isfile(path):
                rejected.append(f"non-regular file in tree: {path}")
                continue
            if suffixes and not any(name.endswith(suffix) for suffix in suffixes):
                continue
            relative = os.path.relpath(path, root)
            inventory[relative] = path
    return inventory, relative_directories, rejected


def _evaluate_tree(artifact, *, source_root, installed_root,
                   expected_uid, expected_gid):
    failures = []
    source = _contained(source_root, artifact["source"])
    destination = _contained(installed_root, artifact["destination"])
    row = {"source": source, "destination": destination, "kind": "tree",
           "passed": False}
    if source is None or destination is None:
        return row, ["tree has an escaping or absolute relative path"]
    if os.path.islink(source) or not os.path.isdir(source):
        return row, [f"tree source is absent, non-directory, or symlinked: {source}"]
    if os.path.islink(destination) or not os.path.isdir(destination):
        return row, [f"installed tree is absent, non-directory, or symlinked: {destination}"]
    suffixes = artifact["include_suffixes"]
    allowed_extra_files = artifact["allowed_extra_files"]
    if (not isinstance(suffixes, list) or not suffixes
            or any(not isinstance(value, str) or not value.startswith(".")
                   for value in suffixes)):
        return row, ["tree include_suffixes must be a non-empty list of suffixes"]
    if (not isinstance(allowed_extra_files, list)
            or any(not isinstance(value, str) or not value
                   or os.path.isabs(value) or ".." in value.split(os.sep)
                   for value in allowed_extra_files)):
        return row, ["tree allowed_extra_files must contain safe relative paths"]
    try:
        file_mode = int(artifact["file_mode"], 8)
        dir_mode = int(artifact["dir_mode"], 8)
    except (TypeError, ValueError):
        return row, ["tree modes must be octal text"]

    source_files, source_directories, source_rejected = _selected_tree_files(
        source, suffixes, ignored_directories={"__pycache__"})
    installed_files, installed_directories, installed_rejected = (
        _selected_tree_files(destination, []))
    failures.extend(source_rejected)
    failures.extend(installed_rejected)
    expected = set(source_files)
    actual = set(installed_files)
    for relative in sorted(expected - actual):
        failures.append(f"installed tree file absent: {destination}/{relative}")
    undeclared = actual - expected - set(allowed_extra_files)
    for relative in sorted(undeclared):
        failures.append(f"undeclared installed tree file: {destination}/{relative}")
    for relative in sorted(source_directories - installed_directories):
        failures.append(f"installed tree directory absent: {destination}/{relative}")
    for relative in sorted(installed_directories - source_directories):
        failures.append(f"undeclared installed tree directory: {destination}/{relative}")
    aggregate = hashlib.sha256()
    for relative in sorted(expected & actual):
        source_hash = _sha256_file(source_files[relative])
        installed_path = installed_files[relative]
        installed_hash = _sha256_file(installed_path)
        aggregate.update(relative.encode("utf-8") + b"\0")
        aggregate.update(source_hash.encode("ascii") + b"\n")
        if source_hash != installed_hash:
            failures.append(f"installed bytes differ from reviewed source: {installed_path}")
        actual_mode = stat.S_IMODE(os.stat(installed_path).st_mode)
        if actual_mode != file_mode:
            failures.append(
                f"mode mismatch: {installed_path} is {actual_mode:04o}, "
                f"expected {file_mode:04o}")
        failures.extend(_ownership_chain(
            installed_path, installed_root, expected_uid, expected_gid))
    for current, directories, _ in os.walk(destination, followlinks=False):
        for directory in [current] + [os.path.join(current, name)
                                      for name in directories]:
            actual_mode = stat.S_IMODE(os.stat(directory).st_mode)
            if actual_mode != dir_mode:
                failures.append(
                    f"directory mode mismatch: {directory} is {actual_mode:04o}, "
                    f"expected {dir_mode:04o}")
            failures.extend(_ownership_chain(
                directory, installed_root, expected_uid, expected_gid))
    row["file_count"] = len(expected)
    row["inventory_sha256"] = aggregate.hexdigest()
    row["passed"] = not failures
    return row, failures


def evaluate(manifest, *, source_root, control_root=None,
             expected_uid=0, expected_gid=0):
    failures = []
    checks = []
    if not isinstance(manifest, dict) or set(manifest) != {
            "manifest_version", "control_root", "artifacts"}:
        return {"passed": False, "checks": [],
                "failures": ["release manifest shape mismatch"]}
    if manifest["manifest_version"] not in MANIFEST_VERSIONS:
        failures.append("unsupported release manifest version")
    declared_root = manifest["control_root"]
    installed_root = os.path.realpath(control_root or declared_root)
    if not os.path.isabs(declared_root):
        failures.append("manifest control_root must be absolute")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        failures.append("release manifest must declare artifacts")
        artifacts = []
    destinations = set()
    for index, artifact in enumerate(artifacts):
        label = f"artifact[{index}]"
        if (isinstance(artifact, dict)
                and artifact.get("kind") == "tree"):
            if set(artifact) != {"source", "destination", "kind",
                                 "include_suffixes", "allowed_extra_files",
                                 "file_mode", "dir_mode"}:
                failures.append(f"{label} tree shape mismatch")
                continue
            destination = _contained(installed_root, artifact["destination"])
            if destination in destinations:
                failures.append(f"duplicate installed destination: {destination}")
                continue
            destinations.add(destination)
            row, tree_failures = _evaluate_tree(
                artifact, source_root=source_root,
                installed_root=installed_root,
                expected_uid=expected_uid, expected_gid=expected_gid)
            checks.append(row)
            failures.extend(f"{label}: {reason}" for reason in tree_failures)
            continue
        if not isinstance(artifact, dict) or set(artifact) != {
                "source", "destination", "mode"}:
            failures.append(f"{label} shape mismatch")
            continue
        source = _contained(source_root, artifact["source"])
        destination = _contained(installed_root, artifact["destination"])
        if source is None or destination is None:
            failures.append(f"{label} has an escaping or absolute relative path")
            continue
        if destination in destinations:
            failures.append(f"duplicate installed destination: {destination}")
            continue
        destinations.add(destination)
        try:
            expected_mode = int(artifact["mode"], 8)
        except (TypeError, ValueError):
            failures.append(f"{label} mode is not octal text")
            continue
        row = {"source": source, "destination": destination, "passed": False}
        checks.append(row)
        if os.path.islink(source) or not os.path.isfile(source):
            failures.append(f"source is absent, non-regular, or symlinked: {source}")
            continue
        if os.path.islink(destination) or not os.path.isfile(destination):
            failures.append(f"installed file is absent, non-regular, or symlinked: {destination}")
            continue
        source_hash = _sha256_file(source)
        installed_hash = _sha256_file(destination)
        row["source_sha256"] = source_hash
        row["installed_sha256"] = installed_hash
        if source_hash != installed_hash:
            failures.append(f"installed bytes differ from reviewed source: {destination}")
        actual_mode = stat.S_IMODE(os.stat(destination).st_mode)
        row["mode"] = format(actual_mode, "04o")
        if actual_mode != expected_mode:
            failures.append(
                f"mode mismatch: {destination} is {actual_mode:04o}, "
                f"expected {expected_mode:04o}")
        ownership_failures = _ownership_chain(
            destination, installed_root, expected_uid, expected_gid)
        failures.extend(ownership_failures)
        row["passed"] = (source_hash == installed_hash
                         and actual_mode == expected_mode
                         and not ownership_failures)
    return {"passed": not failures, "checks": checks, "failures": failures,
            "source_root": os.path.realpath(source_root),
            "control_root": installed_root}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="config/control-plane-release.json")
    parser.add_argument("--source-root", default=os.getcwd())
    parser.add_argument("--control-root")
    args = parser.parse_args(argv)
    try:
        with open(args.manifest, encoding="utf-8") as handle:
            manifest = json.load(handle)
        result = evaluate(manifest, source_root=args.source_root,
                          control_root=args.control_root)
    except (OSError, ValueError) as exc:
        result = {"passed": False, "checks": [], "failures": [str(exc)]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
