
# Print this help message.
help:
    @just --list

# Install a development virtual environment (at `./.venv`).
install:
    if [ ! -d .venv ]; then python -m venv .venv; fi
    .venv/bin/pip install --upgrade pip setuptools wheel
    .venv/bin/pip install -e.
    .venv/bin/pip install -r requirements/test/requirements.txt

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
