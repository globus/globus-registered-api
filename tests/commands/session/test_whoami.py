# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import uuid

import globus_registered_api.cli


class MockResponse:
    def __init__(self, data) -> None:
        self.data = data

    def __getitem__(self, key):
        return self.data[key]


def test_whoami_with_user_app(mock_auth_client, cli_runner):
    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["session", "whoami"])

    # Assert
    assert result.exit_code == 0
    assert "testuser" in result.output

    # Act (json format)
    result_json = cli_runner.invoke(
        globus_registered_api.cli.cli, ["session", "whoami", "--format", "json"]
    )

    # Assert
    assert result_json.exit_code == 0
    assert '"preferred_username": "testuser"' in result_json.output


def test_whoami_with_client_app(mock_auth_client, cli_runner):
    # Arrange
    client_id = str(uuid.uuid4())
    mock_auth_client.userinfo.return_value = MockResponse(
        {"preferred_username": f"{client_id}@clients.auth.globus.org", "email": None}
    )

    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["session", "whoami"])

    # Assert
    assert result.exit_code == 0
    assert client_id in result.output

    # Act (json format)
    result_json = cli_runner.invoke(
        globus_registered_api.cli.cli, ["session", "whoami", "--format", "json"]
    )

    # Assert
    assert result_json.exit_code == 0
    assert (
        f'"preferred_username": "{client_id}@clients.auth.globus.org"'
        in result_json.output
    )
