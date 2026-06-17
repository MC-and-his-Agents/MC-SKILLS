# Automatic Release Workflow

Issue: #100

The automatic release workflow is the default release path after release
materials land on `main`. It creates a public Git tag and a draft GitHub Release
only after the same fail-closed release plan used by the manual workflow passes.

## Trigger

The workflow runs on `push` to `main` when release-relevant files change:

- `VERSION`
- `CHANGELOG.md`
- `metadata/loopengineer.json`
- `.codex-plugin/plugin.json`
- `docs/releases/v*.md`

The release tag is derived from `VERSION` as `vX.Y.Z`.

## Automated

- Run the release plan in automatic mode.
- Run `scripts/check_release_readiness.py` through the release plan script.
- Confirm the derived tag matches `VERSION` and readiness output.
- Confirm the target commit matches `origin/main`.
- Stop before creating artifacts when readiness fails.
- Stop without overwriting when the tag or GitHub Release already exists.
- Create a public Git tag and draft GitHub Release only when the plan is
  `create`.
- Upload `release-evidence.json` and generated release notes.

## Manual Fallback

The manual workflow remains the break-glass path for release recovery and
explicitly reviewed releases. Use it when:

- the automatic workflow failed because of a transient GitHub or authentication
  issue;
- a release needs an explicit target commit review;
- a draft release must be recreated after a failed automatic attempt;
- a maintainer needs to inspect the generated evidence before publishing.

## Still Manual

- Choosing whether a draft GitHub Release should become public.
- Publishing packages, which remains out of scope.
- Running any scheduler, watcher, MCP mutation, merge, or closeout automation.

## Fail-Closed Conditions

- Readiness status is not `pass`.
- Derived tag does not match the checked product version.
- Target commit differs from `origin/main`.
- Tag already exists.
- GitHub Release already exists.
- GitHub Release existence cannot be determined.

The workflow records release evidence with version, tag, target commit, main
commit, release mode, draft setting, readiness checks, release URL when created,
workflow run URL, and conclusion.
