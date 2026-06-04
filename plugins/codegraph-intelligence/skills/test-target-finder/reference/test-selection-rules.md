# Test Selection Rules

Use these rules after collecting affected tests from CodeGraph or the CLI fallback script.

## Test Buckets

- **Minimal tests**: directly import, call or cover the changed symbol or changed file.
- **Caller tests**: cover direct callers or route/command entrypoints affected by the change.
- **Regression tests**: cover indirectly affected shared modules, integration paths or public contracts.
- **Full suite required**: use only when focused mapping is inconclusive or the change touches broad shared contracts.

## Escalate Beyond Minimal Tests When

- The change touches public APIs, auth, permissions, data persistence, migrations, payments, routing, build tooling or shared configuration.
- CodeGraph impact is stale, empty or ambiguous.
- Dynamic imports, generated code or framework conventions are involved.
- The changed file is a shared utility with many dependents.
- There are no focused tests for the affected area.

## Required Output Fields

- Changed files or symbols.
- Minimal tests and why each is included.
- Broader tests and why each is included.
- Tests missing or uncertain.
- Whether full suite is recommended and why.
