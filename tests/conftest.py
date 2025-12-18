# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import pytest
import responses
from click.testing import CliRunner


@pytest.fixture(autouse=True)
def mocked_responses():
    """
    All tests enable `responses` patching of the `requests` package, replacing
    all HTTP calls.
    """
    responses.start()
    yield
    responses.stop()
    responses.reset()


@pytest.fixture
def mock_client_env(monkeypatch):
    monkeypatch.setenv("GLOBUS_REGISTERED_API_CLIENT_ID", "test-id")
    monkeypatch.setenv("GLOBUS_REGISTERED_API_CLIENT_SECRET", "test-secret")


@pytest.fixture
def cli_runner() -> t.Generator[CliRunner, None, None]:
    return CliRunner()
