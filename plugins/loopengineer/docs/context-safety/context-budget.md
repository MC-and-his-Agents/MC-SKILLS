# Context Budget Profiles

Context budgets define the maximum estimated size for message surfaces that can
otherwise grow until they become recovery state. The default budget file is
`schemas/v1/context-budget.default.json`.

## Profiles

| Profile | Surface | Default budget |
| --- | --- | --- |
| `confirmation` | Short acknowledgement or decision confirmation | 120 tokens |
| `locator` | Compact pointer to an artifact, command, source, or state carrier | 240 tokens |
| `cross_thread` | Message sent between threads or workstreams | 800 tokens |
| `initial_prompt` | Initial task prompt for a new loop | 2400 tokens |
| `heartbeat_prompt` | Recurring prompt that resumes an existing loop | 900 tokens |
| `handoff_prompt` | Prompt that transfers ownership to a fresh thread or agent | 1600 tokens |

## Estimation

Version 1 uses `deterministic_approx_v1`:

```text
estimated_tokens =
  ceil(character_count / charsPerToken)
  + line_count * lineOverheadTokens
  + code_fence_count * codeFenceOverheadTokens
```

The default constants are:

- `charsPerToken`: 4
- `lineOverheadTokens`: 1
- `codeFenceOverheadTokens`: 8

This is intentionally approximate. The guard must fail closed when a budget file
or profile cannot be classified.

## Thresholds

Each profile has:

- `budgetTokens`: hard admission limit for the selected surface.
- `warnAtTokens`: early warning threshold used before the hard limit.
- `overflowAction`: the expected action when content exceeds `budgetTokens`.

Allowed overflow actions are:

- `write_artifact_send_locator`
- `rotate_thread`

`write_artifact_send_locator` means the large body is written to an artifact and
the outgoing message carries only locator information. `rotate_thread` means a
fresh thread should be prepared before more context is added.
