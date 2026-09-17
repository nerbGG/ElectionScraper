---
name: pr-description
description: Draft a PR title and description from the current branch's changes vs main, optionally updating an existing PR directly
argument-hint: pr-url
disable-model-invocation: true
---

## Commits vs main
!`git log origin/main..HEAD --oneline`

## Diff vs main
!`git diff origin/main...HEAD`

## Task
Draft a PR title and description with sections: Summary, Known gaps (if any), Test plan.
Match the style already used in this project's PR descriptions — bullet points under each
section, checkboxes for the test plan.

If `$ARGUMENTS` was provided (a PR URL):
- Run `gh pr view $ARGUMENTS --json title,body,url` first to see the PR's current title/description,
  so the draft can extend/correct it rather than clobber unrelated existing content.
- After drafting, update the PR directly with `gh pr edit $ARGUMENTS --body "<drafted description>"`.
- Report the PR URL back once updated.

If `$ARGUMENTS` was not provided, just output the drafted title and description as text for manual
copy-paste — do not attempt to run any `gh pr` command.
