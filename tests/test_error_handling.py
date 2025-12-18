# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import pytest
from globus_sdk import GlobusAPIError

from globus_registered_api.cli import _handle_globus_api_error


def _make_api_error(code: str) -> GlobusAPIError:
    """Create a GlobusAPIError with a specific error code."""
    err = MagicMock(spec=GlobusAPIError)
    err.code = code
    err.message = None
    # Make it a proper exception so it can be raised
    err.__class__ = GlobusAPIError
    return err


def test_handle_auth_error_exits_with_message(capsys):
    err = _make_api_error("AUTHENTICATION_ERROR")

    with pytest.raises(SystemExit) as exc_info:
        _handle_globus_api_error(err)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Authentication Error" in captured.err
    assert "globus-registered-api logout" in captured.err
    assert "globus-registered-api whoami" in captured.err


def test_handle_non_auth_error_reraises():
    err = _make_api_error("NOT_FOUND")

    with pytest.raises(TypeError):
        # TypeError because mock can't be raised, but this proves the
        # function attempted to re-raise rather than handling the error
        _handle_globus_api_error(err)
