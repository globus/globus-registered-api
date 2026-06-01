# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import re
import typing as t
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import globus_sdk.transport
import pytest
import responses

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api import config as config_module
from globus_registered_api import manifest as manifest_module
from globus_registered_api.repositories.clients import GlobusClientRepository


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
    new_path = tmp_path / ".globus_registered_api" / "config.json"
    monkeypatch.setattr(config_module, "_CONFIG_PATH", new_path)

    yield new_path


@pytest.fixture(autouse=True)
def manifest_path(monkeypatch, tmp_path):
    new_path = tmp_path / ".globus_registered_api" / "manifest.json"
    monkeypatch.setattr(manifest_module, "_MANIFEST_PATH", new_path)
    yield new_path


@pytest.fixture(autouse=True)
def mock_auth_client(monkeypatch_client):
    """Fixture that patches create_auth_client and returns a configured MagicMock."""
    client = MagicMock()

    # Set up a default userinfo response.
    resp = {
        "preferred_username": "testuser",
        "email": "test@example.com",
        "sub": "00000000-0000-0000-0000-000000000000",
    }
    client.userinfo.return_value = MockResponse(resp)

    return monkeypatch_client("auth", client)


@pytest.fixture(autouse=True)
def mock_groups_client(monkeypatch_client):
    """Fixture that patches create_groups_client and returns a configured MagicMock."""
    return monkeypatch_client("groups", MagicMock())


@pytest.fixture(autouse=True)
def mock_search_client(monkeypatch_client):
    """Fixture that patches create_search_client and returns a configured MagicMock."""
    return monkeypatch_client("search", MagicMock())


@pytest.fixture(autouse=True)
def mock_flows_client(monkeypatch_client):
    """
    Fixture that patches ExtendedFlowsClient with a pre-initialized instance.

    Note:
        Unlike other clients, flows is only patched to prevent GlobusApp-binding.
        Calls will be made against the real api domains (but intercepted by responses).
    """

    retry_config = globus_sdk.transport.RetryConfig(max_retries=0)
    client = ExtendedFlowsClient(retry_config=retry_config)

    return monkeypatch_client("flows", client)


@pytest.fixture
def monkeypatch_client(monkeypatch):
    def _monkeypatch_client(client_name, client):
        globus = GlobusClientRepository.instance()
        cache = globus._client_cache[globus.cache_key]
        monkeypatch.setitem(cache, client_name, client)
        return client

    return _monkeypatch_client


@pytest.fixture
def subscription_id():
    """Standard subscription ID for testing."""
    return "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"


@pytest.fixture
def subscription_option(subscription_id):
    """CLI option for subscription ID."""
    return ["--subscription-id", subscription_id]
