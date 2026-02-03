

Dependency Installation
=======================

These steps will help you set up a development environment for repository
in which you can interactively write and test changes.

1.  Clone the repository.

    .. code-block::

        git clone https://github.com/globusonline/globus-registered-api.git && cd globus-registered-api

2.  Install dependencies in a local virtualenv (found at `./.venv`) for development.

    .. code-block::

        just install

    .. note::

        This repository uses a ``justfile`` for convenient development commands in place
        of a traditional ``Makefile``.

        To learn more about ``just``, visit https://just.systems/man/en/.
