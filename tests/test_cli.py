# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import pytest
from globus_sdk import ClientApp
from globus_sdk import UserApp

from globus_registered_api.cli import _create_globus_app


@pytest.mark.parametrize(
    "env_var, value",
    [
        ("GLOBUS_REGISTERED_API_CLIENT_ID", "test-id"),
        ("GLOBUS_REGISTERED_API_CLIENT_SECRET", "test-secret"),
    ],
)
def test_create_globus_app_without_required_env_vars_failure(
    monkeypatch, env_var, value
):
    # Arrange
    monkeypatch.setenv(env_var, value)

    # Act
    with pytest.raises(ValueError) as excinfo:
        _ = _create_globus_app()

    # Assert
    assert (
        "Both GLOBUS_CLIENT_ID and GLOBUS_CLIENT_SECRET must be set, or neither."
        in str(excinfo.value)
    )


def test_create_globus_app_returns_client_app_when_env_vars_set(
    monkeypatch, mock_client_env
):
    # Act
    app = _create_globus_app()

    # Assert
    assert isinstance(app, ClientApp)


def test_create_globus_app_returns_user_app_when_env_vars_not_set(monkeypatch):
    # Arrange
    monkeypatch.delenv("GLOBUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("GLOBUS_CLIENT_SECRET", raising=False)

    # Act
    app = _create_globus_app()

    # Assert
    assert isinstance(app, UserApp)
