# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0


def test_logout(patched_globusapp, gra):
    # Act
    result = gra(["session", "logout"], catch_exceptions=False)

    # Assert
    patched_globusapp.logout.assert_called_once()
    assert "Logged out successfully." in result.output


def test_logout_with_profile(patched_globusapp, gra, monkeypatch):
    # Arrange
    monkeypatch.setenv("GLOBUS_PROFILE", "work")

    # Act
    result = gra(["session", "logout"], catch_exceptions=False)

    # Assert
    assert result.exit_code == 0
    patched_globusapp.logout.assert_called_once()
    assert "Logged out successfully from profile 'work'." in result.output
