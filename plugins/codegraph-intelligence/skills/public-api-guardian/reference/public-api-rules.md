# Public API Rules

Use these rules before recommending rename, removal or signature changes for any symbol that may be consumed outside the immediate module.

## Public API Signals

Treat a symbol as public when any signal applies:

- Exported from package entrypoints, barrel files, SDK modules or documented modules.
- HTTP route, GraphQL resolver, RPC endpoint, webhook, CLI command, worker message handler or scheduled job.
- Config schema, environment variable contract, plugin hook, event name, queue name, topic name, migration format or file format.
- Type, interface, class, function or constant imported by more than one package, app, service or workspace.
- Documented in README, API docs, examples, generated docs or changelogs.
- Referenced by tests that look like integration, contract or e2e tests.

## External Consumer Signals

Assume external consumers may exist when:

- The symbol is exported from a published package or app boundary.
- The repository is a library, SDK, framework plugin, CLI or shared service.
- A route, command or schema is reachable over network, shell, config or persisted data.
- Consumers may call it by string, reflection, generated client or framework convention.
- CodeGraph cannot inspect all downstream repositories.

## Breaking Change Levels

- **Low**: internal-only implementation detail, no public export, no route or persisted contract, callers are all updated together.
- **Medium**: exported inside the repo or shared package, but callers are visible and can migrate in one change.
- **High**: public package export, route, CLI, config schema, persisted data shape or external service contract.
- **Unknown**: graph is stale, consumers are outside the repo, or dynamic usage is likely.

## Migration Patterns

Prefer non-breaking migration when risk is medium, high or unknown:

- Add wrapper or alias that forwards to the new implementation.
- Keep old route or command and emit deprecation warnings.
- Introduce versioned endpoint or schema.
- Document deprecation window and replacement path.
- Add contract/integration tests for both old and new behavior during migration.

## Required Output Fields

Every public API review should include:

- API surface and public-surface evidence.
- Known internal consumers.
- Possible external consumers.
- Breaking change level.
- Recommended migration strategy.
- Tests or contract checks required.
- Unknowns that block a safe destructive change.
