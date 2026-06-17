# Changelog

All notable LoopEngineer product changes are recorded by product version.

## 0.6.1 - 2026-06-17

### Added

- Fail-closed automatic GitHub Release workflow for `main` release-material
  changes, creating a public tag and draft GitHub Release.
- Automatic release planning mode that derives `vX.Y.Z` from `VERSION` and
  records release mode and draft status in evidence.
- README marketing badges for LoopEngineer positioning and latest release
  visibility.

### Changed

- Manual release workflow is now documented and retained as the fallback path.
- Release notes generation distinguishes manual and automatic release triggers.

### Deprecated

- None.

### Removed

- README Project Records sections.

### Compatibility

- pluginApiVersion: 1
- protocolVersion: 1
- engineContractVersion: 1
- schemaMajorVersion: 1
- skillContractVersion: 1
- adapterContractVersion: 0

## 0.6.0 - 2026-06-17

### Added

- `worker_lite` provider contract for `direct`, `subagent`, and `thread`.
- ADR 0005 recording the subagent/thread experiment and control-plane boundary.
- Subagent assignment schema, examples, validation, and report provider context.
- Deterministic provider recommendation through `provider_selection.py` and
  `loopengineer.py provider-select`.
- Subagent report eligibility check and optional assignment-aware
  `consume_report.py` receipt metadata.

### Changed

- Worker and routing protocols now define when subagent provider is sufficient
  and when work must escalate to a formal thread worker.
- Report consumption guidance now treats subagent final answers as auxiliary
  evidence, not completion proof.

### Deprecated

- None.

### Removed

- None.

### Compatibility

- pluginApiVersion: 1
- protocolVersion: 1
- engineContractVersion: 1
- schemaMajorVersion: 1
- skillContractVersion: 1
- adapterContractVersion: 0

## 0.5.0 - 2026-06-16

### Added

- Runtime-neutral Loop Engine interface contract and ADR.
- `engineContractVersion` compatibility boundary.
- Unified CLI/JSON engine entrypoint with a stable JSON envelope.
- Session preflight / admission reminder capability.
- Optional stdio MCP adapter over the CLI/JSON engine contract.

### Changed

- M6 now treats CLI/JSON as the primary product surface, with MCP as an optional
  adapter.
- Release readiness now checks repository metadata compatibility fields,
  including `engineContractVersion`.

### Deprecated

- None.

### Removed

- None.

### Compatibility

- pluginApiVersion: 1
- protocolVersion: 1
- engineContractVersion: 1
- schemaMajorVersion: 1
- skillContractVersion: 1
- adapterContractVersion: 0

## 0.4.0 - 2026-06-16

### Added

- Lazy shared channel policy for disabled, declared-forbidden-scope, and active-locking modes.
- Watcher inbox schema, examples, validation, digest support, and summary-first design guidance.
- Watcher automation mode and rotation policy using inbox/digest-first reads and context budget thresholds.
- Coordination cost model and `coordination_tax.py` advisory routing script.
- Loop audit skill and `loop_audit.py` for deterministic checks of common orchestration drift.

### Changed

- Scheduler watcher skill metadata now references the local watcher inbox and rotation policy.
- Script, schema, and skill indexes now include the M5 audit, cost, and watcher policy surface.

### Deprecated

- None.

### Removed

- None.

### Compatibility

- pluginApiVersion: 1
- protocolVersion: 1
- engineContractVersion: 0
- schemaMajorVersion: 1
- skillContractVersion: 1
- adapterContractVersion: 0

## 0.1.0 - 2026-06-15

### Added

- Initial product version file.
- Initial repository metadata file.
- Versioning policy for product, plugin API, protocol, schema, skill contract, and adapter contract boundaries.

### Changed

- None.

### Deprecated

- None.

### Removed

- None.

### Compatibility

- pluginApiVersion: 1
- protocolVersion: 1
- engineContractVersion: 0
- schemaMajorVersion: 1
- skillContractVersion: 1
- adapterContractVersion: 0
