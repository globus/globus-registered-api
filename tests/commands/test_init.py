# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

import responses

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.openapi.loader import load_openapi_spec


def test_init_errors_if_config_exists(gra, config):
    config.commit()

    result = gra(["init"])

    assert result.exit_code != 0
    assert "Cannot re-initialize" in result.output
    assert "gra manage" in result.output


def test_init_gives_the_caller_owner_permissions(gra, prompt_patcher, mock_auth_client):
    user_id = mock_auth_client.userinfo()["sub"]

    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_input("confirmation", False)  # No I don't have an OpenAPI spec.
    prompt_patcher.add_input("click_prompt", "Test Service")
    prompt_patcher.add_input("click_prompt", "https://api.testservice.com")

    gra(["init"], catch_exceptions=False)

    expected = RoleConfig(type="identity", id=UUID(user_id), access_level="owner")
    assert RegisteredAPIConfig.load().roles == [expected]


def test_init_service_without_openapi_spec(gra, prompt_patcher):
    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_input("confirmation", False)  # No I don't have an OpenAPI spec.
    prompt_patcher.add_input("click_prompt", "Test Service")
    prompt_patcher.add_input("click_prompt", "https://api.testservice.com")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized repository!" in result.output

    RegisteredAPIConfig.load()


def test_init_service_with_local_openapi_spec(gra, prompt_patcher, spec_path):
    local_spec_path = str(spec_path("minimal.json"))

    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_input("confirmation", True)  # Yes, I have an OpenAPI spec.
    prompt_patcher.add_input("prompt_toolkit_prompt", local_spec_path)
    prompt_patcher.add_input("confirmation", True)  # Use the server as base url.

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized repository!" in result.output

    specification = load_openapi_spec(local_spec_path)
    config = RegisteredAPIConfig.load()
    assert config.core.specification == local_spec_path
    assert config.core.base_url == specification.servers[0].url


def test_init_service_with_remote_openapi_spec(gra, prompt_patcher):
    remote_spec_url = "https://random-domain.com/openapi.json"
    specification = {
        "openapi": "3.1.0",
        "info": {"title": "Remote API", "version": "1.0.0"},
    }
    responses.get(remote_spec_url, json=specification)

    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_input("confirmation", True)  # Yes, I have an OpenAPI spec.
    prompt_patcher.add_input("prompt_toolkit_prompt", remote_spec_url)
    prompt_patcher.add_input("click_prompt", "https://api.remote-service.com")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized repository!" in result.output

    config = RegisteredAPIConfig.load()
    assert config.core.specification == remote_spec_url
    assert config.core.base_url == "https://api.remote-service.com"


def test_init_service_with_multiple_servers(gra, prompt_patcher):
    remote_spec_url = "https://random-domain.com/openapi.json"
    specification = {
        "openapi": "3.1.0",
        "info": {"title": "Remote API", "version": "1.0.0"},
        "servers": [
            {"url": "https://api.server1.com"},
            {"url": "https://api.server2.com"},
        ],
    }
    responses.get(remote_spec_url, json=specification)

    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_input("confirmation", True)  # Yes, I have an OpenAPI Spec.
    prompt_patcher.add_input("prompt_toolkit_prompt", remote_spec_url)
    prompt_patcher.add_input("confirmation", True)  # Yes, use of the servers.
    prompt_patcher.add_input("selection", "https://api.server2.com")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized repository!" in result.output

    config = RegisteredAPIConfig.load()
    assert config.core.specification == remote_spec_url
    assert config.core.base_url == "https://api.server2.com"
