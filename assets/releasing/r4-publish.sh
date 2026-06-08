#!/usr/bin/env bash

set -e

# Check out the 'releases' branch.
git checkout releases
git pull

export VERSION="$(poetry version --short)"

# Generate the CHANGELOG fragment.
export CHANGELOG_FRAGMENT="$(mktemp)"
scriv print --version "${VERSION}" \
    | pandoc --from rst --to gfm --wrap preserve --shift-heading-level-by 1 \
    > "${CHANGELOG_FRAGMENT}"

# Publish the git artifacts.
git tag "v${VERSION}" --annotate --file="${CHANGELOG_FRAGMENT}"
git push --tags  # This line triggers a CI job that publishes to PyPI.
gh release create "v${VERSION}" \
    --target 'releases' \
    --title "${VERSION}" \
    --notes-from-tag

# Publish the PyPI artifacts.
rm -rf dist/
poetry build --no-plugins
twine check --strict dist/*
twine upload dist/*
