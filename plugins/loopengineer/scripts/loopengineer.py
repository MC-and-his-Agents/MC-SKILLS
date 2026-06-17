#!/usr/bin/env python3
"""Runtime-neutral CLI/JSON LoopEngineer engine entrypoint."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


COMMANDS: dict[str, tuple[str, str]] = {
    "context-guard": ("context_guard", "context_guard.py"),
    "validate-structures": ("validate_structures", "validate_structures.py"),
    "state-digest": ("state_digest", "state_digest.py"),
    "loop-audit": ("loop_audit", "loop_audit.py"),
    "coordination-tax": ("coordination_tax", "coordination_tax.py"),
    "provider-select": ("provider_selection", "provider_selection.py"),
}


REMINDERS = [
    {
        "code": "route_before_escalating",
        "message": "route before escalating",
    },
    {
        "code": "context_guard_before_large_message",
        "message": "run context guard before large messages",
    },
    {
        "code": "no_inline_large_artifacts",
        "message": "do not inline large artifacts",
    },
    {
        "code": "no_state_transition_without_report_consumption",
        "message": "do not transition state before report consumption",
    },
    {
        "code": "do_not_start_runtime_unless_selected",
        "message": "do not start worker, scheduler, or watcher unless user, issue, or router selected it",
    },
]


DENIED_CAPABILITIES = [
    "consume_report",
    "github_mutation",
    "git_mutation",
    "ci_mutation",
    "pr_mutation",
    "release_mutation",
    "loom_fact_write",
    "worker_creation",
    "scheduler_creation",
    "watcher_creation",
    "automation_creation",
    "gate_execution",
    "merge_execution",
]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def load_metadata() -> dict[str, Any]:
    path = ROOT / "metadata/loopengineer.json"
    return json.loads(path.read_text(encoding="utf-8"))


def failure(code: str, message: str, suggested_action: str, *, field: str = "command") -> dict[str, str]:
    return {
        "code": code,
        "file": "argv",
        "field": field,
        "message": message,
        "suggestedAction": suggested_action,
    }


def status_code(status: str) -> int:
    if status == "pass":
        return 0
    if status == "fail":
        return 1
    return 2


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    summary = result.get("summary")
    if isinstance(summary, dict):
        return summary
    if "recommendedProfile" in result:
        return {
            "recommendedProfile": result.get("recommendedProfile"),
            "score": result.get("score"),
        }
    if isinstance(result.get("humanSummary"), str):
        return {"humanSummary": result["humanSummary"]}
    if "suggestedAction" in result:
        return {"suggestedAction": result.get("suggestedAction")}
    if isinstance(result.get("checkedFiles"), list):
        return {"checkedFileCount": len(result["checkedFiles"])}
    return {}


def result_failures(result: dict[str, Any]) -> list[dict[str, Any]]:
    failures = result.get("failures")
    if isinstance(failures, list):
        return failures
    if result.get("status") in {"fail", "error"}:
        return [
            failure(
                "engine_result_failed",
                str(result.get("error", "engine capability returned a non-pass status")),
                str(result.get("suggestedAction", "inspect result")),
                field="result",
            )
        ]
    return []


def envelope(capability: str, result: dict[str, Any], *, returncode: int = 0) -> dict[str, Any]:
    status = str(result.get("status", "error"))
    if returncode == 2:
        status = "error"
    return {
        "status": status,
        "capability": capability,
        "summary": summarize_result(result),
        "result": result,
        "failures": result_failures(result),
    }


def error_envelope(capability: str | None, failures: list[dict[str, Any]], *, result: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "error",
        "capability": capability,
        "summary": {"failureCount": len(failures)},
        "result": result or {"status": "error", "failures": failures},
        "failures": failures,
    }


def invoke_command(command: str, args: list[str]) -> tuple[int, dict[str, Any]]:
    capability, script_name = COMMANDS[command]
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    output = completed.stdout.strip()
    err = completed.stderr.strip()
    if not output:
        failures = [
            failure(
                "engine_no_json_output",
                "engine capability did not emit JSON",
                "fix arguments or the wrapped capability",
            )
        ]
        result = {
            "status": "error",
            "returncode": completed.returncode,
            "stderr": err,
            "failures": failures,
        }
        return 2, error_envelope(capability, failures, result=result)
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        failures = [
            failure(
                "engine_invalid_json_output",
                f"engine capability emitted invalid JSON: {exc}",
                "fix the wrapped capability output",
            )
        ]
        result = {
            "status": "error",
            "returncode": completed.returncode,
            "stdout": output,
            "stderr": err,
            "failures": failures,
        }
        return 2, error_envelope(capability, failures, result=result)
    if not isinstance(result, dict):
        failures = [
            failure(
                "engine_json_not_object",
                "engine capability emitted a non-object JSON document",
                "fix the wrapped capability output",
            )
        ]
        return 2, error_envelope(capability, failures)
    payload = envelope(capability, result, returncode=completed.returncode)
    return status_code(payload["status"]), payload


def preflight() -> tuple[int, dict[str, Any]]:
    try:
        metadata = load_metadata()
    except Exception as exc:  # noqa: BLE001 - CLI must fail closed as JSON.
        failures = [
            failure(
                "metadata_unreadable",
                f"cannot read LoopEngineer metadata: {exc}",
                "restore metadata/loopengineer.json",
                field="metadata",
            )
        ]
        return 2, error_envelope("preflight", failures)
    result = {
        "status": "pass",
        "preflightVersion": "1.0",
        "productVersion": metadata.get("version"),
        "engineContractVersion": metadata.get("engineContractVersion", "0"),
        "reminders": REMINDERS,
        "boundaries": {
            "noConsumedReport": True,
            "noStateTransition": True,
            "noRuntimeLifecycle": True,
            "deniedCapabilities": DENIED_CAPABILITIES,
        },
        "summary": {
            "reminderCount": len(REMINDERS),
            "conclusion": "session admission reminder only; no state transition or runtime lifecycle action",
        },
        "failures": [],
    }
    return 0, envelope("preflight", result)


def dispatch(argv: list[str]) -> tuple[int, dict[str, Any]]:
    if not argv:
        failures = [
            failure(
                "missing_capability",
                "missing engine capability command",
                "choose one of: " + ", ".join(sorted([*COMMANDS, "preflight"])),
            )
        ]
        return 2, error_envelope(None, failures)
    command = argv[0]
    args = argv[1:]
    if command == "preflight":
        if args:
            failures = [
                failure(
                    "unexpected_preflight_arguments",
                    "preflight does not accept arguments",
                    "call preflight without additional arguments",
                    field="arguments",
                )
            ]
            return 2, error_envelope("preflight", failures)
        return preflight()
    if command not in COMMANDS:
        failures = [
            failure(
                "unknown_capability",
                f"unsupported engine capability {command!r}",
                "choose one of: " + ", ".join(sorted([*COMMANDS, "preflight"])),
            )
        ]
        return 2, error_envelope(None, failures)
    return invoke_command(command, args)


def main(argv: list[str] | None = None) -> int:
    code, payload = dispatch(argv if argv is not None else sys.argv[1:])
    emit(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
