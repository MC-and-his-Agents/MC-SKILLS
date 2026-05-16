# Follow Goal Spec

Use this reference to write or validate `/goal` instructions against OpenAI's Codex "Follow a goal" guidance.

Source: https://developers.openai.com/codex/use-cases/follow-goals

## Core Rule

Use `/goal` when a task needs Codex to keep working across turns toward a verifiable stopping condition.

The starter pattern is:

```text
/goal Complete [objective] without stopping until [verifiable end state].
```

## Good Fit

Use a goal for:

- Long-running coding work with a clear success condition and validation loop.
- Code migrations, large refactors, deployment retry loops, experiments, games, prototypes, and side projects where Codex can keep making scoped progress.
- Long experiments with clear success criteria.

Avoid a goal for a loose list of unrelated work.

## Required Contract

A good goal is bigger than one prompt but smaller than an open-ended backlog. It should define:

- What Codex should achieve.
- What Codex should not change.
- How Codex should validate progress.
- When Codex should stop.

## Setup Loop

1. Name one objective and one stopping condition.
2. Point Codex at the files, docs, issue, logs, or plan it must read first.
3. Define the commands or artifacts that prove progress.
4. Tell Codex to work in checkpoints and keep a short progress log.
5. Inspect status while it runs.
6. Pause, resume, or clear the goal when the run is done, blocked, or changing direction.

## Status Updates

Ask for compact progress reports that name:

- Current checkpoint.
- What was verified.
- What remains.
- Whether Codex is blocked.

If the status becomes vague, tighten the goal: name the next checkpoint, the command or artifact that proves it, and what should cause Codex to pause.

## Examples

Migration:

```text
/goal Migrate this project from [legacy stack or system] to [target stack or system]. Make sure all screens stay exactly the same visually, using playwright interactive to verify the output.
```

Prototype:

```text
/goal Implement PLAN.md, creating tests for each milestone and verifying the output with playwright interactive. [include reference screens as needed]
```

Prompt optimization:

```text
/goal Optimize the prompts in [prompt file or directory] until the eval suite reaches [target score or pass rate]. After each change, run [eval command], inspect the failing cases, and keep the prompt edits minimal and targeted. Stop when the target is met or when further prompt changes would need product or policy guidance.
```
