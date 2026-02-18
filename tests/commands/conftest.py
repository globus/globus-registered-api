# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import functools
import typing as t

import pytest
from click.testing import CliRunner

from globus_registered_api.cli import cli as root_gra_command


@pytest.fixture
def gra() -> t.Iterator[t.Callable[..., t.Any]]:
    """
    Factory fixture that provides a function to invoke the CLI with given arguments.

    Usage:
        def test_something(invoke_gra):
            result = gra(["some", "args"])
            result2 = gra("some other args")
    """
    runner = CliRunner()
    yield functools.partial(runner.invoke, root_gra_command)
