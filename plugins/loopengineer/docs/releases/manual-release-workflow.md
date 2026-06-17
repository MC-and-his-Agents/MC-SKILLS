# Manual Release Workflow

Issue: #65

The manual release workflow is a `workflow_dispatch` fallback entry point for
creating a tag and GitHub Release after release readiness passes. The automatic
release workflow is the default merge-triggered path; this workflow remains the
break-glass path for explicit maintainer review and recovery.

## Automated

- Run `scripts/prepare_manual_release.py`.
- Run `scripts/check_release_readiness.py` through the release plan script.
- Confirm the requested tag matches `VERSION` and readiness output.
- Confirm the target commit matches `origin/main` unless an explicit commit is
  acknowledged in the workflow input.
- Stop before creating artifacts when readiness fails.
- Stop without overwriting when the tag or GitHub Release already exists.
- Create the tag and GitHub Release only when the plan is `create`.
- Upload `release-evidence.json` and generated release notes.

## Manual Inputs

- `release_version`: tag-shaped version such as `v0.1.0`.
- `release_commit`: optional explicit commit SHA.
- `allow_explicit_commit`: must be set when releasing a commit that differs from
  `origin/main`.
- `draft_release`: defaults to true.

## Still Manual

- Choosing when to run the workflow.
- Confirming the release target is intended.
- Reviewing the generated draft release before publishing it.
- Package publication, which remains out of scope.

Use this workflow instead of the automatic path only when a maintainer needs an
explicit target commit, recovery from a failed automatic run, or a manually
reviewed draft release.

## Fail-Closed Conditions

- Readiness status is not `pass`.
- Requested tag does not match the checked product version.
- Target commit differs from `origin/main` without explicit acknowledgement.
- Tag already exists.
- GitHub Release already exists.

The workflow records release evidence with version, tag, target commit, main
commit, readiness checks, release URL when created, and conclusion.
