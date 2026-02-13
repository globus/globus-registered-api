# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import globus_registered_api.cli
from globus_registered_api.cli import GLOBUS_PROFILE_ENV_VAR


@patch("globus_registered_api.cli._create_globus_app")
def test_logout(mock_create_app, cli_runner):
    # Arrange
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["session", "logout"])

    # Assert
    assert result.exit_code == 0
    mock_app.logout.assert_called_once()
    assert "Logged out successfully." in result.output


@pytest.mark.parametrize(
    "profile, expected_message",
    [
        pytest.param(None, "Logged out successfully.", id="no-profile"),
        pytest.param(
            "work", "Logged out successfully from profile 'work'.", id="with-profile"
        ),
    ],
)
@patch("globus_registered_api.cli._create_globus_app")
def test_logout_with_profile(
    mock_create_app, cli_runner, monkeypatch, profile, expected_message
):
    # Arrange
    if profile is None:
        monkeypatch.delenv(GLOBUS_PROFILE_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(GLOBUS_PROFILE_ENV_VAR, profile)
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["session", "logout"])

    # Assert
    assert result.exit_code == 0
    assert expected_message in result.output
