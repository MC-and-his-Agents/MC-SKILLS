#!/usr/bin/env python3
"""Validate LoopEngineer structure examples with deterministic local rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXAMPLES = ROOT / "schemas/v1/examples"
VERSION_FIELDS = {
    "productVersion",
    "protocolVersion",
    "schemaVersion",
    "skillContractVersion",
}
NEXT_ACTION_FIELDS = {"owner", "action", "status"}
NEXT_ACTION_OWNERS = {"worker", "scheduler", "watcher", "user", "external"}
NEXT_ACTION_STATUSES = {"required", "blocked", "waiting", "none"}
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
REPORT_ID_RE = re.compile(r"^report-[A-Za-z0-9._-]+$")
REPORT_TYPES = {
    "instruction_ack",
    "startup_report",
    "progress_update",
    "blocker_update",
    "completion_result",
    "gate_wait",
    "routing_missing",
    "correction_result",
}
ROLES = {"worker", "scheduler", "watcher"}
DISPATCH_STATUSES = {
    "instruction-sent-awaiting-ack",
    "confirming",
    "active",
    "waiting-report",
    "waiting-scheduler-gate",
    "blocked",
    "completed",
    "failed",
    "replacement-planned",
}
SCHEDULER_STATUSES = {
    "planned",
    "active",
    "blocked",
    "waiting-gate",
    "completed",
    "retired",
    "systemError-retired",
}
CHANNEL_TYPES = {
    "shared_fact_chain_status",
    "shadow_carrier",
    "current_item_review",
    "high_cost_gate",
    "merge",
    "contract",
}
CHANNEL_STATES = {
    "channel-free",
    "channel-granted",
    "channel-release-pending",
    "channel-blocked",
    "channel-stale-owner",
    "channel-released",
}
EVENT_TYPES = {"request", "grant", "wait", "deny", "release"}
PROVIDERS = {"direct", "subagent", "thread"}
SUBAGENT_ASSIGNMENT_ID_RE = re.compile(r"^assignment-[A-Za-z0-9._-]+$")
SUBAGENT_REQUIRED_FORBIDDEN_SCOPE = {
    "state_transition",
    "shared_channel",
    "gate",
    "merge",
    "release",
    "closeout",
}
DECISION_TYPES = {
    "grant_channel",
    "deny_channel",
    "wait",
    "readback",
    "recover_scheduler",
    "release_channel",
    "noop",
}
WATCHER_INBOX_SUMMARY_FIELDS = {
    "unconsumed_report_count",
    "unconsumed_channel_event_count",
    "unacked_instruction_count",
    "stale_heartbeat_count",
    "stale_channel_owner_count",
    "candidate_unit_count",
    "required_next_action_count",
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


def require_fields(data: dict[str, Any], fields: set[str], file: str, label: str) -> list[dict[str, str]]:
    return [
        failure(file, field, f"{label} missing {field}", f"add {field} to {label}")
        for field in sorted(fields)
        if field not in data
    ]


def require_enum(file: str, field: str, value: Any, allowed: set[str], label: str) -> list[dict[str, str]]:
    if value in allowed:
        return []
    allowed_values = ", ".join(sorted(allowed))
    return [failure(file, field, f"{label} is invalid", f"use one of: {allowed_values}")]


def load_json(root: Path, path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    file = rel(root, path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI must report all parse failures as JSON.
        return None, [failure(file, "json", f"cannot read JSON: {exc}", "fix JSON syntax")]
    if not isinstance(data, dict):
        return None, [failure(file, "json", "JSON document must be an object", "replace with an object")]
    return data, []


def validate_version(root: Path, path: Path, data: Any) -> list[dict[str, str]]:
    file = rel(root, path)
    if not isinstance(data, dict):
        return [failure(file, "version", "version must be an object", "add version metadata")]
    errors = require_fields(data, VERSION_FIELDS, file, "version")
    product_version = data.get("productVersion")
    if not isinstance(product_version, str) or not SEMVER_RE.match(product_version):
        errors.append(failure(file, "version.productVersion", "productVersion must be SemVer", "set productVersion to MAJOR.MINOR.PATCH"))
    for field in ("protocolVersion", "skillContractVersion"):
        if not isinstance(data.get(field), str) or not data.get(field):
            errors.append(failure(file, f"version.{field}", f"{field} must be a non-empty string", f"set version.{field}"))
    if data.get("schemaVersion") != "1.0":
        errors.append(failure(file, "version.schemaVersion", "schemaVersion must be 1.0", "set schemaVersion to 1.0"))
    return errors


def validate_next_action(root: Path, path: Path, data: Any) -> list[dict[str, str]]:
    file = rel(root, path)
    if not isinstance(data, dict):
        return [failure(file, "next_action", "next_action must be an object", "add next_action")]
    errors = require_fields(data, NEXT_ACTION_FIELDS, file, "next_action")
    errors.extend(require_enum(file, "next_action.owner", data.get("owner"), NEXT_ACTION_OWNERS, "owner"))
    if not isinstance(data.get("action"), str) or not data.get("action"):
        errors.append(failure(file, "next_action.action", "action must be a non-empty string", "set next_action.action"))
    if data.get("status") not in NEXT_ACTION_STATUSES:
        errors.append(failure(file, "next_action.status", "status is invalid", "use required, blocked, waiting, or none"))
    return errors


def common(root: Path, path: Path, data: dict[str, Any], kind: str) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = require_fields(data, {"schemaVersion", "kind"}, file, "structure")
    if data.get("schemaVersion") != "1.0":
        errors.append(failure(file, "schemaVersion", "schemaVersion must be 1.0", "set schemaVersion to 1.0"))
    if data.get("kind") != kind:
        errors.append(failure(file, "kind", f"kind must be {kind}", f"set kind to {kind}"))
    return errors


def validate_context_budget(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.contextBudget")
    estimation = data.get("estimation")
    profiles = data.get("profiles")
    if not isinstance(estimation, dict):
        errors.append(failure(file, "estimation", "estimation must be an object", "add estimation settings"))
    else:
        chars_per_token = estimation.get("charsPerToken")
        if not isinstance(chars_per_token, (int, float)) or isinstance(chars_per_token, bool) or chars_per_token < 1:
            errors.append(failure(file, "estimation.charsPerToken", "must be a positive number", "set charsPerToken above zero"))
    if not isinstance(profiles, dict) or not profiles:
        errors.append(failure(file, "profiles", "profiles must be a non-empty object", "add context budget profiles"))
    else:
        for name, profile in profiles.items():
            if not isinstance(profile, dict):
                errors.append(failure(file, f"profiles.{name}", "profile must be an object", "fix profile"))
                continue
            budget = profile.get("budgetTokens")
            warning = profile.get("warnAtTokens")
            if isinstance(budget, int) and isinstance(warning, int) and warning > budget:
                errors.append(failure(file, f"profiles.{name}.warnAtTokens", "must not exceed budgetTokens", "lower warnAtTokens"))
            if profile.get("overflowAction") not in {"write_artifact_send_locator", "rotate_thread"}:
                errors.append(failure(file, f"profiles.{name}.overflowAction", "unsupported overflowAction", "use a supported overflowAction"))
    return errors


def validate_handoff_manifest(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.handoffManifest")
    authority = data.get("authority")
    prohibitions = set(data.get("prohibitions", []))
    if not isinstance(authority, dict):
        errors.append(failure(file, "authority", "authority must be an object", "add authority"))
        return errors
    allowed = set(authority.get("allowed_sources", []))
    forbidden = set(authority.get("forbidden_sources", []))
    for source in ("state_root", "handoff_manifest", "live_facts"):
        if source not in allowed:
            errors.append(failure(file, "authority.allowed_sources", f"missing {source}", "add required authority source"))
    for source in ("retired_thread_history", "old_thread_transcript"):
        if source in allowed:
            errors.append(failure(file, "authority.allowed_sources", f"forbidden source allowed: {source}", "remove forbidden source"))
        if source not in forbidden:
            errors.append(failure(file, "authority.forbidden_sources", f"missing {source}", "add forbidden source"))
    if "do_not_use_retired_thread_as_fact_source" not in prohibitions:
        errors.append(failure(file, "prohibitions", "missing retired-thread prohibition", "add retired thread prohibition"))
    return errors


def validate_report(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.report")
    errors.extend(require_fields(data, {"report_id", "report_type", "role", "status", "version", "producer", "created_at", "summary", "next_action"}, file, "report"))
    if not isinstance(data.get("report_id"), str) or not REPORT_ID_RE.match(data["report_id"]):
        errors.append(failure(file, "report_id", "must match report id pattern", "use a report-[A-Za-z0-9._-]+ id"))
    errors.extend(require_enum(file, "report_type", data.get("report_type"), REPORT_TYPES, "report_type"))
    errors.extend(require_enum(file, "role", data.get("role"), ROLES, "role"))
    errors.extend(require_enum(file, "status", data.get("status"), {"acknowledged", "running", "blocked", "waiting", "completed", "failed"}, "status"))
    producer = data.get("producer")
    if not isinstance(producer, dict):
        errors.append(failure(file, "producer", "producer must be an object", "add producer metadata"))
    else:
        errors.extend(require_fields(producer, {"id", "role"}, file, "producer"))
        errors.extend(require_enum(file, "producer.role", producer.get("role"), ROLES, "producer role"))
    errors.extend(validate_version(root, path, data.get("version")))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    context = data.get("provider_context")
    if context is not None:
        errors.extend(validate_provider_context(root, path, context))
    return errors


def validate_path_items(root: Path, path: Path, data: Any, field: str, *, allow_empty: bool) -> list[dict[str, str]]:
    file = rel(root, path)
    errors: list[dict[str, str]] = []
    if not isinstance(data, list):
        return [failure(file, field, f"{field} must be an array", f"set {field} to a list of paths")]
    if not data and not allow_empty:
        errors.append(failure(file, field, f"{field} must be non-empty", f"add at least one {field} path"))
    for index, item in enumerate(data):
        if not isinstance(item, str) or not item:
            errors.append(failure(file, f"{field}[{index}]", "path must be a non-empty string", "replace with a path string"))
    return errors


def validate_provider_context(root: Path, path: Path, data: Any) -> list[dict[str, str]]:
    file = rel(root, path)
    if not isinstance(data, dict):
        return [failure(file, "provider_context", "provider_context must be an object", "add provider context metadata")]
    errors = require_fields(
        data,
        {"provider", "assignment_id", "agent_id", "thread_id", "report_locator", "changed_paths", "validation", "authority_claims"},
        file,
        "provider_context",
    )
    errors.extend(require_enum(file, "provider_context.provider", data.get("provider"), PROVIDERS, "provider"))
    if data.get("provider") != "subagent":
        errors.append(failure(file, "provider_context.provider", "only subagent context is supported here", "set provider_context.provider to subagent"))
    if not isinstance(data.get("assignment_id"), str) or not SUBAGENT_ASSIGNMENT_ID_RE.match(str(data.get("assignment_id", ""))):
        errors.append(failure(file, "provider_context.assignment_id", "assignment_id must match assignment id pattern", "use assignment-[A-Za-z0-9._-]+"))
    for field in ("agent_id", "thread_id", "report_locator"):
        if not isinstance(data.get(field), str) or not data.get(field):
            errors.append(failure(file, f"provider_context.{field}", f"{field} must be a non-empty string", f"set provider_context.{field}"))
    changed_paths = data.get("changed_paths")
    if not isinstance(changed_paths, list):
        errors.append(failure(file, "provider_context.changed_paths", "changed_paths must be an array", "record changed path entries or an empty array"))
    else:
        for index, item in enumerate(changed_paths):
            if not isinstance(item, dict):
                errors.append(failure(file, f"provider_context.changed_paths[{index}]", "changed path entry must be an object", "use {path, change_type}"))
                continue
            errors.extend(require_fields(item, {"path", "change_type"}, file, "changed path"))
            if not isinstance(item.get("path"), str) or not item.get("path"):
                errors.append(failure(file, f"provider_context.changed_paths[{index}].path", "path must be a non-empty string", "set changed path"))
    validation = data.get("validation")
    if not isinstance(validation, dict):
        errors.append(failure(file, "provider_context.validation", "validation must be an object", "record validation status"))
    else:
        errors.extend(require_fields(validation, {"status", "commands"}, file, "validation"))
        errors.extend(require_enum(file, "provider_context.validation.status", validation.get("status"), {"pass", "fail"}, "validation status"))
        commands = validation.get("commands")
        if not isinstance(commands, list) or not commands:
            errors.append(failure(file, "provider_context.validation.commands", "commands must be a non-empty array", "record validation commands"))
    claims = data.get("authority_claims")
    if not isinstance(claims, list):
        errors.append(failure(file, "provider_context.authority_claims", "authority_claims must be an array", "record an empty array when none"))
    else:
        forbidden = sorted(set(claims) & SUBAGENT_REQUIRED_FORBIDDEN_SCOPE)
        if forbidden:
            errors.append(failure(file, "provider_context.authority_claims", "subagent cannot claim control-plane authority", "remove forbidden claims: " + ", ".join(forbidden)))
    return errors


def validate_subagent_assignment(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.subagentAssignment")
    errors.extend(
        require_fields(
            data,
            {
                "assignment_id",
                "unit_id",
                "instruction_id",
                "provider",
                "agent_id",
                "thread_id",
                "objective_digest",
                "allowed_read_paths",
                "allowed_write_paths",
                "forbidden_scope",
                "expected_report_type",
                "report_output_path",
                "validation_expectation",
                "next_owner",
                "next_action",
            },
            file,
            "subagent_assignment",
        )
    )
    if not isinstance(data.get("assignment_id"), str) or not SUBAGENT_ASSIGNMENT_ID_RE.match(str(data.get("assignment_id", ""))):
        errors.append(failure(file, "assignment_id", "assignment_id must match assignment id pattern", "use assignment-[A-Za-z0-9._-]+"))
    for field in ("unit_id", "instruction_id", "agent_id", "thread_id", "objective_digest", "report_output_path"):
        if not isinstance(data.get(field), str) or not data.get(field):
            errors.append(failure(file, field, f"{field} must be a non-empty string", f"set {field}"))
    errors.extend(require_enum(file, "provider", data.get("provider"), PROVIDERS, "provider"))
    if data.get("provider") != "subagent":
        errors.append(failure(file, "provider", "subagent assignment must use subagent provider", "set provider to subagent"))
    errors.extend(validate_path_items(root, path, data.get("allowed_read_paths"), "allowed_read_paths", allow_empty=False))
    errors.extend(validate_path_items(root, path, data.get("allowed_write_paths"), "allowed_write_paths", allow_empty=True))
    forbidden_scope = data.get("forbidden_scope")
    if not isinstance(forbidden_scope, list):
        errors.append(failure(file, "forbidden_scope", "forbidden_scope must be an array", "list prohibited control-plane authority"))
    else:
        missing = sorted(SUBAGENT_REQUIRED_FORBIDDEN_SCOPE - set(forbidden_scope))
        if missing:
            errors.append(failure(file, "forbidden_scope", "missing required subagent prohibitions", "add: " + ", ".join(missing)))
    errors.extend(require_enum(file, "expected_report_type", data.get("expected_report_type"), REPORT_TYPES, "expected_report_type"))
    errors.extend(require_enum(file, "next_owner", data.get("next_owner"), {"worker", "scheduler", "watcher", "user"}, "next_owner"))
    validation = data.get("validation_expectation")
    if not isinstance(validation, dict):
        errors.append(failure(file, "validation_expectation", "validation_expectation must be an object", "record validation expectation"))
    else:
        errors.extend(require_fields(validation, {"required", "commands"}, file, "validation_expectation"))
        if not isinstance(validation.get("required"), bool):
            errors.append(failure(file, "validation_expectation.required", "required must be boolean", "set required to true or false"))
        commands = validation.get("commands")
        if validation.get("required") is True and (not isinstance(commands, list) or not commands):
            errors.append(failure(file, "validation_expectation.commands", "required validation needs commands", "add validation command expectations"))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_dispatch_table(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.dispatchTable")
    errors.extend(require_fields(data, {"table_id", "version", "scheduler_id", "created_at", "state_root", "entries", "next_action"}, file, "dispatch_table"))
    errors.extend(validate_version(root, path, data.get("version")))
    ids = []
    for entry in data.get("entries", []):
        errors.extend(require_fields(entry, {"instruction_id", "unit_id", "status", "expected_report_type", "report_output_path", "report_to_thread_id", "assigned_scope", "next_action"}, file, "dispatch entry"))
        ids.append(entry.get("instruction_id"))
        errors.extend(require_enum(file, "entries.status", entry.get("status"), DISPATCH_STATUSES, "dispatch entry status"))
        errors.extend(require_enum(file, "entries.expected_report_type", entry.get("expected_report_type"), REPORT_TYPES, "expected_report_type"))
        errors.extend(validate_next_action(root, path, entry.get("next_action")))
    if len(ids) != len(set(ids)):
        errors.append(failure(file, "entries.instruction_id", "instruction_id values must be unique", "deduplicate dispatch entries"))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_scheduler_pool(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.schedulerPool")
    errors.extend(require_fields(data, {"pool_id", "version", "created_at", "state_root", "schedulers", "next_action"}, file, "scheduler_pool"))
    errors.extend(validate_version(root, path, data.get("version")))
    ids = []
    for scheduler in data.get("schedulers", []):
        errors.extend(require_fields(scheduler, {"scheduler_id", "unit_id", "status", "report_inbox", "next_action"}, file, "scheduler"))
        ids.append(scheduler.get("scheduler_id"))
        errors.extend(require_enum(file, "schedulers.status", scheduler.get("status"), SCHEDULER_STATUSES, "scheduler status"))
        errors.extend(validate_next_action(root, path, scheduler.get("next_action")))
    if len(ids) != len(set(ids)):
        errors.append(failure(file, "schedulers.scheduler_id", "scheduler_id values must be unique", "deduplicate schedulers"))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_channel_state(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.channelState")
    errors.extend(require_fields(data, {"channel_id", "channel_type", "state", "version", "updated_at", "release_predicate", "waiting_scheduler_ids", "next_action"}, file, "channel_state"))
    errors.extend(require_enum(file, "channel_type", data.get("channel_type"), CHANNEL_TYPES, "channel_type"))
    errors.extend(require_enum(file, "state", data.get("state"), CHANNEL_STATES, "channel state"))
    errors.extend(validate_version(root, path, data.get("version")))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_waiting_queue(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.waitingQueue")
    errors.extend(require_fields(data, {"queue_id", "version", "channel_id", "updated_at", "items", "next_action"}, file, "waiting_queue"))
    errors.extend(validate_version(root, path, data.get("version")))
    ids = []
    for item in data.get("items", []):
        errors.extend(require_fields(item, {"wait_id", "scheduler_id", "unit_id", "request_id", "requested_paths", "resume_condition", "allowed_non_channel_work", "forbidden_until_grant", "next_readback_at"}, file, "waiting item"))
        ids.append(item.get("wait_id"))
        if not item.get("requested_paths"):
            errors.append(failure(file, "items.requested_paths", "requested_paths must be non-empty", "add requested paths"))
        if not item.get("forbidden_until_grant"):
            errors.append(failure(file, "items.forbidden_until_grant", "forbidden_until_grant must be non-empty", "add forbidden actions"))
    if len(ids) != len(set(ids)):
        errors.append(failure(file, "items.wait_id", "wait_id values must be unique", "deduplicate waiting items"))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_channel_event(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.channelEvent")
    errors.extend(require_fields(data, {"event_id", "event_type", "version", "channel_id", "scheduler_id", "unit_id", "created_at", "next_action"}, file, "channel_event"))
    errors.extend(require_enum(file, "event_type", data.get("event_type"), EVENT_TYPES, "event_type"))
    errors.extend(validate_version(root, path, data.get("version")))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_watcher_decision(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.watcherDecision")
    errors.extend(require_fields(data, {"decision_id", "decision_type", "version", "watcher_id", "created_at", "inputs", "rationale", "next_action"}, file, "watcher_decision"))
    errors.extend(require_enum(file, "decision_type", data.get("decision_type"), DECISION_TYPES, "decision_type"))
    if not data.get("inputs"):
        errors.append(failure(file, "inputs", "inputs must be non-empty", "cite consumed input locators"))
    errors.extend(validate_version(root, path, data.get("version")))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


def validate_watcher_inbox(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, str]]:
    file = rel(root, path)
    errors = common(root, path, data, "loopengineer.watcherInbox")
    errors.extend(
        require_fields(
            data,
            {
                "inbox_id",
                "version",
                "watcher_id",
                "generated_at",
                "state_root",
                "sources",
                "summary",
                "unconsumed_scheduler_reports",
                "unconsumed_channel_events",
                "unacked_scheduler_instructions",
                "stale_heartbeat_targets",
                "stale_channel_owners",
                "candidate_units",
                "required_next_actions",
                "next_action",
            },
            file,
            "watcher_inbox",
        )
    )
    if not isinstance(data.get("inbox_id"), str) or not data.get("inbox_id", "").startswith("watcher-inbox-"):
        errors.append(failure(file, "inbox_id", "inbox_id must start with watcher-inbox-", "use a watcher-inbox-* id"))
    if not data.get("sources"):
        errors.append(failure(file, "sources", "sources must be non-empty", "cite inbox source locators"))
    summary = data.get("summary")
    if not isinstance(summary, dict):
        errors.append(failure(file, "summary", "summary must be an object", "add watcher inbox summary counts"))
    else:
        errors.extend(require_fields(summary, WATCHER_INBOX_SUMMARY_FIELDS, file, "summary"))
        for field in sorted(WATCHER_INBOX_SUMMARY_FIELDS):
            value = summary.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(failure(file, f"summary.{field}", "summary count must be a non-negative integer", "set count to zero or greater"))
    for report in data.get("unconsumed_scheduler_reports", []):
        errors.extend(require_fields(report, {"report_id", "scheduler_id", "report_path", "report_type", "created_at"}, file, "unconsumed scheduler report"))
        errors.extend(require_enum(file, "unconsumed_scheduler_reports.report_type", report.get("report_type"), REPORT_TYPES, "report_type"))
    for event in data.get("unconsumed_channel_events", []):
        errors.extend(require_fields(event, {"event_id", "event_type", "channel_id", "event_path", "created_at"}, file, "unconsumed channel event"))
        errors.extend(require_enum(file, "unconsumed_channel_events.event_type", event.get("event_type"), EVENT_TYPES, "event_type"))
    for instruction in data.get("unacked_scheduler_instructions", []):
        errors.extend(require_fields(instruction, {"instruction_id", "scheduler_id", "sent_at", "expected_report_type", "next_readback_at"}, file, "unacked scheduler instruction"))
        errors.extend(require_enum(file, "unacked_scheduler_instructions.expected_report_type", instruction.get("expected_report_type"), REPORT_TYPES, "expected_report_type"))
    for heartbeat in data.get("stale_heartbeat_targets", []):
        errors.extend(require_fields(heartbeat, {"scheduler_id", "expected_thread_id", "observed_thread_id", "last_checked_at"}, file, "stale heartbeat target"))
    for owner in data.get("stale_channel_owners", []):
        errors.extend(require_fields(owner, {"channel_id", "owner_scheduler_id", "stale_reason", "next_readback_at"}, file, "stale channel owner"))
    for unit in data.get("candidate_units", []):
        errors.extend(require_fields(unit, {"unit_id", "readiness", "source"}, file, "candidate unit"))
        errors.extend(require_enum(file, "candidate_units.readiness", unit.get("readiness"), {"ready", "blocked", "needs_readback"}, "candidate readiness"))
    for action in data.get("required_next_actions", []):
        errors.extend(require_fields(action, {"owner", "action", "source"}, file, "required next action"))
        errors.extend(require_enum(file, "required_next_actions.owner", action.get("owner"), NEXT_ACTION_OWNERS, "required next action owner"))
    errors.extend(validate_version(root, path, data.get("version")))
    errors.extend(validate_next_action(root, path, data.get("next_action")))
    return errors


VALIDATORS: dict[str, Callable[[Path, Path, dict[str, Any]], list[dict[str, str]]]] = {
    "loopengineer.contextBudget": validate_context_budget,
    "loopengineer.handoffManifest": validate_handoff_manifest,
    "loopengineer.report": validate_report,
    "loopengineer.subagentAssignment": validate_subagent_assignment,
    "loopengineer.dispatchTable": validate_dispatch_table,
    "loopengineer.schedulerPool": validate_scheduler_pool,
    "loopengineer.channelState": validate_channel_state,
    "loopengineer.waitingQueue": validate_waiting_queue,
    "loopengineer.channelEvent": validate_channel_event,
    "loopengineer.watcherDecision": validate_watcher_decision,
    "loopengineer.watcherInbox": validate_watcher_inbox,
}


def default_inputs(root: Path) -> list[Path]:
    examples = root / "schemas/v1/examples"
    return sorted(examples.glob("*.valid.json")) + sorted((root / "schemas/v1").glob("*.default.json"))


def validate_file(root: Path, path: Path) -> list[dict[str, str]]:
    data, errors = load_json(root, path)
    if data is None:
        return errors
    kind = data.get("kind")
    validator = VALIDATORS.get(kind)
    if validator is None:
        errors.append(
            failure(
                rel(root, path),
                "kind",
                f"unsupported kind {kind!r}",
                "use a supported LoopEngineer structure kind",
            )
        )
        return errors
    return errors + validator(root, path, data)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate LoopEngineer structure files.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument(
        "--input-file",
        action="append",
        help="Specific structure file to validate. May be passed more than once.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    paths = [Path(item) for item in args.input_file] if args.input_file else default_inputs(root)
    paths = [path if path.is_absolute() else root / path for path in paths]
    failures: list[dict[str, str]] = []
    for path in paths:
        try:
            failures.extend(validate_file(root, path))
        except Exception as exc:  # noqa: BLE001 - CLI must fail closed with JSON.
            failures.append(
                failure(
                    rel(root, path),
                    "validation",
                    f"validator failed: {exc}",
                    "fix the structure shape or validator rule so validation can complete",
                )
            )
    payload = {
        "status": "pass" if not failures else "fail",
        "checkedFiles": [rel(root, path) for path in paths],
        "failures": failures,
    }
    emit(payload)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
