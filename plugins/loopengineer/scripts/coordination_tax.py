#!/usr/bin/env python3
"""Estimate LoopEngineer coordination cost for routing decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

WEIGHTS = {
    "control_plane_token_block": 1,
    "cross_thread_message": 4,
    "report_read": 2,
    "report_write": 3,
    "heartbeat": 5,
    "recovery_action": 15,
    "worker": 6,
    "scheduler": 12,
}

THRESHOLDS = [
    ("direct", 0, 9),
    ("worker_lite", 10, 24),
    ("scheduler_lite", 25, 49),
    ("scheduler_full", 50, 79),
    ("watcher_full", 80, 119),
    ("incident_recovery", 120, None),
]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def failure(file: str, field: str, message: str, suggested_action: str) -> dict[str, str]:
    return {
        "file": file,
        "field": field,
        "message": message,
        "suggestedAction": suggested_action,
    }


def non_negative(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def recommended_profile(score: int) -> str:
    for profile, minimum, maximum in THRESHOLDS:
        if score >= minimum and (maximum is None or score <= maximum):
            return profile
    return "incident_recovery"


def threshold_payload() -> list[dict[str, Any]]:
    return [
        {"profile": profile, "minScore": minimum, "maxScore": maximum}
        for profile, minimum, maximum in THRESHOLDS
    ]


def calculate(args: argparse.Namespace) -> dict[str, Any]:
    token_blocks = (args.control_plane_tokens + 399) // 400
    components = {
        "controlPlaneTokenBlocks": token_blocks * WEIGHTS["control_plane_token_block"],
        "crossThreadMessages": args.cross_thread_messages * WEIGHTS["cross_thread_message"],
        "reportReads": args.reports_read * WEIGHTS["report_read"],
        "reportWrites": args.reports_written * WEIGHTS["report_write"],
        "heartbeats": args.heartbeats * WEIGHTS["heartbeat"],
        "recoveryActions": args.recovery_actions * WEIGHTS["recovery_action"],
        "workers": args.workers * WEIGHTS["worker"],
        "schedulers": args.schedulers * WEIGHTS["scheduler"],
    }
    score = sum(components.values())
    profile = recommended_profile(score)
    return {
        "status": "pass",
        "score": score,
        "recommendedProfile": profile,
        "inputs": {
            "controlPlaneTokens": args.control_plane_tokens,
            "crossThreadMessages": args.cross_thread_messages,
            "reportsRead": args.reports_read,
            "reportsWritten": args.reports_written,
            "heartbeats": args.heartbeats,
            "recoveryActions": args.recovery_actions,
            "workers": args.workers,
            "schedulers": args.schedulers,
        },
        "components": components,
        "thresholds": threshold_payload(),
        "humanSummary": (
            f"Coordination score {score} recommends {profile}; safety, shared-channel, "
            "review, merge, and release checks still take precedence."
        ),
        "failures": [],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estimate LoopEngineer coordination cost.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--control-plane-tokens", type=non_negative, default=0)
    parser.add_argument("--cross-thread-messages", type=non_negative, default=0)
    parser.add_argument("--reports-read", type=non_negative, default=0)
    parser.add_argument("--reports-written", type=non_negative, default=0)
    parser.add_argument("--heartbeats", type=non_negative, default=0)
    parser.add_argument("--recovery-actions", type=non_negative, default=0)
    parser.add_argument("--workers", type=non_negative, default=0)
    parser.add_argument("--schedulers", type=non_negative, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
    except SystemExit as exc:
        payload = {
            "status": "fail",
            "score": None,
            "recommendedProfile": None,
            "inputs": None,
            "components": None,
            "thresholds": threshold_payload(),
            "humanSummary": "Invalid coordination cost input.",
            "failures": [
                failure("argv", "arguments", "arguments must be non-negative integers", "pass zero or positive integers")
            ],
        }
        emit(payload)
        return int(exc.code) if isinstance(exc.code, int) and exc.code != 0 else 1
    payload = calculate(args)
    emit(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
