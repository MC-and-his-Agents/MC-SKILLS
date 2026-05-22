# Dead Code False Positive Checklist

Use this checklist before labeling any symbol as dead code. A symbol with zero static callers is only a candidate, not proof of deletion safety.

## Exclude From Dead Code Findings

Do not classify a symbol as high-confidence dead code when any item below applies.

- Public exports from package entrypoints, barrel files, plugin APIs, SDKs or generated type surfaces.
- HTTP routes, GraphQL resolvers, RPC handlers, CLI commands, background jobs, scheduled tasks or worker entrypoints.
- Framework lifecycle hooks such as React lifecycle methods, Vue hooks, Angular hooks, NestJS hooks, Rails callbacks, Django/Flask/FastAPI route handlers, Laravel controller actions, Spring annotations, Go handler registrations or test framework hooks.
- Dependency injection targets, decorators, annotations, reflection targets or symbols registered by container name.
- Symbols referenced by strings, config files, templates, generated code, routes, migrations, seed data, feature flags, manifests or external systems.
- Files or symbols exported for consumers outside the current repository.
- Test fixtures, snapshots, factories or helpers loaded dynamically by the test framework.
- Language magic methods and convention-based methods such as Python dunder methods, Ruby/Rails callbacks, Java serialization methods, Swift/C# protocol/interface implementations or Go interface methods.

## Confidence Rules

- **High confidence**: no callers, not exported, no route/handler role, no string/config/template reference, no framework convention match, and a targeted text search finds no non-static usage.
- **Medium confidence**: no callers, but exported, convention-named, dynamically reachable or only partially searched.
- **Low confidence**: static graph is missing, stale, ambiguous or the symbol belongs to a framework-heavy area.

## Required Evidence

Every candidate should include:

- Symbol name and file path.
- Static caller evidence from `codegraph_callers`.
- Export or public-surface status.
- False-positive checks completed.
- Remaining uncertainty.
- Recommended manual verification before deletion.
