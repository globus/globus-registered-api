# Print this help message.
help:
    @just --list

# Install a development virtual environment (at `./.venv`) and pre-commit hooks.
install:
    #!/usr/bin/env bash
    if [ ! -d .venv ]; then
        python -m venv .venv
    fi
    .venv/bin/pip install --upgrade pip setuptools wheel
    .venv/bin/pip install -e.
    .venv/bin/pip install -r requirements/test/requirements.txt
    pre-commit install

# Run pre-commit checks on all files.
lint:
    pre-commit run --all-files

# Run the full test suite locally.
test:
    tox run --color=yes

# Type check the project with mypy.
mypy filepath="./src":
    tox -e mypy-py3.12 -- {{filepath}}

# Rebuild the project's documentation locally (at ./`build`).
docs:
    tox -e docs

# Delete known build artifacts.
clean:
    rm -rf .mypy_cache
    rm -rf .pytest_cache
    rm -rf .tox
    rm -rf .venv
    rm -rf build
    rm -f .coverage.*
    find . \( -type d -name __pycache__ -or -name \*.py[oc] \) -delete

# RELEASING 1: Create a new branch and update the project metadata.
r1-prep-release version:
    bash assets/releasing/r1-prep-release.sh "{{version}}"

# RELEASING 2: (OPTIONAL) Amend the CHANGELOG after changes are made.
r2-amend-changelog:
    bash assets/releasing/r2-amend-changelog.sh

# RELEASING 3: Create the release PR.
r3-create-pr:
    bash assets/releasing/r3-create-pr.sh

# RELEASING 4: Publish a git tag and GitHub release.
r4-publish:
    bash assets/releasing/r4-publish.sh

# RELEASING 5: Create the merge-back-to-main PR.
r5-merge-back:
    bash assets/releasing/r5-merge-back.sh
