# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import re
import typing as t
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import responses

import globus_registered_api.clients as src_clients
import globus_registered_api.config
from globus_registered_api import ExtendedFlowsClient


@pytest.fixture(scope="session")
def api_url_patterns():
    return SimpleNamespace(
        LIST=re.compile(r"https://.*flows.*\.globus\.org/registered_apis"),
        SHOW=re.compile(r"https://.*flows.*\.globus\.org/registered_apis/[a-f0-9-]+"),
        UPDATE=re.compile(r"https://.*flows.*\.globus\.org/registered_apis/[a-f0-9-]+"),
        CREATE=re.compile(r"https://.*flows.*\.globus\.org/registered_apis$"),
        DELETE=re.compile(r"https://.*flows.*\.globus\.org/registered_apis/[a-f0-9-]+"),
    )


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
def spec_path():
    """
    Factory fixture that returns the path to a spec file by name.

    Usage:
        def test_something(spec_path):
            path = spec_path("minimal.json")
    """

    def _get_path(filename: str) -> Path:
        return Path(__file__).parent / "files" / "openapi_specs" / filename

    return _get_path


@pytest.fixture
def temp_spec_file(tmp_path):
    """
    Factory fixture that creates a temporary spec file with given content.

    Usage:
        def test_something(temp_spec_file):
            path = temp_spec_file("test.json", '{"invalid": "content"}')
    """

    def _create_file(filename: str, content: str) -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path

    return _create_file


class MockResponse:
    """Mock response object that mimics Globus SDK response behavior."""

    def __init__(self, data: dict) -> None:
        self.data = data

    def __getitem__(self, key: str) -> t.Any:
        return self.data[key]


@pytest.fixture(autouse=True)
def config_path(monkeypatch, tmp_path):
    """
    Fixture that patches the config path to a temporary directory for all tests.

    Ensure that tests don't write to the runners invocation directory.
    """
    new_path = tmp_path / ".globus_registered_api/config.json"
    monkeypatch.setattr(globus_registered_api.config, "_CONFIG_PATH", new_path)

    yield new_path


@pytest.fixture(autouse=True)
def mock_auth_client(monkeypatch):
    """Fixture that patches create_auth_client and returns a configured MagicMock."""
    client = MagicMock()
    monkeypatch.setattr(src_clients, "AuthClient", lambda *_, **__: client)

    # Set up a default userinfo response.
    resp = {
        "preferred_username": "testuser",
        "email": "test@example.com",
        "sub": "00000000-0000-0000-0000-000000000000",
    }
    client.userinfo.return_value = MockResponse(resp)
    return client


@pytest.fixture(autouse=True)
def mock_groups_client(monkeypatch):
    """Fixture that patches create_groups_client and returns a configured MagicMock."""
    client = MagicMock()
    monkeypatch.setattr(src_clients, "GroupsClient", lambda *_, **__: client)
    return client


@pytest.fixture(autouse=True)
def mock_search_client(monkeypatch):
    """Fixture that patches create_search_client and returns a configured MagicMock."""
    client = MagicMock()
    monkeypatch.setattr(src_clients, "SearchClient", lambda *_, **__: client)
    return client


@pytest.fixture(autouse=True)
def mock_flows_client(monkeypatch):
    """
    Fixture that patches ExtendedFlowsClient with a pre-initialized instance.

    Note:
        Unlike other clients, flows is only patched to prevent GlobusApp-binding.
        Calls will be made against the real api domains (but intercepted by responses).
    """
    client = ExtendedFlowsClient()
    monkeypatch.setattr(src_clients, "ExtendedFlowsClient", lambda *_, **__: client)
    return client
