#!/usr/bin/env python3
"""Minimal stdio MCP adapter for LoopEngineer."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "loopengineer.py"
PROTOCOL_VERSION = "2025-06-18"


TOOLS: dict[str, dict[str, Any]] = {
    "loopengineer.context_guard": {
        "command": "context-guard",
        "description": "Check text against a LoopEngineer context budget profile.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string"},
                "input_file": {"type": "string"},
                "budget_file": {"type": "string"},
            },
            "required": ["profile", "input_file"],
            "additionalProperties": False,
        },
    },
    "loopengineer.validate_structures": {
        "command": "validate-structures",
        "description": "Validate LoopEngineer structure files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
    },
    "loopengineer.state_digest": {
        "command": "state-digest",
        "description": "Build compact LoopEngineer state digests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["minimal", "full"]},
                "input_file": {"type": "array", "items": {"type": "string"}},
                "report_inbox_glob": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    "loopengineer.loop_audit": {
        "command": "loop-audit",
        "description": "Audit LoopEngineer loop state for orchestration drift.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "array", "items": {"type": "string"}},
                "report_glob": {"type": "array", "items": {"type": "string"}},
                "receipt_glob": {"type": "array", "items": {"type": "string"}},
                "current_owner": {"type": "string", "enum": ["worker", "scheduler", "watcher", "user", "external"]},
                "now": {"type": "string"},
                "stale_after_minutes": {"type": "integer", "minimum": 0},
            },
            "additionalProperties": False,
        },
    },
    "loopengineer.coordination_tax": {
        "command": "coordination-tax",
        "description": "Estimate LoopEngineer coordination cost.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "control_plane_tokens": {"type": "integer", "minimum": 0},
                "cross_thread_messages": {"type": "integer", "minimum": 0},
                "reports_read": {"type": "integer", "minimum": 0},
                "reports_written": {"type": "integer", "minimum": 0},
                "heartbeats": {"type": "integer", "minimum": 0},
                "recovery_actions": {"type": "integer", "minimum": 0},
                "workers": {"type": "integer", "minimum": 0},
                "schedulers": {"type": "integer", "minimum": 0},
            },
            "additionalProperties": False,
        },
    },
    "loopengineer.provider_selection": {
        "command": "provider-select",
        "description": "Recommend a worker_lite provider without spawning workers or mutating state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_risk": {"type": "string", "enum": ["low", "medium", "high"]},
                "write_scope": {"type": "string", "enum": ["none", "local", "shared-contract", "external"]},
                "duration": {"type": "string", "enum": ["short", "medium", "long"]},
                "needs_gate": {"type": "boolean"},
                "external_action": {"type": "boolean"},
                "shared_state": {"type": "boolean"},
                "requires_recovery": {"type": "boolean"},
                "parallelizable": {"type": "boolean"},
                "isolated_scope": {"type": "boolean"},
                "prefer_delegation": {"type": "boolean"},
                "worktree_required": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    "loopengineer.preflight": {
        "command": "preflight",
        "description": "Return a session admission reminder without state transition or runtime lifecycle action.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
}


def error_response(request_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def result_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def server_version() -> str:
    try:
        metadata = json.loads((ROOT / "metadata/loopengineer.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - version read failure must not break MCP initialization.
        return "unknown"
    value = metadata.get("version")
    return value if isinstance(value, str) and value else "unknown"


def tool_descriptor(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "description": spec["description"],
        "inputSchema": spec["inputSchema"],
    }


def validate_object(value: Any, *, label: str) -> tuple[dict[str, Any] | None, str | None]:
    if value is None:
        return {}, None
    if not isinstance(value, dict):
        return None, f"{label} must be an object"
    return value, None


def add_repeated(argv: list[str], flag: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return f"{flag} must be an array of strings"
    for item in value:
        argv.extend([flag, item])
    return None


def add_string(argv: list[str], flag: str, value: Any, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            return f"{flag} is required"
        return None
    if not isinstance(value, str):
        return f"{flag} must be a string"
    argv.extend([flag, value])
    return None


def add_non_negative_int(argv: list[str], flag: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return f"{flag} must be a non-negative integer"
    argv.extend([flag, str(value)])
    return None


def add_bool_flag(argv: list[str], flag: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        return f"{flag} must be a boolean"
    if value:
        argv.append(flag)
    return None


def args_for_tool(name: str, arguments: dict[str, Any]) -> tuple[list[str] | None, str | None]:
    extra = set(arguments) - set(TOOLS[name]["inputSchema"]["properties"])
    if extra:
        return None, "unsupported argument(s): " + ", ".join(sorted(extra))
    if name == "loopengineer.context_guard":
        argv: list[str] = []
        for error in (
            add_string(argv, "--profile", arguments.get("profile"), required=True),
            add_string(argv, "--input-file", arguments.get("input_file"), required=True),
            add_string(argv, "--budget-file", arguments.get("budget_file")),
        ):
            if error:
                return None, error
        return argv, None
    if name == "loopengineer.validate_structures":
        argv = []
        error = add_repeated(argv, "--input-file", arguments.get("input_file"))
        return (None, error) if error else (argv, None)
    if name == "loopengineer.state_digest":
        argv = []
        mode = arguments.get("mode")
        if mode is not None:
            if mode not in {"minimal", "full"}:
                return None, "mode must be minimal or full"
            argv.extend(["--mode", mode])
        for error in (
            add_repeated(argv, "--input-file", arguments.get("input_file")),
            add_string(argv, "--report-inbox-glob", arguments.get("report_inbox_glob")),
        ):
            if error:
                return None, error
        return argv, None
    if name == "loopengineer.loop_audit":
        argv = []
        for error in (
            add_repeated(argv, "--input-file", arguments.get("input_file")),
            add_repeated(argv, "--report-glob", arguments.get("report_glob")),
            add_repeated(argv, "--receipt-glob", arguments.get("receipt_glob")),
            add_string(argv, "--current-owner", arguments.get("current_owner")),
            add_string(argv, "--now", arguments.get("now")),
            add_non_negative_int(argv, "--stale-after-minutes", arguments.get("stale_after_minutes")),
        ):
            if error:
                return None, error
        return argv, None
    if name == "loopengineer.coordination_tax":
        argv = []
        for key in (
            "control_plane_tokens",
            "cross_thread_messages",
            "reports_read",
            "reports_written",
            "heartbeats",
            "recovery_actions",
            "workers",
            "schedulers",
        ):
            error = add_non_negative_int(argv, "--" + key.replace("_", "-"), arguments.get(key))
            if error:
                return None, error
        return argv, None
    if name == "loopengineer.provider_selection":
        argv = []
        for key in ("task_risk", "write_scope", "duration"):
            value = arguments.get(key)
            if value is not None:
                argv.extend(["--" + key.replace("_", "-"), value])
        for key in (
            "needs_gate",
            "external_action",
            "shared_state",
            "requires_recovery",
            "parallelizable",
            "isolated_scope",
            "prefer_delegation",
            "worktree_required",
        ):
            error = add_bool_flag(argv, "--" + key.replace("_", "-"), arguments.get(key))
            if error:
                return None, error
        return argv, None
    if name == "loopengineer.preflight":
        if arguments:
            return None, "preflight does not accept arguments"
        return [], None
    return None, f"unknown tool {name}"


def call_engine(command: str, argv: list[str]) -> tuple[int, dict[str, Any] | None, str | None]:
    completed = subprocess.run(
        [sys.executable, str(ENGINE), command, *argv],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return completed.returncode, None, f"engine returned invalid JSON: {exc}"
    if not isinstance(payload, dict):
        return completed.returncode, None, "engine returned non-object JSON"
    return completed.returncode, payload, None


def tool_result(payload: dict[str, Any], *, is_error: bool) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, sort_keys=True),
            }
        ],
        "structuredContent": payload,
        "isError": is_error,
    }


class McpServer:
    def __init__(self) -> None:
        self.initialize_accepted = False
        self.initialized = False

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        has_id = "id" in message
        request_id = message.get("id")
        if has_id and (request_id is None or isinstance(request_id, bool) or not isinstance(request_id, (str, int))):
            return error_response(None, -32600, "request id must be a string or number")

        method = message.get("method")
        if not isinstance(method, str):
            return None if not has_id else error_response(request_id, -32600, "method must be a string")

        if not has_id:
            return self.handle_notification(method, message.get("params"))

        params, error = validate_object(message.get("params"), label="params")
        if error:
            return error_response(request_id, -32602, error)
        if method == "initialize":
            error = self.validate_initialize_params(params or {})
            if error:
                return error_response(request_id, -32602, error)
            self.initialize_accepted = True
            return result_response(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": "loopengineer",
                        "version": server_version(),
                    },
                    "capabilities": {
                        "tools": {},
                    },
                },
            )
        if method == "ping":
            return result_response(request_id, {})
        if method in {"tools/list", "tools/call"} and not self.initialized:
            return error_response(request_id, -32002, "server is not initialized")
        if method == "tools/list":
            return result_response(
                request_id,
                {"tools": [tool_descriptor(name, spec) for name, spec in sorted(TOOLS.items())]},
            )
        if method == "tools/call":
            return self.handle_tool_call(request_id, params or {})
        return error_response(request_id, -32601, f"unknown method {method}")

    def handle_notification(self, method: str, raw_params: Any) -> None:
        if method != "notifications/initialized":
            return None
        params, error = validate_object(raw_params, label="params")
        if error:
            return None
        if params:
            return None
        if self.initialize_accepted:
            self.initialized = True
        return None

    def validate_initialize_params(self, params: dict[str, Any]) -> str | None:
        protocol_version = params.get("protocolVersion")
        if not isinstance(protocol_version, str) or not protocol_version:
            return "initialize requires protocolVersion"
        if protocol_version != PROTOCOL_VERSION:
            return f"unsupported protocolVersion {protocol_version}"
        capabilities = params.get("capabilities")
        if not isinstance(capabilities, dict):
            return "initialize requires capabilities object"
        client_info = params.get("clientInfo")
        if not isinstance(client_info, dict):
            return "initialize requires clientInfo object"
        if not isinstance(client_info.get("name"), str) or not client_info.get("name"):
            return "initialize requires clientInfo.name"
        if not isinstance(client_info.get("version"), str) or not client_info.get("version"):
            return "initialize requires clientInfo.version"
        return None

    def handle_tool_call(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str):
            return error_response(request_id, -32602, "tools/call requires a string name")
        if name not in TOOLS:
            return error_response(request_id, -32602, f"unknown tool {name}")
        arguments, error = validate_object(params.get("arguments"), label="arguments")
        if error:
            return error_response(request_id, -32602, error)
        argv, error = args_for_tool(name, arguments or {})
        if error:
            return error_response(request_id, -32602, error)
        returncode, payload, error = call_engine(TOOLS[name]["command"], argv or [])
        if error:
            return error_response(request_id, -32603, error)
        return result_response(request_id, tool_result(payload or {}, is_error=returncode != 0))


def parse_line(line: str) -> dict[str, Any] | None:
    try:
        value = json.loads(line)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def main() -> int:
    server = McpServer()
    for line in sys.stdin:
        message = parse_line(line)
        if message is None:
            emit = error_response(None, -32700, "parse error")
        else:
            emit = server.handle(message)
        if emit is not None:
            print(json.dumps(emit, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
