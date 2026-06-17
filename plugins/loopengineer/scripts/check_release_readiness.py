#!/usr/bin/env python3
"""Check whether the repository is ready for a manual release action."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import check_version


ROOT = Path(__file__).resolve().parents[1]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def failure(
    check: str,
    file: str,
    field: str,
    message: str,
    suggested_action: str,
) -> dict[str, str]:
    return {
        "check": check,
        "file": file,
        "field": field,
        "message": message,
        "suggestedAction": suggested_action,
    }


def read_json(root: Path, path: Path, check: str, field: str, failures: list[dict[str, str]]):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - readiness must report all failures as JSON.
        failures.append(
            failure(
                check,
                relative_path(root, path),
                field,
                f"cannot read JSON: {exc}",
                "fix JSON syntax or restore the expected file",
            )
        )
        return None
    if not isinstance(data, dict):
        failures.append(
            failure(
                check,
                relative_path(root, path),
                field,
                "JSON document must be an object",
                "replace the file with an object containing the required metadata",
            )
        )
        return None
    return data


def parse_skill_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if line.startswith("  - ") and current_key:
                data.setdefault(current_key, []).append(line[4:].strip().strip('"').strip("'"))
                continue
            if not line.startswith(" ") and ":" in line:
                key, value = line.split(":", 1)
                current_key = key
                value = value.strip()
                if value:
                    data[key] = value.strip('"').strip("'")
                else:
                    data[key] = []
    return data


def add_version_failures(version_payload: dict[str, Any], failures: list[dict[str, str]]) -> None:
    for item in version_payload["failures"]:
        failures.append(
            failure(
                "version",
                item["file"],
                item["field"],
                item["message"],
                item["suggestedAction"],
            )
        )


def check_plugin_manifest(root: Path, version: str | None, failures: list[dict[str, str]]) -> None:
    path = root / ".codex-plugin/plugin.json"
    data = read_json(root, path, "plugin_manifest", "version", failures)
    if data is None:
        return
    plugin_version = data.get("version")
    if not isinstance(plugin_version, str) or not plugin_version:
        failures.append(
            failure(
                "plugin_manifest",
                ".codex-plugin/plugin.json",
                "version",
                "version must be a non-empty string",
                "set .codex-plugin/plugin.json.version to match VERSION",
            )
        )
        return
    if version is not None and plugin_version != version:
        failures.append(
            failure(
                "plugin_manifest",
                ".codex-plugin/plugin.json",
                "version",
                f"{plugin_version!r} does not match VERSION {version!r}",
                "update .codex-plugin/plugin.json.version or VERSION so they match",
            )
        )


def check_schema_instances(root: Path, failures: list[dict[str, str]]) -> None:
    for path in sorted((root / "schemas").glob("v*/examples/*.json")) + sorted(
        (root / "schemas").glob("v*/*.default.json")
    ):
        data = read_json(root, path, "schema_examples", "schema metadata", failures)
        if data is None:
            continue
        rel = relative_path(root, path)
        for field in ("schemaVersion", "kind"):
            if not data.get(field):
                failures.append(
                    failure(
                        "schema_examples",
                        rel,
                        field,
                        f"{field} is required",
                        f"declare {field} in the schema example metadata",
                    )
                )


def check_skill_paths(root: Path, failures: list[dict[str, str]]) -> None:
    for path in sorted((root / "skills").glob("*/skill.yaml")):
        rel = relative_path(root, path)
        try:
            data = parse_skill_yaml(path)
        except Exception as exc:  # noqa: BLE001 - readiness must report all failures as JSON.
            failures.append(
                failure("skill_paths", rel, "skill.yaml", f"cannot read skill.yaml: {exc}", "fix skill metadata")
            )
            continue
        entrypoint = data.get("entrypoint")
        if not isinstance(entrypoint, str) or not entrypoint:
            failures.append(
                failure(
                    "skill_paths",
                    rel,
                    "entrypoint",
                    "entrypoint must be declared",
                    "declare entrypoint in skill.yaml",
                )
            )
        elif not (path.parent / entrypoint).is_file():
            failures.append(
                failure(
                    "skill_paths",
                    rel,
                    "entrypoint",
                    f"{entrypoint} does not exist",
                    "point entrypoint at an existing file in the skill directory",
                )
            )

        reads = data.get("reads")
        if not isinstance(reads, list):
            failures.append(
                failure(
                    "skill_paths",
                    rel,
                    "reads",
                    "reads must be declared as a list",
                    "declare reads paths in skill.yaml",
                )
            )
            continue
        for read_path in reads:
            if not (root / read_path).exists():
                failures.append(
                    failure(
                        "skill_paths",
                        rel,
                        "reads",
                        f"{read_path} does not exist",
                        "remove the stale reads path or add the referenced file",
                    )
                )


def run_unittest(root: Path, failures: list[dict[str, str]]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        failures.append(
            failure(
                "unittest",
                "tests",
                "unittest discover",
                "python3 -m unittest discover -s tests failed",
                "fix failing tests before release",
            )
        )
    return {
        "command": "python3 -m unittest discover -s tests",
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
    }


def run_checks(root: Path = ROOT, *, run_tests: bool = True) -> dict[str, Any]:
    root = root.resolve()
    failures: list[dict[str, str]] = []
    version_payload = check_version.run_checks(root)
    add_version_failures(version_payload, failures)
    version = version_payload["checkedVersion"]

    check_plugin_manifest(root, version, failures)
    check_schema_instances(root, failures)
    check_skill_paths(root, failures)
    test_result = run_unittest(root, failures) if run_tests else {
        "command": "python3 -m unittest discover -s tests",
        "status": "skipped",
        "returncode": None,
    }

    checks = [
        {"name": "version", "status": version_payload["status"]},
        {
            "name": "plugin_manifest",
            "status": "fail" if any(item["check"] == "plugin_manifest" for item in failures) else "pass",
        },
        {
            "name": "schema_examples",
            "status": "fail" if any(item["check"] == "schema_examples" for item in failures) else "pass",
        },
        {
            "name": "skill_paths",
            "status": "fail" if any(item["check"] == "skill_paths" for item in failures) else "pass",
        },
        {"name": "unittest", "status": test_result["status"]},
    ]
    return {
        "status": "pass" if not failures else "fail",
        "checkedVersion": version,
        "checks": checks,
        "failures": failures,
        "testResult": test_result,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LoopEngineer release readiness without creating release artifacts."
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Repository root to check. Defaults to the current LoopEngineer checkout.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip unittest execution. Intended for focused fixture tests only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    payload = run_checks(Path(args.root), run_tests=not args.skip_tests)
    emit(payload)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
