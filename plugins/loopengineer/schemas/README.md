# Schemas

This directory is the future home for LoopEngineer schemas.

Current status:

- v1 context budget schema and default budget live under `schemas/v1/`;
- v1 report, dispatch table, and scheduler pool schemas live under `schemas/v1/`;
- v1 channel state, waiting queue, channel event, and watcher decision schemas live
  under `schemas/v1/`;
- v1 watcher inbox schema lives under `schemas/v1/` as a compact watcher-first
  summary surface;
- v1 subagent assignment schema and subagent report provider context support
  `worker_lite` provider consumption checks;
- future schemas should live under major-versioned directories such as `schemas/v1/`;
- schema examples and invalid examples should land with the schema that requires them.

Related issues include #5, #18, #19, #26, #87, #90, #93, and #94.
