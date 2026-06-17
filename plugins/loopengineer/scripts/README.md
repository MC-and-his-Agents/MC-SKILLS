# Scripts

This directory is the future home for deterministic LoopEngineer scripts.

Current status:

- `check_version.py` checks product version metadata, skill metadata, schema metadata,
  and the changelog release entry;
- `check_release_readiness.py` aggregates release readiness checks without creating
  tags, releases, packages, or other external artifacts;
- `consume_report.py` validates a report artifact, writes a consumption receipt,
  and emits a compact scheduler/watcher summary; when passed a subagent
  assignment, it first checks assignment/report eligibility;
- `coordination_tax.py` estimates coordination cost and recommends the lightest
  sufficient routing profile without changing external state;
- `context_guard.py` checks text against a v1 context budget profile;
- `loop_audit.py` audits LoopEngineer state for unconsumed reports, missing ACKs,
  stale targets, waiting recovery gaps, and channel release evidence gaps;
- `loopengineer.py` is the runtime-neutral CLI/JSON engine entrypoint; it wraps
  read-only, diagnostic, validation, and admission reminder capabilities in a
  stable JSON envelope;
- `provider_selection.py` recommends the lightest `worker_lite` provider
  (`direct`, `subagent`, or `thread`) without spawning workers or mutating state;
- `prepare_manual_release.py` prepares the fail-closed tag and GitHub Release
  plan used by manual and automatic release workflows;
- `state_digest.py` builds compact state summaries for heartbeat and handoff prompts;
- `subagent_report_check.py` validates subagent assignment/report binding before
  a subagent report can be consumed;
- `validate_structures.py` checks LoopEngineer structure files and examples;
- future watcher inbox tooling should keep watcher wakeups summary-first and
  locator-backed;
- scripts must output machine-readable results and fail closed when added;
- scripts must not implicitly modify GitHub, git, PRs, issues, or external state.

Related issues include #6, #20, #21, #22, #23, #27, #46, #64, #65, #82, #30,
#87, #92, and #93.

Optional MCP adapter:

- `../mcp/loopengineer_stdio.py` exposes only the read-only, diagnostic,
  validation, provider selection, and preflight engine capabilities over stdio
  JSON-RPC. It does not expose `consume_report.py`.
