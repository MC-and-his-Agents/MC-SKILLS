#!/usr/bin/env python3
"""Audit LoopEngineer loop state for common orchestration drift."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import glob
import json
from pathlib import Path
import sys
from typing import Any

import validate_structures


ROOT = Path(__file__).resolve().parents[1]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def finding(code: str, file: str, field: str, message: str, suggested_action: str) -> dict[str, str]:
    return {
        "code": code,
        "file": file,
        "field": field,
        "message": message,
        "suggestedAction": suggested_action,
    }


def load_json(root: Path, path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - audit must fail closed as JSON.
        return None, [finding("json_unreadable", rel(root, path), "json", f"cannot read JSON: {exc}", "fix JSON syntax")]
    if not isinstance(data, dict):
        return None, [finding("json_not_object", rel(root, path), "json", "JSON document must be an object", "replace with an object")]
    return data, []


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def expand_globs(root: Path, patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(str(root / pattern) if not Path(pattern).is_absolute() else pattern)
        paths.extend(Path(match) for match in matches)
    return sorted(set(path.resolve() for path in paths))


def next_action_findings(
    root: Path,
    path: Path,
    data: dict[str, Any],
    *,
    current_owner: str | None,
) -> list[dict[str, str]]:
    if not current_owner:
        return []
    action = data.get("next_action")
    if not isinstance(action, dict):
        return []
    if action.get("owner") == current_owner and action.get("status") == "required":
        return [
            finding(
                "self_owned_next_action",
                rel(root, path),
                "next_action.owner",
                "current owner has a required next action that must be acted on before status-only closeout",
                "perform the action or reassign/block it with evidence",
            )
        ]
    return []


def audit(
    root: Path,
    input_paths: list[Path],
    report_paths: list[Path],
    receipt_paths: list[Path],
    *,
    current_owner: str | None,
    now: datetime,
    stale_after_minutes: int,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    structures: list[tuple[Path, dict[str, Any]]] = []
    reports: dict[str, tuple[Path, dict[str, Any]]] = {}
    consumed_report_ids: set[str] = set()
    consumed_instruction_reports: set[tuple[str | None, str | None]] = set()
    release_events_by_channel: set[str] = set()

    for path in input_paths + report_paths:
        validation = validate_structures.validate_file(root, path)
        if validation:
            findings.extend(
                finding("invalid_structure", item["file"], item["field"], item["message"], item["suggestedAction"])
                for item in validation
            )
            continue
        data, errors = load_json(root, path)
        findings.extend(errors)
        if data is None:
            continue
        structures.append((path, data))
        if data.get("kind") == "loopengineer.report":
            reports[data["report_id"]] = (path, data)
        if data.get("kind") == "loopengineer.channelEvent" and data.get("event_type") == "release":
            release_events_by_channel.add(str(data.get("channel_id")))

    for path in receipt_paths:
        receipt, errors = load_json(root, path)
        findings.extend(errors)
        if receipt is None:
            continue
        if receipt.get("kind") != "loopengineer.reportConsumed":
            findings.append(
                finding("invalid_receipt", rel(root, path), "kind", "receipt must be loopengineer.reportConsumed", "pass report consumption receipt files")
            )
            continue
        report_id = receipt.get("report_id")
        consumed_report_ids.add(str(report_id))
        consumed_instruction_reports.add((receipt.get("report_for_instruction_id"), receipt.get("report_type")))

    for report_id, (path, report) in reports.items():
        if report_id not in consumed_report_ids:
            code = "completed_report_unconsumed" if report.get("status") == "completed" else "unconsumed_report"
            findings.append(
                finding(
                    code,
                    rel(root, path),
                    "report_id",
                    f"report {report_id} has no consumption receipt",
                    "consume the report and write a reportConsumed receipt before transitioning state",
                )
            )

    for path, data in structures:
        findings.extend(next_action_findings(root, path, data, current_owner=current_owner))
        kind = data.get("kind")
        file = rel(root, path)
        if kind == "loopengineer.dispatchTable":
            for index, entry in enumerate(data.get("entries", [])):
                if (
                    entry.get("status") == "instruction-sent-awaiting-ack"
                    and (entry.get("instruction_id"), "instruction_ack") not in consumed_instruction_reports
                ):
                    findings.append(
                        finding(
                            "missing_ack",
                            file,
                            f"entries[{index}].instruction_id",
                            "scheduler instruction is awaiting ACK without a consumed instruction_ack report",
                            "read the ACK report locator or classify/recover the missing ACK before marking work active",
                        )
                    )
                findings.extend(next_action_findings(root, path, entry, current_owner=current_owner))
        elif kind == "loopengineer.waitingQueue":
            for index, item in enumerate(data.get("items", [])):
                if not item.get("resume_condition") or not item.get("next_readback_at"):
                    findings.append(
                        finding(
                            "missing_waiting_recovery_condition",
                            file,
                            f"items[{index}].resume_condition",
                            "waiting item is missing a concrete resume condition or next readback time",
                            "add resume_condition and next_readback_at before leaving scheduler blocked",
                        )
                    )
        elif kind == "loopengineer.channelState":
            if data.get("state") == "channel-stale-owner":
                findings.append(
                    finding(
                        "stale_channel_owner",
                        file,
                        "state",
                        "channel state marks a stale owner",
                        "recover or release the stale owner before granting shared work",
                    )
                )
            if data.get("state") == "channel-release-pending" and str(data.get("channel_id")) not in release_events_by_channel:
                findings.append(
                    finding(
                        "missing_channel_release_evidence",
                        file,
                        "state",
                        "channel release is pending without a release event in audited inputs",
                        "add release event evidence or keep the channel blocked",
                    )
                )
        elif kind == "loopengineer.watcherInbox":
            for index, target in enumerate(data.get("stale_heartbeat_targets", [])):
                checked = parse_time(target.get("last_checked_at"))
                if checked is None or (now - checked).total_seconds() >= stale_after_minutes * 60:
                    findings.append(
                        finding(
                            "stale_heartbeat_target",
                            file,
                            f"stale_heartbeat_targets[{index}].last_checked_at",
                            "watcher inbox contains a stale heartbeat target",
                            "refresh or correct the heartbeat target before continuing watcher decisions",
                        )
                    )
            for index, owner in enumerate(data.get("stale_channel_owners", [])):
                findings.append(
                    finding(
                        "stale_channel_owner",
                        file,
                        f"stale_channel_owners[{index}]",
                        "watcher inbox contains a stale channel owner",
                        "recover or release the stale owner before granting shared work",
                    )
                )
            for index, action in enumerate(data.get("required_next_actions", [])):
                if current_owner and action.get("owner") == current_owner:
                    findings.append(
                        finding(
                            "self_owned_next_action",
                            file,
                            f"required_next_actions[{index}].owner",
                            "watcher inbox assigns a required next action to the current owner",
                            "perform the action or classify a blocker before reporting only status",
                        )
                    )

    status = "pass" if not findings else "fail"
    return {
        "status": status,
        "auditVersion": "1.0",
        "checkedFiles": [rel(root, path) for path in input_paths + report_paths + receipt_paths],
        "summary": {
            "findingCount": len(findings),
            "reportCount": len(reports),
            "receiptCount": len(consumed_report_ids),
            "conclusion": "loop state has audit findings" if findings else "loop state passed audit checks",
        },
        "humanSummary": f"{len(findings)} audit finding(s); {len(reports)} report(s), {len(consumed_report_ids)} receipt(s) checked.",
        "findings": findings,
        "failures": findings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit LoopEngineer loop state for drift.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--input-file", action="append", default=[], help="Structure file to audit. May be repeated.")
    parser.add_argument("--report-glob", action="append", default=[], help="Repository-relative glob of report files.")
    parser.add_argument("--receipt-glob", action="append", default=[], help="Repository-relative glob of report consumption receipts.")
    parser.add_argument("--current-owner", choices=("worker", "scheduler", "watcher", "user", "external"), help="Current owner role for self-owned next action checks.")
    parser.add_argument("--now", help="Current time for stale checks. Defaults to current UTC time.")
    parser.add_argument("--stale-after-minutes", type=int, default=60)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    input_paths = [Path(item) for item in args.input_file]
    input_paths = [path if path.is_absolute() else root / path for path in input_paths]
    report_paths = expand_globs(root, args.report_glob)
    receipt_paths = expand_globs(root, args.receipt_glob)
    now = parse_time(args.now) or datetime.now(timezone.utc)
    payload = audit(
        root,
        input_paths,
        report_paths,
        receipt_paths,
        current_owner=args.current_owner,
        now=now,
        stale_after_minutes=max(args.stale_after_minutes, 0),
    )
    emit(payload)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
