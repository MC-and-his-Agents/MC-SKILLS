# LoopEngineer Versioning

LoopEngineer uses layered versioning. Product releases, plugin compatibility, loop protocols, engine contracts, schemas, skills, and external adapters are related but separate compatibility boundaries.

## Version Layers

| Layer | Field or file | Purpose |
| --- | --- | --- |
| Product version | `VERSION`, Git tag `vX.Y.Z`, `metadata/loopengineer.json.version` | External LoopEngineer release identity. |
| Plugin API version | `metadata/loopengineer.json.pluginApiVersion`, plugin manifest `version` when the plugin skeleton exists | Codex plugin packaging and host compatibility. |
| Protocol version | `protocolVersion` | Skill entrypoint, routing, scheduling, report consumption, and handoff protocol compatibility. |
| Engine contract version | `engineContractVersion` | Runtime-neutral CLI/JSON engine contract compatibility. |
| Schema version | `schemaMajorVersion`, schema file `schemaVersion`, instance `schemaVersion` | Structured state, reports, budgets, manifests, and tables compatibility. |
| Skill contract version | `skillContractVersion` in each `skills/*/skill.yaml` | Skill trigger, entrypoint, reads, writes, and expected output compatibility. |
| Adapter contract version | `adapterContractVersion` | Optional external integration contract compatibility, including future Loom adapters. |

Do not collapse these fields into one version. A product patch can update documentation without changing protocol compatibility. A schema major change can require migration even when the plugin API stays the same.

## Product Version

`VERSION` contains only the product version:

```text
0.1.0
```

Product versions use SemVer:

```text
MAJOR.MINOR.PATCH
```

Before `1.0.0`, compatibility can still change, but changes must be documented. The intended early roadmap is:

- `0.1.0`: context safety minimum version, plugin skeleton metadata, and lightweight routing baseline.
- `0.2.0`: core skill import, short entrypoints, and protocol profiles.
- `0.3.0`: structure definitions and deterministic scripts.
- `0.4.0`: loop audit, cost control, and watcher strategy.
- `0.5.0`: runtime-neutral CLI/JSON engine contract and optional adapters.
- `0.6.0`: subagent-backed `worker_lite` provider contract and deterministic checks.
- `1.0.0`: stable protocol, schemas, skill entrypoints, and migration strategy.

Release tags use `vX.Y.Z`, for example `v0.1.0`.

## Repository Metadata

`metadata/loopengineer.json` is the repository-level metadata carrier. Its `version` field is the product release version and must match `VERSION`.

Compatibility fields must not be mixed:

- `version` is the LoopEngineer product version.
- `pluginApiVersion` is the Codex plugin API compatibility boundary.
- `protocolVersion` is the loop protocol compatibility boundary.
- `engineContractVersion` is the runtime-neutral CLI/JSON engine contract boundary. `0` means no stable engine contract is available yet.
- `schemaMajorVersion` is the latest stable schema major line.
- `skillContractVersion` is the baseline skill contract version for skills that do not declare a newer contract.
- `adapterContractVersion` is the external adapter compatibility boundary. `0` means no stable adapter contract is available yet.

## Plugin Version

When the Codex plugin manifest is introduced, its package `version` should normally start aligned with the product version. It is still a plugin packaging version, not a replacement for product, protocol, schema, or skill contract versions.

Changing plugin host requirements can require a plugin version bump even when the loop protocol remains unchanged.

## Protocol Version

`protocolVersion` covers compatibility of agent loop behavior:

- routing profile names and meanings;
- context guard admission semantics;
- worker, scheduler, watcher, and audit role boundaries;
- report consumption and state transition requirements;
- handoff and recovery protocol expectations.

Compatible additions can stay in the same protocol version. Removing a required field, changing role ownership semantics, or changing completion and evidence rules requires a new protocol version.

## Engine Contract Version

`engineContractVersion` covers compatibility of the runtime-neutral CLI/JSON
engine contract:

- command names and capability names;
- JSON envelope fields;
- exit code meanings;
- required input arguments;
- stable result and failure locations for engine callers.

