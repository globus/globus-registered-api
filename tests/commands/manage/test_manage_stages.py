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
from globus_registered_api.config import StageConfig
from globus_registered_api.config import TargetConfig
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


@pytest.fixture(autouse=True)
def autocommitted_config(config):
    config.commit()


def test_stage_management_add_stage(prompt_patcher, mock_auth_client, gra):
    user_id = UUID(mock_auth_client.userinfo()["sub"])

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Stages")
    prompt_patcher.add_selection("<Register a New Stage>")

    prompt_patcher.add_selection("Set Name")
    prompt_patcher.add_input("click_prompt", "beta")

    prompt_patcher.add_selections("Set Subscription")
    prompt_patcher.add_selection(f"{SUBS.Globus.name} ({SUBS.Globus.id})")

    prompt_patcher.add_selection("Set OpenAPI Location")
    openapi_spec_path = "https://api.example.com/openapi.json"
    prompt_patcher.add_input("prompt_toolkit_prompt", openapi_spec_path)

    prompt_patcher.add_selections("Set Base URL", "https://api.example.com")

    prompt_patcher.add_selections("<Submit>", "<Exit>")

    # Act
    gra(["manage"], catch_exceptions=False)

    # Verify we've added the expected stage to the config and committed it.
    user_role = RoleConfig(type="identity", id=user_id, access_level="owner")
    assert GRAConfig.load().stages["beta"] == StageConfig(
        subscription_id=SUBS.Globus.id,
        specification=openapi_spec_path,
        base_url="https://api.example.com",
        roles=[user_role],
    )


def test_stage_management_remove_stage(prompt_patcher, config, gra):
    config.stages["beta"] = StageConfig(
        subscription_id=SUBS.Globus.id,
        specification="https://api.example.com/openapi.json",
        base_url="https://api.example.com",
        roles=[],
    )
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Stages", "Manage 'beta'")

    prompt_patcher.add_selection("Remove Stage")
    prompt_patcher.add_input("confirmation", True)

    prompt_patcher.add_selection("<Exit>")

    # Act
    gra(["manage"], catch_exceptions=False)

    assert "beta" not in GRAConfig.load().stages


def test_stage_management_modify_stage(prompt_patcher, gra):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Stages", "Manage 'production'")

    prompt_patcher.add_selection("Rename Stage")
    prompt_patcher.add_input("click_prompt", "prod")

    prompt_patcher.add_selection("Modify Subscription")
    prompt_patcher.add_selection(f"{SUBS.UChicago.name} ({SUBS.UChicago.id})")

    prompt_patcher.add_selection("Modify Base URL")
    prompt_patcher.add_input("click_prompt", "https://totall-new-domain.com")

    prompt_patcher.add_selection("<Exit>")

    # Act
    gra(["manage"], catch_exceptions=False)

    updated_config = GRAConfig.load()
    assert "production" not in updated_config.stages
    updated_stage = updated_config.stages["prod"]
    assert updated_stage.subscription_id == SUBS.UChicago.id
    assert updated_stage.base_url == "https://totall-new-domain.com"


def test_stage_management_last_stage_removal_is_rejected(prompt_patcher, gra):

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Stages", "Manage 'production'")
    prompt_patcher.add_selection("Remove Stage")

    prompt_patcher.add_selection("<Exit>")

    # Act
    result = gra(["manage"], catch_exceptions=False)

    # Verify we didn't delete the stage & informed the user why.
    assert "production" in GRAConfig.load().stages
    assert "Cannot remove the only remaining stage" in result.output
    assert "add a new stage" in result.output


def test_stage_management_rename_stage_updates_targets(
    prompt_patcher,
    config,
    gra,
):
    # Add a target explicitly pointing at the "production" stage.
    config.targets = {
        "get-example": TargetConfig(
            path="/example",
            method="GET",
            description="Desc",
            stages=["production"],
        ),
    }
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Stages", "Manage 'production'")

    prompt_patcher.add_selection("Rename Stage")
    prompt_patcher.add_input("click_prompt", "prod")

    prompt_patcher.add_selection("<Exit>")

    # Act
    gra(["manage"], catch_exceptions=False)

    # Verify the target now points at 'prod' instead of 'production'
    assert GRAConfig.load().targets["get-example"].stages == ["prod"]
