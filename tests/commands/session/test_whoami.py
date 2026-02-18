# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import uuid

import pytest

from globus_registered_api.cli import GLOBUS_PROFILE_ENV_VAR


class MockResponse:
    def __init__(self, data) -> None:
        self.data = data

    def __getitem__(self, key):
        return self.data[key]


def test_whoami_with_user_app(gra):
    # Act
    result = gra(["session", "whoami"])

    # Assert
    assert result.exit_code == 0
    assert "testuser" in result.output

    # Act (json format)
    result_json = gra(["session", "whoami", "--format", "json"])

    # Assert
    assert result_json.exit_code == 0
    assert '"preferred_username": "testuser"' in result_json.output


def test_whoami_with_client_app(mock_auth_client, gra):
    # Arrange
    client_id = str(uuid.uuid4())
    mock_auth_client.userinfo.return_value = MockResponse(
        {"preferred_username": f"{client_id}@clients.auth.globus.org", "email": None}
    )

    # Act
    result = gra(["session", "whoami"])

    # Assert
    assert result.exit_code == 0
    assert client_id in result.output

    # Act (json format)
    result_json = gra(["session", "whoami", "--format", "json"])

    # Assert
    assert result_json.exit_code == 0
    username = f"{client_id}@clients.auth.globus.org"
    assert f'"preferred_username": "{username}"' in result_json.output


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
    gra,
    monkeypatch,
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
    args = ["session", "whoami"]
    if format == "json":
        args += ["--format", "json"]
    result = gra(args)

    # Assert
    assert result.exit_code == 0
    assert expected_output in result.output
    if check_profile_absent:
        assert "profile" not in result.output
