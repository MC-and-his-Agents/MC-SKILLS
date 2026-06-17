#!/usr/bin/env python3
"""Check LoopEngineer version metadata consistency."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
EXPECTED_COMPATIBILITY_BY_VERSION = {
    "0.5.0": {
        "engineContractVersion": "1",
        "adapterContractVersion": "0",
    },
    "0.6.0": {
        "engineContractVersion": "1",
        "adapterContractVersion": "0",
    },
    "0.6.1": {
        "engineContractVersion": "1",
        "adapterContractVersion": "0",
    },
}


@dataclass(frozen=True)
class Finding:
    file: str
    field: str
    message: str
    suggested_action: str

    def as_dict(self) -> dict[str, str]:
        return {
            "file": self.file,
            "field": self.field,
            "message": self.message,
            "suggestedAction": self.suggested_action,
        }


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(root: Path, path: Path, field: str, findings: list[Finding]) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # noqa: BLE001 - CLI must turn all parse failures into JSON.
        findings.append(
            Finding(
                relative_path(root, path),
                field,
                f"cannot read JSON: {exc}",
                "fix JSON syntax or restore the expected file",
            )
        )
        return None
    if not isinstance(data, dict):
        findings.append(
            Finding(
                relative_path(root, path),
                field,
                "JSON document must be an object",
                "replace the file with an object containing the required metadata",
            )
        )
        return None
    return data


def parse_top_level_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if line.startswith(" "):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key] = value.strip().strip('"').strip("'")
    return data


def read_version(root: Path, findings: list[Finding]) -> str | None:
    path = root / "VERSION"
    try:
        version = path.read_text(encoding="utf-8").strip()
    except Exception as exc:  # noqa: BLE001 - CLI must turn all read failures into JSON.
        findings.append(
            Finding(
                "VERSION",
                "version",
                f"cannot read VERSION: {exc}",
                "restore VERSION with the current product SemVer",
            )
        )
        return None
    if not version:
        findings.append(
            Finding("VERSION", "version", "VERSION is empty", "write the current product SemVer")
        )
        return None
    if not SEMVER_RE.match(version):
        findings.append(
            Finding(
                "VERSION",
                "version",
                f"{version!r} is not MAJOR.MINOR.PATCH SemVer",
                "update VERSION to a SemVer value such as 0.1.0",
            )
        )
    return version


def check_metadata_version(root: Path, version: str | None, findings: list[Finding]) -> None:
    path = root / "metadata/loopengineer.json"
    data = load_json(root, path, "version", findings)
    if data is None:
        return
    metadata_version = data.get("version")
    if not isinstance(metadata_version, str) or not metadata_version:
        findings.append(
            Finding(
                "metadata/loopengineer.json",
                "version",
                "version must be a non-empty string",
                "set metadata/loopengineer.json.version to match VERSION",
            )
        )
        return
    if version is not None and metadata_version != version:
        findings.append(
            Finding(
                "metadata/loopengineer.json",
                "version",
                f"{metadata_version!r} does not match VERSION {version!r}",
                "update metadata/loopengineer.json.version or VERSION so they match",
            )
        )
    for field in (
        "pluginApiVersion",
        "protocolVersion",
        "engineContractVersion",
        "schemaMajorVersion",
        "skillContractVersion",
        "adapterContractVersion",
    ):
        if not isinstance(data.get(field), str) or not data.get(field):
            findings.append(
                Finding(
                    "metadata/loopengineer.json",
                    field,
                    f"{field} must be a non-empty string",
                    f"set metadata/loopengineer.json.{field}",
                )
            )
    expected = EXPECTED_COMPATIBILITY_BY_VERSION.get(version or "")
    if expected:
        for field, expected_value in expected.items():
            if data.get(field) != expected_value:
                findings.append(
                    Finding(
                        "metadata/loopengineer.json",
                        field,
                        f"{field} must be {expected_value!r} for version {version}",
                        f"set metadata/loopengineer.json.{field} to {expected_value}",
                    )
                )


def check_changelog(root: Path, version: str | None, findings: list[Finding]) -> None:
    if version is None:
        return
    path = root / "CHANGELOG.md"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - CLI must turn all read failures into JSON.
        findings.append(
            Finding(
                "CHANGELOG.md",
                "version entry",
                f"cannot read CHANGELOG.md: {exc}",
                "restore CHANGELOG.md with an entry for the current version",
            )
        )
        return
    if not re.search(rf"(?m)^##\s+{re.escape(version)}(?:\s|$)", text):
        findings.append(
            Finding(
                "CHANGELOG.md",
                "version entry",
                f"missing changelog section for {version}",
                "add a ## {version} release entry to CHANGELOG.md",
            )
        )


def check_skills(root: Path, findings: list[Finding]) -> None:
    skills_dir = root / "skills"
    for path in sorted(skills_dir.glob("*/skill.yaml")):
        rel = relative_path(root, path)
        try:
            data = parse_top_level_yaml(path)
        except Exception as exc:  # noqa: BLE001 - CLI must turn all parse failures into JSON.
            findings.append(
                Finding(rel, "skill.yaml", f"cannot read skill.yaml: {exc}", "fix skill metadata")
            )
            continue
        for field in ("version", "skillContractVersion"):
            if not data.get(field):
                findings.append(
                    Finding(
                        rel,
                        field,
                        f"{field} is required",
                        f"declare {field} in the skill metadata",
                    )
                )


def check_schemas(root: Path, findings: list[Finding]) -> None:
    schemas_dir = root / "schemas"
    for path in sorted(schemas_dir.glob("v*/*.schema.json")):
        rel = relative_path(root, path)
        data = load_json(root, path, "schema metadata", findings)
        if data is None:
            continue
        for field in ("$id", "schemaVersion", "kind"):
            if not data.get(field):
                findings.append(
                    Finding(
                        rel,
                        field,
                        f"{field} is required",
                        f"declare {field} in the schema metadata",
                    )
                )


def run_checks(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    findings: list[Finding] = []
    version = read_version(root, findings)
    check_metadata_version(root, version, findings)
    check_changelog(root, version, findings)
    check_skills(root, findings)
    check_schemas(root, findings)
    status = "pass" if not findings else "fail"
    return {
        "status": status,
        "checkedVersion": version,
        "failures": [finding.as_dict() for finding in findings],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LoopEngineer version metadata consistency."
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Repository root to check. Defaults to the current LoopEngineer checkout.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    payload = run_checks(Path(args.root))
    emit(payload)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
