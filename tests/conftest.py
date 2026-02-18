# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import functools
import re
import typing as t
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import responses

import globus_registered_api.clients
from globus_registered_api import ExtendedFlowsClient


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
def mock_auth_client(monkeypatch):
    """
    Fixture that patches _create_auth_client and returns a configured mock.

    Usage:
        def test_something(mock_auth_client):
            # _create_auth_client is already patched and returns a mock
            # with userinfo() returning {"preferred_username": "testuser", ...}
    """
    client = MagicMock()
    client.userinfo.return_value = MockResponse(
        {"preferred_username": "testuser", "email": "test@example.com"}
    )
    monkeypatch.setattr(
        globus_registered_api.clients,
        "AuthClient",
        lambda *args, **kwargs: client,
    )
    return client


@pytest.fixture(autouse=True)
def mock_flows_client(monkeypatch):
    """
    Fixture that patches ExtendedFlowsClient and returns a mock instance.
    """
    client = ExtendedFlowsClient()
    monkeypatch.setattr(
        globus_registered_api.clients,
        "ExtendedFlowsClient",
        lambda *args, **kwargs: client,
    )
    return client


@pytest.fixture
def crud_patcher() -> RegisteredAPICRUDPatcher:
    """
    Fixture to aid in patching the Registered API CRUD endpoints in the flows service.

    Usage:
    def test_something(crud_patcher):
        crud_patcher.patch_list(json={"registered_apis": []})
        crud_patcher.patch_show(json={"id": "1234", "name": "Test API"})
        ....

    """
    return RegisteredAPICRUDPatcher()


_LIST_URL = re.compile(r"https://.*flows.*\.globus\.org/registered_apis")
_SHOW_URL = re.compile(r"https://.*flows.*\.globus\.org/registered_apis/[a-f0-9-]+")
_UPDATE_URL = re.compile(r"https://.*flows.*\.globus\.org/registered_apis/[a-f0-9-]+")
_CREATE_URL = re.compile(r"https://.*flows.*\.globus\.org/registered_apis$")


class RegisteredAPICRUDPatcher:
    def __init__(self) -> None:
        self.patch_list = functools.partial(responses.add, responses.GET, _LIST_URL)
        self.patch_show = functools.partial(responses.add, responses.GET, _SHOW_URL)
        self.patch_update = functools.partial(
            responses.add, responses.PATCH, _UPDATE_URL
        )
        self.patch_create = functools.partial(
            responses.add, responses.POST, _CREATE_URL
        )
