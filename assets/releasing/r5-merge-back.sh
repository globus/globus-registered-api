#!/usr/bin/env bash

set -e

# Push a new branch to the repo.
# If merge conflicts exist, the 'merge-back' branch is where the conflicts can be resolved.
git fetch origin
git push origin refs/remotes/origin/releases:refs/heads/merge-back

# Create the merge-back PR.
export PR_BODY="$(mktemp)"
echo '
> [!NOTE]
>
> Merge with the "Create a merge commit" strategy!
' > "${PR_BODY}"
gh pr create \
    --title 'Merge back to main' \
    --body-file "${PR_BODY}" \
    --base 'main' \
    --head 'merge-back' \
    --assignee '@me' \
    --label 'no-news-is-good-news'
