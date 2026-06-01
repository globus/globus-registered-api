# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

from globus_sdk import GlobusAPIError

from globus_registered_api.cli import _handle_globus_api_error
from globus_registered_api.errors import GRAArgumentError
from globus_registered_api.errors import GRACommandLineError


def _make_api_error(code: str) -> GlobusAPIError:
    """Create a GlobusAPIError with a specific error code."""
    err = MagicMock(spec=GlobusAPIError)
    err.code = code
    err.message = "Something is very wrong here."
    # Make it a proper exception so it can be raised
    err.__class__ = GlobusAPIError
    err.raw_json = {"code": code, "message": "Something is very wrong here."}
    return err


def test_handle_auth_error_exits_with_message(capsys):
    err = _make_api_error("AUTHENTICATION_ERROR")

    _handle_globus_api_error(err)
    captured = capsys.readouterr()

    assert "Authentication Error" in captured.err
    assert "globus-registered-api logout" in captured.err
    assert "globus-registered-api whoami" in captured.err


def test_handle_non_auth_error_reraises(capsys):
    err = _make_api_error("NOT_FOUND")

    _handle_globus_api_error(err)

    captured = capsys.readouterr()
    assert err.code in captured.err
    assert err.message in captured.err


def test_handle_gra_commandline_error(capsys):
    error = GRACommandLineError("my error", "my resolution")

    error.click_echo()

    captured = capsys.readouterr()
    assert "Error: my error" in captured.err
    assert "Resolution: my resolution" in captured.err


def test_handle_gra_argument_error(capsys):
    error = GRAArgumentError("my error", ["b", "a"])

    error.click_echo()

    captured = capsys.readouterr()
    assert "Error: my error" in captured.err
    assert "Allowed Values: a, b" in captured.err