The initial value is `0`, meaning no stable engine contract has been published.
The first stable CLI/JSON engine contract should move to `1` after #28 defines
the boundary and #82 lands the entrypoint.

MCP and host hooks do not define the engine contract. They are adapters over
the CLI/JSON engine contract unless a later issue explicitly changes that
boundary.

## Skill Contract Version

Each skill must declare a `skill.yaml` when the skill is added:

```yaml
id: context-safety
name: Context Safety
version: 0.1.0
skillContractVersion: 1
requires:
  loopengineer: ">=0.1.0 <0.2.0"
  protocolVersion: "1"
reads:
  - schemas/v1/context-budget.schema.json
  - schemas/v1/handoff.schema.json
entrypoint: README.md
stability: experimental
```

Rules:

- Small compatible skill content changes bump the skill patch version.
- Compatible new skill capability bumps the skill minor version.
- Incompatible trigger, entrypoint, reads, writes, output, or role semantics require a new `skillContractVersion` or product major boundary.
- Existing skills, if present, must declare `version` and `skillContractVersion`.

## Schema Version

Schema files live under major-versioned directories:

```text
schemas/v1/report.schema.json
schemas/v2/report.schema.json
```

Every schema file must declare:

- `$id`
- `schemaVersion`
- `kind`

Every persisted schema instance must also declare `schemaVersion`.

Example instance:

```json
{
  "schemaVersion": "1.0",
  "kind": "loopengineer.report",
  "id": "report-20260615-001",
  "type": "worker-completion",
  "role": "worker",
  "status": "completed",
  "producer": "worker-a",
  "createdAt": "2026-06-15T00:00:00Z",
  "nextAction": {
    "owner": "scheduler",
    "action": "consume-report"
  }
}
```

Rules:

- `schemas/v1/` allows compatible additions only.
- Removing fields, changing field semantics, or changing required fields requires `schemas/v2/`.
- Scripts should default to the latest stable schema major and allow an explicit schema version, for example `--schema-version v1`.
- Migration scripts are not required until real persisted v1 data exists and a breaking v2 change is needed.

## Adapter Contract Version

External integrations, including Loom, use `adapterContractVersion`.

The initial value is `0`, meaning no stable external adapter contract has been published. The first stable adapter contract should move to `1` only after the external boundary is documented and smoke-test planning exists.

LoopEngineer must not write Loom-owned `.loom/` state directly. Future adapter contracts should define check, verify, recommend, and smoke-test boundaries before install or register actions.

## Changelog

`CHANGELOG.md` is organized by product version. Each release entry should include:

- Added
- Changed
- Deprecated
- Removed
- Compatibility

The compatibility section records the versions that reviewers need to reason about release impact:

```markdown
### Compatibility

- pluginApiVersion: 1
- protocolVersion: 1
- engineContractVersion: 0
- schemaMajorVersion: 1
- skillContractVersion: 1
- adapterContractVersion: 0
```

## Release Gate

Before a release tag is created, confirm:

- `VERSION` is updated.
- `CHANGELOG.md` contains the product version.
- `metadata/loopengineer.json.version` matches `VERSION`.
- Existing `skills/*/skill.yaml` files declare `version` and `skillContractVersion`.
- Existing `schemas/v*/...schema.json` files declare `$id`, `schemaVersion`, and `kind`.
- Examples and tests for changed structures pass when they exist.
- The tag uses `vX.Y.Z`.

## Future Check Script

`scripts/check_version.py` is intentionally not implemented in this issue. Its minimum checks should be:

- `VERSION` equals `metadata/loopengineer.json.version`.
- `CHANGELOG.md` contains the current product version.
- `metadata/loopengineer.json.engineContractVersion` exists.
- Every existing `skills/*/skill.yaml` declares `version` and `skillContractVersion`.
- Every existing `schemas/v*/...schema.json` declares `$id`, `schemaVersion`, and `kind`.

The script should fail closed and print the failing file, field, and suggested action.
