# CodeGraph Tool Policy

Use this shared policy from every CodeGraph Intelligence skill. Skill-specific files should describe task workflow; this file owns common tool selection, fallback and unavailable handling.

## Availability Check

Start graph-backed work with `codegraph_status` or `codegraph status .`.

- If no index exists, ask the user to run `codegraph init -i` or run it only when the user explicitly wants initialization.
- If the index is stale, prefer `codegraph sync` before relying on graph results.
- After editing files, wait briefly before re-querying because the watcher syncs with a short debounce.

## MCP First

Prefer MCP tools when they are available:

- `codegraph_search`: find symbols by name, route, module or short code term.
- `codegraph_context`: build focused task context without broad file reads.
- `codegraph_explore`: survey unfamiliar modules or broad areas after search finds concrete anchors.
- `codegraph_node`: inspect one symbol's location, signature, export state or source.
- `codegraph_callers` / `codegraph_callees`: trace direct relationships.
- `codegraph_impact`: estimate broader change radius.
- `codegraph_files`: inspect indexed file structure.

## Explore Discipline

Use `codegraph_explore` only for broad or unfamiliar areas. Do not use it for narrow symbol lookups. Anchor explore queries to symbols, file names or short code terms found by `codegraph_search`; avoid natural-language-only explore queries.

## CLI Fallback

Use CLI fallback only when MCP tools are unavailable:

- `codegraph query` for symbol search.
- `codegraph context` for focused context.
- `codegraph files` for indexed structure.
- `codegraph affected` for changed-file-to-test mapping.
- `codegraph status` and `codegraph sync` for index health.

When parsing CLI output, state that results may be less structured than MCP output.

## No Graph Available

If neither MCP nor CLI is available, proceed only with conservative local inspection. State that graph-backed analysis could not be performed, avoid high-confidence deletion or breaking-change claims, and keep findings explicitly uncertain.
