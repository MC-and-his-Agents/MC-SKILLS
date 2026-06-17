#!/usr/bin/env python3
"""Check whether a subagent report is eligible for control-plane consumption."""

from __future__ import annotations

import argparse
import json
import posixpath
from pathlib import Path
import sys
from typing import Any

import validate_structures


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_AUTHORITY_CLAIMS = {
    "state_transition",
    "shared_channel",
    "gate",
    "merge",
    "release",
    "closeout",
}


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def failure(file: str, field: str, message: str, suggested_action: str) -> dict[str, str]:
    return {
        "file": file,
        "field": field,
        "message": message,
        "suggestedAction": suggested_action,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_relative_path(path: str) -> str | None:
    if path.startswith("/"):
        return None
    if ".." in path.split("/"):
        return None
    normalized = posixpath.normpath(path)
    if normalized in {"", "."} or normalized == ".." or normalized.startswith("../"):
        return None
    return normalized


def path_allowed(path: str, allowed_paths: list[str]) -> bool:
    normalized = normalize_relative_path(path)
    if normalized is None:
        return False
    for allowed in allowed_paths:
        if allowed.strip() == ".":
            return True
        allowed_normalized = normalize_relative_path(allowed)
        if allowed_normalized is None:
            continue
        if normalized == allowed_normalized or normalized.startswith(allowed_normalized.rstrip("/") + "/"):
            return True
    return False


def check_subagent_report(root: Path, assignment_path: Path, report_path: Path) -> dict[str, Any]:
    assignment_file = rel(root, assignment_path)
    report_file = rel(root, report_path)
    failures: list[dict[str, str]] = []
    failures.extend(validate_structures.validate_file(root, assignment_path))
    failures.extend(validate_structures.validate_file(root, report_path))
    if failures:
        return {
            "status": "fail",
            "assignmentFile": assignment_file,
            "reportFile": report_file,
            "summary": {"eligible": False},
            "failures": failures,
        }

    assignment = load_json(assignment_path)
    report = load_json(report_path)
    context = report.get("provider_context")
    if not isinstance(context, dict):
        failures.append(
            failure(report_file, "provider_context", "subagent report missing provider context", "add provider_context")
        )
    else:
        checks = {
            "provider": assignment.get("provider"),
            "assignment_id": assignment.get("assignment_id"),
            "agent_id": assignment.get("agent_id"),
            "thread_id": assignment.get("thread_id"),
        }
        for field, expected in checks.items():
            observed = context.get(field)
            if observed != expected:
                failures.append(
                    failure(
                        report_file,
                        f"provider_context.{field}",
                        f"{field} does not match assignment",
                        f"set provider_context.{field} to {expected}",
                    )
                )
        if not context.get("report_locator"):
            failures.append(
                failure(
                    report_file,
                    "provider_context.report_locator",
                    "report locator is required",
                    "record the report artifact locator",
                )
            )
        elif context.get("report_locator") not in {assignment.get("report_output_path"), report_file}:
            failures.append(
                failure(
                    report_file,
                    "provider_context.report_locator",
                    "report locator does not match assignment output path",
                    "align provider_context.report_locator with report_output_path",
                )
            )
        validation = context.get("validation")
        if not isinstance(validation, dict) or validation.get("status") not in {"pass", "fail"}:
            failures.append(
                failure(
                    report_file,
                    "provider_context.validation",
                    "validation result is required",
                    "record validation.status as pass or fail",
                )
            )
        elif report.get("status") == "completed" and validation.get("status") != "pass":
            failures.append(
                failure(
                    report_file,
                    "provider_context.validation.status",
                    "completed subagent report requires passing validation",
                    "run required validation or mark report non-complete",
                )
            )
        changed_paths = context.get("changed_paths")
        allowed_write_paths = assignment.get("allowed_write_paths", [])
        if isinstance(changed_paths, list):
            for index, item in enumerate(changed_paths):
                path = item.get("path") if isinstance(item, dict) else None
                if isinstance(path, str) and not path_allowed(path, allowed_write_paths):
                    failures.append(
                        failure(
                            report_file,
                            f"provider_context.changed_paths[{index}].path",
                            "changed path is outside allowed_write_paths",
                            "move the change back into assigned write scope or request a thread worker",
                        )
                    )
        claims = set(context.get("authority_claims", [])) if isinstance(context.get("authority_claims"), list) else set()
        forbidden_claims = sorted(claims & FORBIDDEN_AUTHORITY_CLAIMS)
        if forbidden_claims:
            failures.append(
                failure(
                    report_file,
                    "provider_context.authority_claims",
                    "subagent provider cannot own control-plane authority",
                    "remove forbidden claims: " + ", ".join(forbidden_claims),
                )
            )

    if assignment.get("instruction_id") != report.get("instruction_id"):
        failures.append(
            failure(report_file, "instruction_id", "instruction_id does not match assignment", "report the assigned instruction_id")
        )
    if assignment.get("expected_report_type") != report.get("report_type"):
        failures.append(
            failure(report_file, "report_type", "report_type does not match assignment", "use the expected report type")
        )

    status = "pass" if not failures else "fail"
    return {
        "status": status,
        "assignmentFile": assignment_file,
        "reportFile": report_file,
        "summary": {
            "eligible": status == "pass",
            "assignmentId": assignment.get("assignment_id"),
            "agentId": assignment.get("agent_id"),
            "threadId": assignment.get("thread_id"),
        },
        "failures": failures,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a subagent report before consumption.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--assignment-file", required=True, help="Subagent assignment JSON file.")
    parser.add_argument("--report-file", required=True, help="Subagent report JSON file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    assignment_path = Path(args.assignment_file)
    report_path = Path(args.report_file)
    assignment_path = assignment_path if assignment_path.is_absolute() else root / assignment_path
    report_path = report_path if report_path.is_absolute() else root / report_path
    payload = check_subagent_report(root, assignment_path, report_path)
    emit(payload)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
