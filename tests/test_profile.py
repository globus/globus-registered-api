# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from globus_sdk import ClientApp
from globus_sdk import UserApp

from globus_registered_api.cli import GLOBUS_PROFILE_ENV_VAR
from globus_registered_api.cli import ProfileAwareJSONTokenStorage
from globus_registered_api.cli import _create_globus_app
from globus_registered_api.cli import _get_profile
from globus_registered_api.cli import _resolve_namespace
from globus_registered_api.cli import cli


@pytest.mark.parametrize(
    "profile, environment, expected",
    [
        pytest.param(None, "production", "DEFAULT", id="no-profile"),
        pytest.param("", "production", "DEFAULT", id="empty-profile"),
        pytest.param(
            "work", "production", "userprofile/production/work", id="with-profile"
        ),
        pytest.param(
            "dev", "sandbox", "userprofile/sandbox/dev", id="with-environment"
        ),
    ],
)
def test_resolve_namespace(monkeypatch, profile, environment, expected):
    # Arrange
    if profile is None:
        monkeypatch.delenv(GLOBUS_PROFILE_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(GLOBUS_PROFILE_ENV_VAR, profile)

    # Act
    result = _resolve_namespace(environment)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "profile, expected",
    [
        pytest.param(None, None, id="no-profile"),
        pytest.param("work", "work", id="with-profile"),
    ],
)
def test_get_profile(monkeypatch, profile, expected):
    # Arrange
    if profile is None:
        monkeypatch.delenv(GLOBUS_PROFILE_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(GLOBUS_PROFILE_ENV_VAR, profile)

    # Act
    result = _get_profile()

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "profile, expected_namespace",
    [
        pytest.param(None, "DEFAULT", id="no-profile"),
        pytest.param("work", "userprofile/production/work", id="with-profile"),
    ],
)
@patch("globus_registered_api.cli.JSONTokenStorage.for_globus_app")
def test_profile_aware_storage_namespace(
    mock_for_globus_app, monkeypatch, profile, expected_namespace
):
    # Arrange
    if profile is None:
        monkeypatch.delenv(GLOBUS_PROFILE_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(GLOBUS_PROFILE_ENV_VAR, profile)
    mock_config = MagicMock()
    mock_config.environment = "production"

    # Act
    ProfileAwareJSONTokenStorage.for_globus_app(
        app_name="test-app",
        config=mock_config,
        client_id="test-client-id",
        namespace="ignored",
    )

    # Assert
    mock_for_globus_app.assert_called_once_with(
        app_name="test-app",
        config=mock_config,
        client_id="test-client-id",
        namespace=expected_namespace,
    )


def test_user_app_uses_profile_aware_storage(monkeypatch):
    # Arrange
    monkeypatch.delenv("GLOBUS_REGISTERED_API_CLIENT_ID", raising=False)
    monkeypatch.delenv("GLOBUS_REGISTERED_API_CLIENT_SECRET", raising=False)

    # Act
    app = _create_globus_app()

    # Assert
    assert isinstance(app, UserApp)
    assert app.config.token_storage is ProfileAwareJSONTokenStorage


def test_client_app_ignores_profile(monkeypatch, mock_client_env):
    # Arrange
    monkeypatch.setenv(GLOBUS_PROFILE_ENV_VAR, "work")

    # Act
    app = _create_globus_app()

    # Assert
    assert isinstance(app, ClientApp)
    assert app.config.token_storage is not ProfileAwareJSONTokenStorage


@pytest.mark.parametrize(
    "profile, format, expected_output, check_profile_absent",
    [
        pytest.param(None, "text", "testuser", True, id="text-no-profile"),
        pytest.param(
            "work", "text", "testuser (profile: work)", False, id="text-with-profile"
        ),
        pytest.param(
            None, "json", '"preferred_username": "testuser"', True, id="json-no-profile"
        ),
        pytest.param(
            "work", "json", '"profile": "work"', False, id="json-with-profile"
        ),
    ],
)
def test_whoami_with_profile(
    cli_runner,
    monkeypatch,
    mock_auth_client,
    profile,
    format,
    expected_output,
    check_profile_absent,
):
    # Arrange
    if profile is None:
        monkeypatch.delenv(GLOBUS_PROFILE_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(GLOBUS_PROFILE_ENV_VAR, profile)

    # Act
    args = ["whoami"] if format == "text" else ["whoami", "--format", "json"]
    result = cli_runner.invoke(cli, args)

    # Assert
    assert result.exit_code == 0
    assert expected_output in result.output
    if check_profile_absent:
        assert "profile" not in result.output


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
    result = cli_runner.invoke(cli, ["logout"])

    # Assert
    assert result.exit_code == 0
    assert expected_message in result.output
