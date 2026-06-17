# No Inline Large Artifacts Policy

## Covers

- Issue: #7
- Scope: context safety documentation only

## Policy

Agent loop messages must not inline large artifacts. Large artifacts must be
written to files or durable external records, then referenced by compact
locators.

This keeps thread history usable for coordination instead of turning it into a
state database.

## Must Not Inline

Do not paste full contents of:

- reports;
- state tables;
- logs;
- diffs;
- retired or old thread history;
- large review outputs;
- large tool outputs;
- large generated artifacts.

## Allowed Inline Content

Messages may inline only the smallest information needed for the next owner to
act:

- artifact path or URL;
- report id, run id, head sha, or issue/PR id;
- short conclusion;
- concise summary;
- blocker or risk classification;
- next owner;
- next action;
- validation command and result.

Inline summaries should explain what matters, not reproduce the artifact.

## Over-Budget Handling

If content exceeds the selected context budget or is likely to make later
recovery depend on chat history:

1. write the complete artifact to an appropriate file or external record;
2. send only the locator and a short conclusion;
3. include enough metadata to verify freshness, such as head sha, run id, path,
   or timestamp;
4. rotate or hand off the thread when the current context is already polluted by
   large payloads.

## Examples

Preferred locator message:

```text
report_path: reports/context-guard/2026-06-15T090000Z.json
head_sha: abc1234
conclusion: fail, prompt exceeds worker_lite budget
next_action: replace full log with artifact locator before retrying admission
```

Avoid:

```text
Here is the complete log, diff, report, and previous thread transcript:
...
```

## Non-Goals

This policy does not implement validation scripts, schemas, hooks, or skill
refactors. Deterministic enforcement belongs to later context guard and schema
work.
