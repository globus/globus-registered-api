
Development
-----------

*   Added a `Justfile` with basic developer assistance commands:

    .. code-block::

        > just
        Available recipes:
            clean   # Delete known build artifacts.
            docs    # Rebuild the project's documentation locally (at ./`build`).
            help    # Print this help message.
            install # Install a development virtual environment (at `./.venv`).
            test    # Run the full test suite locally.
