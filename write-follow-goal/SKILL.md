---
name: write-follow-goal
description: Draft and refine Codex /goal instructions that follow OpenAI's "Follow a goal" guidance. Use when the user asks to create, set, design, rewrite, validate, or improve a durable long-running Codex goal; when the request mentions /goal, follow-goals, long-running work, stopping conditions, validation loops, checkpoints, or persistent objectives; or when a normal task should be converted into a verifiable Codex goal statement. Default to the user's language, and use Chinese when the user's language is unclear or mixed.
---

# Write Follow Goal

## Overview

Create a concise, executable `/goal` instruction from the user's context. Prefer one durable objective, a verifiable stopping condition, explicit scope boundaries, and a practical validation loop.

Read `references/follow-goal-spec.md` when the user asks for official compliance, asks to validate an existing goal, or the goal is high stakes, ambiguous, or long-running enough that exact structure matters.

## Language Policy

Reply in the user's language by default. If the user writes in Chinese or the language is mixed or unclear, use Chinese. Keep commands, file names, code identifiers, and quoted goal text unchanged when they are already in the right form.

## Workflow

1. Extract the durable objective from the user's context.
2. Identify the verifiable end state before drafting.
3. Define what Codex must read first: files, docs, issues, logs, plans, screenshots, or URLs.
4. Set boundaries: what to change, what to preserve, and what requires asking the user.
5. Define validation: commands to run, artifacts to inspect, screenshots to compare, tests to pass, scores to reach, or documents to update.
6. Add checkpoint behavior: work in scoped checkpoints, keep a short progress log, and re-run validation after meaningful changes.
7. Add pause or block conditions: missing credentials, destructive operations, product decisions, policy calls, unclear requirements, or repeated validation failure.
8. Return the final `/goal` plus a short self-check when useful.
9. Keep the response language aligned with the user's language, with Chinese as the default fallback.

## Draft Shape

Use this structure unless the user's environment needs a shorter command:

```text
/goal Complete [objective] without stopping until [verifiable end state].

First read [required context].
Stay within [scope boundaries].
Work in checkpoints: [checkpoint cadence or milestones].
Validate progress with [commands, artifacts, or review steps].
Keep a short progress log with current checkpoint, what was verified, what remains, and blockers.
Pause only if [block conditions].
Stop when [done condition] is true and [final verification] passes.
```

## Quality Bar

A good goal must be:

- Bigger than a single normal prompt but smaller than an open-ended backlog.
- Centered on one objective, not a bundle of unrelated requests.
- Clear about what "done" means before Codex starts.
- Concrete about validation artifacts or commands.
- Explicit about boundaries and non-goals.
- Specific enough that another Codex instance could continue after compaction.

Avoid vague stopping conditions such as "when it looks good", "until everything is done", or "until no issues remain" unless they are paired with concrete checks.

## Conversation Handling

Ask at most one concise question only when a missing detail changes the goal materially and cannot be inferred safely. Otherwise, make conservative assumptions and state them in the goal.

When the user says "set the goal" or asks you to create an active goal, create the goal using the available goal tool if present. When they only ask for wording, provide the `/goal` text without activating it.

## Validation Pass

Before finalizing, check that the goal answers:

- Objective: What exactly should Codex accomplish?
- End state: What verifiable condition lets Codex stop?
- Context: What must Codex read first?
- Boundaries: What should Codex avoid changing?
- Loop: How should Codex prove progress?
- Checkpoints: How should Codex report compact status?
- Blocks: What should cause Codex to pause and ask?

If any answer is missing, revise the goal before returning it.
