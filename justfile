
# Print this help message.
help:
    @just --list

# Install a development virtual environment (at `./.venv`).
install:
    #!/usr/bin/env bash
    if [ ! -d .venv ]; then
        python -m venv .venv
    fi
    source .venv/bin/activate
    poetry install -P ./requirements/test

# Run the full test suite locally.
test:
	tox run -m testsuite

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
