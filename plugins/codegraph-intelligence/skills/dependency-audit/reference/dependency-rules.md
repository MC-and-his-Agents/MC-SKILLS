# Dependency Audit Rules

Use these rules to classify module relationships and dependency risks.

## Dependency Categories

- **Inbound dependency**: another module imports, calls or references this module.
- **Outbound dependency**: this module imports, calls or references another module.
- **Stable dependency**: dependency points from higher-level policy to lower-level utility or platform code.
- **Volatile dependency**: dependency points to code that changes frequently, owns business workflow or has external side effects.
- **Boundary dependency**: dependency crosses package, service, domain, layer or ownership boundaries.

## Coupling Signals

Flag tight coupling when:

- Two modules import from each other or call each other in both directions.
- A module has both high inbound and high outbound dependencies.
- Feature code imports infrastructure details directly across many files.
- UI, controller or route layers depend on storage, transport or vendor SDKs without an intermediate boundary.
- Shared utilities import feature-specific modules.
- Tests require many unrelated modules to boot a small unit.

## Cycle Signals

Flag a cycle when:

- Module A imports B and B imports A.
- A chain returns to the starting module: A -> B -> C -> A.
- Runtime registration hides the cycle but static imports or framework wiring reveal mutual dependency.

Classify cycle severity:

- **Low**: test-only or type-only cycle with no runtime effect.
- **Medium**: runtime cycle inside one package or layer.
- **High**: cross-package, cross-domain or initialization-order cycle.
- **Unknown**: graph is incomplete or dynamic imports hide the edge.

## Recommended Output Fields

- Modules audited.
- Inbound dependencies.
- Outbound dependencies.
- Boundary crossings.
- Possible cycles.
- Coupling risks.
- Incremental remediation options.
- Evidence gaps.
