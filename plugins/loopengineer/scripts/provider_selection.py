#!/usr/bin/env python3
"""Recommend the lightest sufficient worker_lite provider."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


PROVIDERS = ("direct", "subagent", "thread")


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def disallow(provider: str, code: str, message: str, result: dict[str, Any]) -> None:
    result["disallowed_providers"].setdefault(provider, []).append(
        {
            "code": code,
            "reason": message,
        }
    )
    result["reasons"].append(message)


def choose_provider(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "pass",
        "recommended_provider": None,
        "disallowed_providers": {provider: [] for provider in PROVIDERS},
        "reasons": [],
        "required_fields": [],
        "summary": {},
        "failures": [],
    }

    thread_signals = []
    if args.task_risk == "high":
        thread_signals.append("high risk requires a thread worker")
    if args.write_scope in {"shared-contract", "external"}:
        thread_signals.append(f"{args.write_scope} write scope requires a thread worker")
    if args.duration == "long":
        thread_signals.append("long duration requires a recoverable thread worker")
    if args.needs_gate:
        thread_signals.append("high-cost or formal gate needs a thread worker")
    if args.external_action:
        thread_signals.append("external action needs a thread worker")
    if args.shared_state:
        thread_signals.append("shared state needs a scheduler/thread control plane")
    if args.requires_recovery:
        thread_signals.append("strict recovery needs a thread worker")
    if args.worktree_required:
        thread_signals.append("independent branch/worktree requires a thread worker")

    if thread_signals:
        for message in thread_signals:
            disallow("subagent", "requires_thread", message, result)
        result["recommended_provider"] = "thread"
        result["required_fields"] = [
            "worker_thread_id",
            "worktree_path",
            "branch",
            "report_output_path",
            "gate_owner",
        ]
    elif args.task_risk == "low" and args.duration == "short" and args.isolated_scope and (
        args.parallelizable or args.prefer_delegation
    ):
        result["recommended_provider"] = "subagent"
        result["required_fields"] = [
            "unit_id",
            "instruction_id",
            "agent_id",
            "thread_id",
            "objective_digest",
            "allowed_read_paths",
            "allowed_write_paths",
            "forbidden_scope",
            "expected_report_type",
            "report_output_path",
            "validation_expectation",
        ]
        result["reasons"].append("short, low-risk, isolated bounded work can use subagent provider")
    else:
        result["recommended_provider"] = "direct"
        result["required_fields"] = ["scope", "validation_expectation"]
        result["reasons"].append("single-owner bounded work does not need delegated provider")

    if args.write_scope == "none" and args.parallelizable:
        result["reasons"].append("read-only parallel work may use subagent if a locator-backed report is required")

    result["summary"] = {
        "recommendedProvider": result["recommended_provider"],
        "disallowedProviderCount": sum(1 for items in result["disallowed_providers"].values() if items),
    }
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recommend a worker_lite provider.")
    parser.add_argument("--task-risk", choices=("low", "medium", "high"), default="low")
    parser.add_argument("--write-scope", choices=("none", "local", "shared-contract", "external"), default="local")
    parser.add_argument("--duration", choices=("short", "medium", "long"), default="short")
    parser.add_argument("--needs-gate", action="store_true")
    parser.add_argument("--external-action", action="store_true")
    parser.add_argument("--shared-state", action="store_true")
    parser.add_argument("--requires-recovery", action="store_true")
    parser.add_argument("--parallelizable", action="store_true")
    parser.add_argument("--isolated-scope", action="store_true")
    parser.add_argument("--prefer-delegation", action="store_true")
    parser.add_argument("--worktree-required", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    emit(choose_provider(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
