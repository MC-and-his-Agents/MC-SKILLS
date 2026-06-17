#!/usr/bin/env python3
"""Check text against a LoopEngineer context budget profile."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUDGET = ROOT / "schemas/v1/context-budget.default.json"


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def load_budget(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_budget(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "1.0":
        errors.append("schemaVersion must be 1.0")
    if data.get("kind") != "loopengineer.contextBudget":
        errors.append("kind must be loopengineer.contextBudget")

    estimation = data.get("estimation")
    if not isinstance(estimation, dict):
        errors.append("estimation must be an object")
    else:
        if estimation.get("method") != "deterministic_approx_v1":
            errors.append("estimation.method must be deterministic_approx_v1")
        chars_per_token = estimation.get("charsPerToken")
        line_overhead = estimation.get("lineOverheadTokens")
        fence_overhead = estimation.get("codeFenceOverheadTokens")
        if not isinstance(chars_per_token, int) or chars_per_token < 1:
            errors.append("estimation.charsPerToken must be a positive integer")
        if not isinstance(line_overhead, int) or line_overhead < 0:
            errors.append("estimation.lineOverheadTokens must be a non-negative integer")
        if not isinstance(fence_overhead, int) or fence_overhead < 0:
            errors.append("estimation.codeFenceOverheadTokens must be a non-negative integer")

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        errors.append("profiles must be a non-empty object")
        return errors

    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            errors.append(f"{name} must be an object")
            continue
        budget = profile.get("budgetTokens")
        warning = profile.get("warnAtTokens")
        if not isinstance(budget, int) or budget < 1:
            errors.append(f"{name}.budgetTokens must be a positive integer")
        if not isinstance(warning, int) or warning < 1:
            errors.append(f"{name}.warnAtTokens must be a positive integer")
        if isinstance(budget, int) and isinstance(warning, int) and warning > budget:
            errors.append(f"{name}.warnAtTokens must not exceed budgetTokens")
        if profile.get("overflowAction") not in {
            "write_artifact_send_locator",
            "rotate_thread",
        }:
            errors.append(f"{name}.overflowAction is unsupported")

    return errors


def estimate_tokens(text: str, estimation: dict) -> int:
    chars_per_token = estimation["charsPerToken"]
    line_overhead = estimation["lineOverheadTokens"]
    fence_overhead = estimation["codeFenceOverheadTokens"]
    character_tokens = math.ceil(len(text) / chars_per_token)
    line_count = text.count("\n") + (1 if text else 0)
    code_fences = text.count("```")
    return character_tokens + (line_count * line_overhead) + (code_fences * fence_overhead)


def result_for(profile_name: str, profile: dict, estimated_tokens: int) -> tuple[str, str]:
    budget = profile["budgetTokens"]
    warning = profile["warnAtTokens"]
    overflow = profile["overflowAction"]
    if estimated_tokens > budget:
        return "fail", overflow
    if estimated_tokens >= warning:
        return "pass", "send_with_warning"
    return "pass", "send"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an input file against a LoopEngineer context budget profile."
    )
    parser.add_argument("--profile", required=True, help="Budget profile name.")
    parser.add_argument("--input-file", required=True, help="Text file to check.")
    parser.add_argument(
        "--budget-file",
        default=str(DEFAULT_BUDGET),
        help="Budget JSON file. Defaults to schemas/v1/context-budget.default.json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    budget_path = Path(args.budget_file)
    input_path = Path(args.input_file)

    try:
        budget = load_budget(budget_path)
    except Exception as exc:  # noqa: BLE001 - CLI must report all read/parse failures.
        emit(
            {
                "status": "error",
                "profile": args.profile,
                "estimatedTokens": None,
                "budgetTokens": None,
                "suggestedAction": "fix_budget_file",
                "error": f"cannot read budget file: {exc}",
            }
        )
        return 2

    errors = validate_budget(budget)
    if errors:
        emit(
            {
                "status": "error",
                "profile": args.profile,
                "estimatedTokens": None,
                "budgetTokens": None,
                "suggestedAction": "fix_budget_file",
                "error": "; ".join(errors),
            }
        )
        return 2

    profile = budget["profiles"].get(args.profile)
    if profile is None:
        emit(
            {
                "status": "error",
                "profile": args.profile,
                "estimatedTokens": None,
                "budgetTokens": None,
                "suggestedAction": "choose_known_profile",
                "error": "unknown profile",
            }
        )
        return 2

    try:
        text = input_path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - CLI must report all read failures.
        emit(
            {
                "status": "error",
                "profile": args.profile,
                "estimatedTokens": None,
                "budgetTokens": profile["budgetTokens"],
                "suggestedAction": "fix_input_file",
                "error": f"cannot read input file: {exc}",
            }
        )
        return 2

    estimated = estimate_tokens(text, budget["estimation"])
    status, action = result_for(args.profile, profile, estimated)
    emit(
        {
            "status": status,
            "profile": args.profile,
            "estimatedTokens": estimated,
            "budgetTokens": profile["budgetTokens"],
            "suggestedAction": action,
        }
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
