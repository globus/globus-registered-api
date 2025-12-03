# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: MIT
from unittest.mock import MagicMock, patch
import uuid

import pytest

import globus_registered_api.cli


class MockResponse:
      def __init__(self, data):
          self.data = data

      def __getitem__(self, key):
          return self.data[key]


@patch("globus_registered_api.cli._create_auth_client", autospec=True)
def test_whoami_with_user_app(mock_auth_client, cli_runner):
    # Arrange
    mock_auth = MagicMock()
    mock_auth.userinfo.return_value = MockResponse({"preferred_username": "testuser", "email": "testuser@example.com"})
    mock_auth_client.return_value = mock_auth

    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["whoami"])

    # Assert
    assert result.exit_code == 0
    assert "testuser" in result.output

    # Act (json format)
    result_json = cli_runner.invoke(globus_registered_api.cli.cli, ["whoami", "--format", "json"])

    # Assert
    assert result_json.exit_code == 0
    assert '"preferred_username": "testuser"' in result_json.output


@patch("globus_registered_api.cli._create_auth_client", autospec=True)
def test_whoami_with_client_app(mock_client_env, cli_runner):
    # Arrange
    mock_auth = MagicMock()
    client_id = str(uuid.uuid4())
    mock_auth.userinfo.return_value = MockResponse({"preferred_username": f"{client_id}@clients.auth.globus.org", "email": None})
    mock_client_env.return_value = mock_auth

    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["whoami"])

    # Assert
    assert result.exit_code == 0
    assert client_id in result.output

    # Act (json format)
    result_json = cli_runner.invoke(globus_registered_api.cli.cli, ["whoami", "--format", "json"])

    # Assert
    assert result_json.exit_code == 0
    assert f'"preferred_username": "{client_id}@clients.auth.globus.org"' in result_json.output
