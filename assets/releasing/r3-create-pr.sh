#!/usr/bin/env bash

set -e

export VERSION="$(poetry version --short)"
export BRANCH="release/${VERSION}"

# Require that `release/$VERSION` branch is already checked out.
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "${current_branch}" != "${BRANCH}" ]; then
    echo "You must be on the '${BRANCH}' branch."
    exit 1
fi

# Generate the CHANGELOG fragment.
export CHANGELOG_FRAGMENT="$(mktemp --suffix '.md')"

echo '
> [!NOTE]
>
> Merge with the "Create a merge commit" strategy!
' > "${CHANGELOG_FRAGMENT}"

scriv print --version "${VERSION}" \
    | pandoc --from rst --to gfm --wrap preserve --shift-heading-level-by 1 \
    >> "${CHANGELOG_FRAGMENT}"

# Create the PR.
git push origin --set-upstream "${BRANCH}"
gh pr create \
    --title "Release ${VERSION}" \
    --body-file "${CHANGELOG_FRAGMENT}" \
    --base 'releases'
