# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock
from unittest.mock import patch

import globus_registered_api.cli


@patch("globus_registered_api.cli._create_globus_app")
def test_logout(mock_create_app, cli_runner):
    # Arrange
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # Act
    result = cli_runner.invoke(globus_registered_api.cli.cli, ["logout"])

    # Assert
    assert result.exit_code == 0
    mock_app.logout.assert_called_once()
    assert "Logged out successfully." in result.output
