# Runtime-Neutral Loop Engine Interface

Issue: #28

LoopEngineer exposes deterministic loop judgment capabilities. Its first M6
product surface is a runtime-neutral CLI/JSON engine contract, not MCP and not
a hook lifecycle.

## Product Shape

The engine contract is a one-shot judgment interface:

```text
runtime or host
  -> LoopEngineer CLI/JSON engine contract
  -> structured judgment
  -> runtime or host decides what to do next
```

LoopEngineer may be called by Loom or another runtime, but it does not become
the runtime. It does not schedule work, create automations, mutate the host,
write Loom `.loom/` facts, run gates, merge, close releases, or own lifecycle
state.

MCP is an optional adapter over the engine contract. Host hook examples, if
added, are admission reminder examples over the engine contract. Neither is the
core product surface.

The optional MCP adapter is a host-facing stdio JSON-RPC adapter. It exposes
tools only, calls `python3 scripts/loopengineer.py`, and does not implement
LoopEngineer judgment logic itself.

## First Contract Surface

The first engine contract exposes these capabilities:

- `context_guard`
- `validate_structures`
- `state_digest`
- `loop_audit`
- `coordination_tax`
- `provider_selection`
- `preflight` or `admission_reminder`

The canonical entrypoint is:

```text
python3 scripts/loopengineer.py <command>
```

The first command set is:

```text
context-guard
validate-structures
state-digest
loop-audit
coordination-tax
provider-select
preflight
```

Each command emits a JSON object with:

- `status`
- `capability`
- `summary`
- `result`
- `failures`

Exit code meanings are stable for engine callers:

- `0`: `status` is `pass`;
- `1`: `status` is `fail`;
- `2`: `status` is `error`.

`provider-select` is a read-only diagnostic recommendation. `consume_report` is
not part of the engine contract. It writes a consumption receipt and is a
`local-artifact-write` capability. It can only be added later through an
explicit gated local write policy.

## Risk Classes

Engine capabilities are classified before any adapter exposes them:

| Class | Meaning | M6 default |
| --- | --- | --- |
| `read-only` | Reads local files or metadata and emits JSON. | Allowed. |
| `diagnostic` | Produces summaries, findings, or recommendations. | Allowed. |
| `validation` | Fails closed on invalid structure or policy input. | Allowed. |
| `local-artifact-write` | Writes local receipts, reports, or generated files. | Denied by default. |
| `host-mutation` | Changes GitHub, git, CI, PRs, releases, automations, host state, or `.loom/`. | Denied. |

## Adapter Approval Assumptions

Any future adapter exposure of a `local-artifact-write` capability, including
`consume_report`, requires a separate approval policy. That policy must assume:

- the user or owning runtime explicitly opts in before the tool is exposed;
- writes are limited to an approved local artifact path or output directory;
- the tool cannot mutate GitHub, git, CI, PRs, releases, host state, or
  Loom-owned `.loom/` facts;
- invalid input, missing approval, or path ambiguity fails closed;
- adapter code enforces the same policy instead of relying only on caller
  discipline.

## First Denylist

M6 must not expose capabilities that:

- mutate GitHub, git, CI, PRs, releases, or production hosts;
- write Loom-owned `.loom/` facts;
- create workers, schedulers, watchers, threads, or automations;
- run gates, merge, release, or closeout lifecycle transitions;
- consume reports or write receipts without a later explicit local write policy.

## Optional MCP Adapter

The first MCP adapter maps only these tools to engine commands:

| MCP tool | Engine command |
| --- | --- |
| `loopengineer.context_guard` | `context-guard` |
| `loopengineer.validate_structures` | `validate-structures` |
| `loopengineer.state_digest` | `state-digest` |
| `loopengineer.loop_audit` | `loop-audit` |
| `loopengineer.coordination_tax` | `coordination-tax` |
| `loopengineer.provider_selection` | `provider-select` |
| `loopengineer.preflight` | `preflight` |

It must not expose `consume_report`, release readiness, GitHub, git, CI, PR,
merge, gate, worker, scheduler, watcher, automation, or `.loom` mutation
capabilities.

## Compatibility

`engineContractVersion` is the compatibility boundary for the CLI/JSON engine
contract. The value `0` means no stable engine contract has been published.

`adapterContractVersion` remains the compatibility boundary for optional
external adapters, including a future Loom adapter or optional MCP adapter.
An adapter can remain experimental even after the CLI/JSON engine contract
becomes stable.
