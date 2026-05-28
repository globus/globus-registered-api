# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace
from uuid import UUID
from uuid import uuid4

import pytest

from globus_registered_api.config import GRAConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.repositories import SubscriptionRepository
from globus_registered_api.repositories.clients import GlobusClientRepository
from globus_registered_api.repositories.subscriptions import SubscriptionInfo


@pytest.fixture(autouse=True)
def patch_subscription_repository(monkeypatch):
    repository = SubscriptionRepository.instance()
    globus = GlobusClientRepository.instance()

    active_cache = repository._active_cache
    known_cache = repository._known_cache

    for sub in (SUBS.UChicago, SUBS.Globus, SUBS.Harvard):
        known_cache[sub.id] = sub

    active_cache[globus.cache_key] = [SUBS.UChicago, SUBS.Globus]


SUBS = SimpleNamespace(
    UChicago=SubscriptionInfo(str(uuid4()), "UChicago"),
    Globus=SubscriptionInfo(str(uuid4()), "Globus"),
    Harvard=SubscriptionInfo(str(uuid4()), "Harvard"),
)


def test_init_errors_if_config_exists(gra, config):
    config.commit()

    result = gra(["init"])

    assert result.exit_code != 0
    assert "Error: Config already exists at " in result.output
    assert "gra manage" in result.output


def test_init_service_with_local_openapi_spec(prompt_patcher, gra, openapi_schema):
    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_selection("Set Subscription")
    prompt_patcher.add_selection(f"{SUBS.Globus.name} ({SUBS.Globus.id})")

    prompt_patcher.add_selection("Set OpenAPI Location")
    prompt_patcher.add_input("prompt_toolkit_prompt", "./dummy.json")

    prompt_patcher.add_selections("Set Base URL", "<Enter url manually>")
    prompt_patcher.add_input("click_prompt", "https://api.example.com")

    prompt_patcher.add_selection("<Submit>")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized GRA Repository" in result.output

    stage_config = GRAConfig.load().stages["production"]
    assert stage_config.specification == "./dummy.json"
    assert stage_config.base_url == "https://api.example.com"


def test_init_service_with_remote_openapi_spec(prompt_patcher, gra, openapi_schema):
    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_selection("Set Subscription")
    prompt_patcher.add_selection(f"{SUBS.Globus.name} ({SUBS.Globus.id})")

    prompt_patcher.add_selection("Set OpenAPI Location")
    spec_url = "https://api.remote-service.com/openapi.json"
    prompt_patcher.add_input("prompt_toolkit_prompt", spec_url)

    prompt_patcher.add_selection("Set Base URL")
    prompt_patcher.add_selection("https://api.remote-service.com")

    prompt_patcher.add_selection("<Submit>")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized GRA Repository" in result.output

    stage_config = GRAConfig.load().stages["production"]
    assert stage_config.specification == spec_url
    assert stage_config.base_url == "https://api.remote-service.com"


def test_init_gives_the_caller_owner_permissions(
    prompt_patcher, gra, mock_auth_client, openapi_schema
):
    user_id = mock_auth_client.userinfo()["sub"]

    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_selection("Set Subscription")
    prompt_patcher.add_selection(f"{SUBS.Globus.name} ({SUBS.Globus.id})")

    prompt_patcher.add_selection("Set OpenAPI Location")
    prompt_patcher.add_input("prompt_toolkit_prompt", "./dummy.json")

    prompt_patcher.add_selections("Set Base URL", "<Enter url manually>")
    prompt_patcher.add_input("click_prompt", "https://api.example.com")

    prompt_patcher.add_selection("<Submit>")

    gra(["init"], catch_exceptions=False)

    expected = RoleConfig(type="identity", id=UUID(user_id), access_level="owner")
    assert GRAConfig.load().stages["production"].roles == [expected]


def test_init_service_with_remote_openapi_spec_and_whitespace(
    prompt_patcher, gra, openapi_schema
):
    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_selection("Set Subscription")
    prompt_patcher.add_selection(f"{SUBS.Globus.name} ({SUBS.Globus.id})")

    prompt_patcher.add_selection("Set OpenAPI Location")
    spec_url = "https://api.remote-service.com/openapi.json"
    prompt_patcher.add_input("prompt_toolkit_prompt", f"{spec_url}\n")

    prompt_patcher.add_selection("Set Base URL")
    prompt_patcher.add_selection("https://api.remote-service.com")

    prompt_patcher.add_selection("<Submit>")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized GRA Repository" in result.output

    stage_config = GRAConfig.load().stages["production"]
    assert stage_config.specification == spec_url
    assert stage_config.base_url == "https://api.remote-service.com"


def test_init_service_with_multiple_servers(prompt_patcher, gra, openapi_schema):
    openapi_schema["servers"] = [
        {"url": "https://api.server1.com"},
        {"url": "https://api.server2.com"},
    ]

    # Set up a sequence of inputs to be made by the mocked user.
    prompt_patcher.add_selection("Set Subscription")
    prompt_patcher.add_selection(f"{SUBS.Globus.name} ({SUBS.Globus.id})")

    prompt_patcher.add_selection("Set OpenAPI Location")
    prompt_patcher.add_input("prompt_toolkit_prompt", "./dummy.json")

    prompt_patcher.add_selections("Set Base URL", "https://api.server2.com")

    prompt_patcher.add_selection("<Submit>")

    result = gra(["init"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Successfully initialized GRA Repository" in result.output

    stage_config = GRAConfig.load().stages["production"]
    assert stage_config.base_url == "https://api.server2.com"
