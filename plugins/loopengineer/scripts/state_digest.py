#!/usr/bin/env python3
"""Build compact LoopEngineer state digests for heartbeat and handoff prompts."""

from __future__ import annotations

import argparse
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def next_action(data: dict[str, Any]) -> dict[str, Any] | None:
    action = data.get("next_action")
    if not isinstance(action, dict):
        return None
    return {
        "owner": action.get("owner"),
        "action": action.get("action"),
        "status": action.get("status"),
    }


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def summarize_structure(data: dict[str, Any], *, mode: str) -> dict[str, Any]:
    kind = data["kind"]
    base: dict[str, Any] = {
        "kind": kind,
        "schemaVersion": data.get("schemaVersion"),
    }
    if kind == "loopengineer.contextBudget":
        profiles = data.get("profiles", {})
        base.update({"profileCount": len(profiles), "profiles": sorted(profiles)})
    elif kind == "loopengineer.handoffManifest":
        base.update(
            {
                "manifestId": data.get("manifest_id"),
                "rotationReason": data.get("rotation_reason"),
                "nextOwner": data.get("next_owner"),
                "nextAction": data.get("next_action"),
            }
        )
    elif kind == "loopengineer.report":
        base.update(
            {
                "reportId": data.get("report_id"),
                "reportType": data.get("report_type"),
                "role": data.get("role"),
                "status": data.get("status"),
                "nextAction": next_action(data),
            }
        )
    elif kind == "loopengineer.dispatchTable":
        entries = data.get("entries", [])
        base.update(
            {
                "tableId": data.get("table_id"),
                "schedulerId": data.get("scheduler_id"),
                "entryCount": len(entries),
                "entryStatusCounts": count_by(entries, "status"),
                "nextAction": next_action(data),
            }
        )
        if mode == "full":
            base["instructions"] = [
                {
                    "instructionId": entry.get("instruction_id"),
                    "unitId": entry.get("unit_id"),
                    "status": entry.get("status"),
                    "expectedReportType": entry.get("expected_report_type"),
                }
                for entry in entries
            ]
    elif kind == "loopengineer.schedulerPool":
        schedulers = data.get("schedulers", [])
        base.update(
            {
                "poolId": data.get("pool_id"),
                "schedulerCount": len(schedulers),
                "schedulerStatusCounts": count_by(schedulers, "status"),
                "nextAction": next_action(data),
            }
        )
        if mode == "full":
            base["schedulers"] = [
                {
                    "schedulerId": item.get("scheduler_id"),
                    "unitId": item.get("unit_id"),
                    "status": item.get("status"),
                    "reportInbox": item.get("report_inbox"),
                }
                for item in schedulers
            ]
    elif kind == "loopengineer.channelState":
        base.update(
            {
                "channelId": data.get("channel_id"),
                "channelType": data.get("channel_type"),
                "state": data.get("state"),
                "owner": data.get("owner"),
                "waitingCount": len(data.get("waiting_scheduler_ids", [])),
                "nextAction": next_action(data),
            }
        )
    elif kind == "loopengineer.waitingQueue":
        items = data.get("items", [])
        base.update(
            {
                "queueId": data.get("queue_id"),
                "channelId": data.get("channel_id"),
                "waitingCount": len(items),
                "nextAction": next_action(data),
            }
        )
        if mode == "full":
            base["waiting"] = [
                {
                    "waitId": item.get("wait_id"),
                    "schedulerId": item.get("scheduler_id"),
                    "unitId": item.get("unit_id"),
                    "nextReadbackAt": item.get("next_readback_at"),
                }
                for item in items
            ]
    elif kind == "loopengineer.channelEvent":
        base.update(
            {
                "eventId": data.get("event_id"),
                "eventType": data.get("event_type"),
                "channelId": data.get("channel_id"),
                "schedulerId": data.get("scheduler_id"),
                "nextAction": next_action(data),
            }
        )
    elif kind == "loopengineer.watcherDecision":
        base.update(
            {
                "decisionId": data.get("decision_id"),
                "decisionType": data.get("decision_type"),
                "watcherId": data.get("watcher_id"),
                "targetChannelId": data.get("target_channel_id"),
                "targetSchedulerId": data.get("target_scheduler_id"),
                "inputCount": len(data.get("inputs", [])),
                "nextAction": next_action(data),
            }
        )
    elif kind == "loopengineer.watcherInbox":
        summary = data.get("summary", {})
        base.update(
            {
                "inboxId": data.get("inbox_id"),
                "watcherId": data.get("watcher_id"),
                "stateRoot": data.get("state_root"),
                "sourceCount": len(data.get("sources", [])),
                "summary": summary,
                "nextAction": next_action(data),
            }
        )
        if mode == "full":
            base["requiredNextActions"] = [
                {
                    "owner": action.get("owner"),
                    "action": action.get("action"),
                }
                for action in data.get("required_next_actions", [])
            ]
    return base


def default_inputs(root: Path) -> list[Path]:
    return validate_structures.default_inputs(root)


def report_inbox_summary(root: Path, pattern: str | None) -> dict[str, Any] | None:
    if pattern is None:
        return None
    paths = sorted(root.glob(pattern))
    return {
        "glob": pattern,
        "count": len(paths),
        "reports": [rel(root, path) for path in paths],
    }


def build_digest(
    root: Path,
    paths: list[Path],
    *,
    mode: str,
    report_inbox_glob: str | None = None,
) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    structures = []
    kind_counts: dict[str, int] = {}
    for path in paths:
        failures.extend(validate_structures.validate_file(root, path))
        if failures:
            continue
        data = load_json(path)
        kind = data["kind"]
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        item = summarize_structure(data, mode=mode)
        item["file"] = rel(root, path)
        structures.append(item)

    if failures:
        return {
            "status": "fail",
            "mode": mode,
            "checkedFiles": [rel(root, path) for path in paths],
            "failures": failures,
        }

    digest: dict[str, Any] = {
        "status": "pass",
        "digestVersion": "1.0",
        "mode": mode,
        "checkedFiles": [rel(root, path) for path in paths],
        "summary": {
            "fileCount": len(paths),
            "kindCounts": dict(sorted(kind_counts.items())),
        },
        "structures": structures,
        "failures": [],
    }
    inbox = report_inbox_summary(root, report_inbox_glob)
    if mode == "full" and inbox is not None:
        digest["reportInbox"] = inbox
    return digest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a compact LoopEngineer state digest.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--mode", choices=("minimal", "full"), default="minimal")
    parser.add_argument(
        "--input-file",
        action="append",
        help="Structure file to digest. May be passed more than once.",
    )
    parser.add_argument(
        "--report-inbox-glob",
        help="Optional repository-relative glob for report inbox files in full mode.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    paths = [Path(item) for item in args.input_file] if args.input_file else default_inputs(root)
    paths = [path if path.is_absolute() else root / path for path in paths]
    payload = build_digest(root, paths, mode=args.mode, report_inbox_glob=args.report_inbox_glob)
    emit(payload)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
