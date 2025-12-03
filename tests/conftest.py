# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import pytest
from click.testing import CliRunner


@pytest.fixture
def mock_client_env(monkeypatch):
    monkeypatch.setenv("GLOBUS_REGISTERED_API_CLIENT_ID", "test-id")
    monkeypatch.setenv("GLOBUS_REGISTERED_API_CLIENT_SECRET", "test-secret")


@pytest.fixture
def cli_runner() -> t.Generator[CliRunner, None, None]:
    return CliRunner()
