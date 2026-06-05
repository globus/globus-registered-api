#!/usr/bin/env bash

set -e

require_exit='0'

required_commands=(
    gh
    pandoc
    poetry
    scriv
)

for required_command in "${required_commands[@]}"; do
    if ! command -v "${required_command}" 1>/dev/null 2>/dev/null; then
        echo "${required_command} must be installed."
        require_exit='1'
    fi
done

# Require that `main` is already checked out.
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "${current_branch}" != 'main' ]; then
    echo "You must be on the 'main' branch."
    require_exit='1'
fi

# Require a single argument, representing the new version.
if [ "$1" == '' ]; then
    echo
    echo "USAGE: $0 {VERSION}"
    require_exit='1'
fi

if [ "${require_exit}" -eq '1' ]; then
    exit 1
fi

# Set the new version.
export VERSION="$1"
export BRANCH="release/${VERSION}"

# Pull the latest changes.
git pull

# Bump the metadata.
git checkout -b "release/${VERSION}"
poetry version "${VERSION}"
scriv collect

# Commit the changes
git add changelog.d/ CHANGELOG.rst pyproject.toml
git commit -m 'Update project metadata'
