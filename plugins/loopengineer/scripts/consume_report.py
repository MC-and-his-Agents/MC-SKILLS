#!/usr/bin/env python3
"""Consume a validated LoopEngineer report and write a receipt."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

import validate_structures
import subagent_report_check


ROOT = Path(__file__).resolve().parents[1]
REPORT_ID_RE = re.compile(r"^report-[A-Za-z0-9._-]+$")


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


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_receipt(
    root: Path,
    report_path: Path,
    report: dict[str, Any],
    *,
    consumed_by: str,
    table_updated: str,
    state_file_updated: str | None,
) -> dict[str, Any]:
    next_action = report.get("next_action", {})
    receipt = {
        "schemaVersion": "1.0",
        "kind": "loopengineer.reportConsumed",
        "report_id": report["report_id"],
        "report_path": rel(root, report_path),
        "report_type": report.get("report_type"),
        "report_for_instruction_id": report.get("instruction_id"),
        "report_state": report.get("status"),
        "consumed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "consumed_by": consumed_by,
        "table_updated": table_updated,
        "state_file_updated": state_file_updated,
        "next_owner": next_action.get("owner"),
        "next_action": next_action.get("action"),
    }
    context = report.get("provider_context")
    if isinstance(context, dict) and context.get("provider") == "subagent":
        receipt["provider"] = "subagent"
        receipt["subagent_consumption"] = {
            "assignment_id": context.get("assignment_id"),
            "agent_id": context.get("agent_id"),
            "thread_id": context.get("thread_id"),
            "report_locator": context.get("report_locator"),
            "consumption_result": "eligible",
        }
    return receipt


def consume_report(
    root: Path,
    report_path: Path,
    output_dir: Path,
    *,
    assignment_path: Path | None = None,
    consumed_by: str,
    table_updated: str,
    state_file_updated: str | None,
    force: bool = False,
) -> dict[str, Any]:
    failures = validate_structures.validate_file(root, report_path)
    file = rel(root, report_path)
    if failures:
        return {"status": "fail", "receiptPath": None, "summary": None, "failures": failures}
    if assignment_path is not None:
        check = subagent_report_check.check_subagent_report(root, assignment_path, report_path)
        if check["status"] != "pass":
            return {
                "status": "fail",
                "receiptPath": None,
                "summary": check.get("summary"),
                "failures": check["failures"],
            }

    report = load_report(report_path)
    if report.get("kind") != "loopengineer.report":
        return {
            "status": "fail",
            "receiptPath": None,
            "summary": None,
            "failures": [
                failure(file, "kind", "input must be loopengineer.report", "pass a report artifact")
            ],
        }
    context = report.get("provider_context")
    if isinstance(context, dict) and context.get("provider") == "subagent" and assignment_path is None:
        return {
            "status": "fail",
            "receiptPath": None,
            "summary": None,
            "failures": [
                failure(
                    file,
                    "assignment_file",
                    "subagent report requires assignment validation before consumption",
                    "pass --assignment-file for subagent provider reports",
                )
            ],
        }
    report_id = report.get("report_id")
    if not isinstance(report_id, str) or not REPORT_ID_RE.match(report_id):
        return {
            "status": "fail",
            "receiptPath": None,
            "summary": None,
            "failures": [
                failure(file, "report_id", "report_id is not safe for receipt filename", "use a report-[A-Za-z0-9._-]+ id")
            ],
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / f"{report_id}-consumed.json"
    if receipt_path.exists() and not force:
        return {
            "status": "fail",
            "receiptPath": rel(root, receipt_path),
            "summary": None,
            "failures": [
                failure(
                    rel(root, receipt_path),
                    "receipt",
                    "consumption receipt already exists",
                    "use a new report or pass --force after confirming this is an intentional overwrite",
                )
            ],
        }

    receipt = build_receipt(
        root,
        report_path,
        report,
        consumed_by=consumed_by,
        table_updated=table_updated,
        state_file_updated=state_file_updated,
    )
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "reportId": receipt["report_id"],
        "reportType": receipt["report_type"],
        "reportState": receipt["report_state"],
        "consumedBy": consumed_by,
        "nextOwner": receipt["next_owner"],
        "nextAction": receipt["next_action"],
    }
    return {
        "status": "pass",
        "receiptPath": rel(root, receipt_path),
        "summary": summary,
        "failures": [],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume a LoopEngineer report artifact.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--report-file", required=True, help="Report JSON file to consume.")
    parser.add_argument("--assignment-file", help="Subagent assignment JSON file required for subagent provider reports.")
    parser.add_argument("--output-dir", required=True, help="Directory where the receipt will be written.")
    parser.add_argument("--consumed-by", required=True, help="Consumer thread, scheduler, or watcher id.")
    parser.add_argument("--table-updated", choices=("yes", "no"), default="no")
    parser.add_argument("--state-file-updated", help="State file updated after consumption, if any.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing receipt.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    report_path = Path(args.report_file)
    assignment_path = Path(args.assignment_file) if args.assignment_file else None
    output_dir = Path(args.output_dir)
    report_path = report_path if report_path.is_absolute() else root / report_path
    assignment_path = assignment_path if assignment_path is None or assignment_path.is_absolute() else root / assignment_path
    output_dir = output_dir if output_dir.is_absolute() else root / output_dir
    payload = consume_report(
        root,
        report_path,
        output_dir,
        assignment_path=assignment_path,
        consumed_by=args.consumed_by,
        table_updated=args.table_updated,
        state_file_updated=args.state_file_updated,
        force=args.force,
    )
    emit(payload)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
