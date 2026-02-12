Dependency Installation
=======================

These steps will help you set up a development environment for repository
in which you can interactively write and test changes.

1.  Clone the repository.

    .. code-block::

        git clone https://github.com/globus/globus-registered-api.git && cd globus-registered-api

2.  Install dependencies in a local virtualenv (at ``./.venv``) and pre-commit hooks.

    .. code-block::

        just install

    This will create a local virtualenv, install dependencies, and configure
    pre-commit hooks to run automatically before each commit.

    .. note::

        This repository uses a ``justfile`` for convenient development commands in place
        of a traditional ``Makefile``.

        To learn more about ``just``, visit https://just.systems/man/en/.

    To manually run all pre-commit checks:

    .. code-block::

        just lint
