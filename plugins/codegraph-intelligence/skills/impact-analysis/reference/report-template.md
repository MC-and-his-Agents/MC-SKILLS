# Impact Analysis Report Template

Use this template for impact-analysis output. Keep the report concise, but do not omit uncertainty.

## Required Sections

### Target

- Symbol, route, module or file being changed.
- Current role: public API, internal helper, route handler, CLI command, data layer, shared utility or unknown.
- Evidence used to identify the target.

### Direct Impact

- Direct callers from `codegraph_callers`.
- Direct callees from `codegraph_callees`.
- Files likely to change.

### Broader Impact

- Indirect callers or dependents from `codegraph_impact`.
- Routes, commands, jobs, UI flows or external integrations affected.
- Public exports or API surfaces involved.

### Tests

- Minimal focused tests.
- Broader regression tests.
- Tests missing or unclear.

### Risk

Use these levels:

- **Low**: private implementation detail, visible callers, narrow test coverage available.
- **Medium**: shared module, multiple callers, partial dynamic behavior or incomplete tests.
- **High**: public API, persisted data, auth/security/payment path, cross-service behavior or broad shared contract.
- **Unknown**: stale graph, ambiguous symbols, missing downstream consumers or insufficient evidence.

### Recommended Order

- Discovery still needed.
- Implementation order.
- Validation order.

### Uncertainty

- What CodeGraph could not prove.
- What was inferred manually.
- What requires user, domain or external system confirmation.
