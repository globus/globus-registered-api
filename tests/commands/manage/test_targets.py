# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import pytest
from rich.console import Console

from globus_registered_api.commands.manage.target import (
    modification as modification_module,
)
from globus_registered_api.config import GRAConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import TargetConfig


@pytest.fixture
def rich_disabled_colors(monkeypatch):
    monkeypatch.setattr(modification_module, "console", Console(color_system=None))


@pytest.fixture(autouse=True)
def committed_config(config):
    config.commit()


def test_target_management_add_target_no_scope(prompt_patcher, gra):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Targets", "<Register a New Target>")

    prompt_patcher.add_selections("Select Route", "/example (GET)")
    prompt_patcher.add_selection("Set Alias")
    prompt_patcher.add_input("click_prompt", "get-example")

    prompt_patcher.add_selection("<Submit>")
    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    # Verify we've added the expected target to the config and committed it.
    expected = {
        "get-example": TargetConfig(
            path="/example",
            method="GET",
            description="Example GET endpoint",
        )
    }
    assert GRAConfig.load().targets == expected


def test_target_management_add_target_manual_scope(prompt_patcher, gra):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Targets", "<Register a New Target>")

    prompt_patcher.add_selections("Select Route", "/example (GET)")
    prompt_patcher.add_selection("Set Alias")
    prompt_patcher.add_input("click_prompt", "get-example")
    prompt_patcher.add_selections("Set Globus Scope", "<Enter a scope string>")
    prompt_patcher.add_input("click_prompt", "example:read")

    prompt_patcher.add_selection("<Submit>")
    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    # Verify we've added the expected target to the config and committed it.
    expected = {
        "get-example": TargetConfig(
            path="/example",
            method="GET",
            description="Example GET endpoint",
            security=TargetConfig.Security(globus_auth_scope="example:read"),
        )
    }
    assert GRAConfig.load().targets == expected


def test_target_management_add_target_openapi_scopes(
    prompt_patcher, openapi_schema, gra
):
    # Update the spec to define scopes for a target.
    openapi_schema["paths"]["/example"]["get"]["security"] = [
        {"GlobusAuth": ["example:read"]},
        {"GlobusAuth": ["example:write"]},
    ]

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Targets", "<Register a New Target>")

    prompt_patcher.add_selections("Select Route", "/example (GET)")
    prompt_patcher.add_selection("Set Alias")
    prompt_patcher.add_input("click_prompt", "get-example")

    prompt_patcher.add_selection("<Submit>")

    prompt_patcher.add_selection("get-example")
    prompt_patcher.add_selection("Print Target")

    prompt_patcher.add_selection("<Exit>")

    # Execute
    result = gra(["manage"], catch_exceptions=False)

    expected = TargetConfig(
        path="/example", method="GET", description="Example GET endpoint"
    )
    assert GRAConfig.load().targets == {"get-example": expected}

    # Spec-defined scopes aren't committed to config, instead they are presented
    # as "imputed".
    for keyword in ("Imputed", "example:read", "example:write"):
        assert keyword in result.output


def test_target_management_add_target_manual_route(prompt_patcher, gra):
    """
    Register a target whose route specifier doesn't exist in the openapi spec.
    """

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Targets", "<Register a New Target>")

    prompt_patcher.add_selection("Select Route")
    prompt_patcher.add_selection("<Enter custom path and method>")
    prompt_patcher.add_input("click_prompt", "/manual")
    prompt_patcher.add_selection("POST")

    prompt_patcher.add_selection("Set Alias")
    prompt_patcher.add_input("click_prompt", "post-manual")

    prompt_patcher.add_selection("<Submit>")
    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    expected = TargetConfig(
        path="/manual", method="POST", description="post-manual: POST /manual"
    )
    assert GRAConfig.load().targets == {"post-manual": expected}


def test_target_management_print_target(
    prompt_patcher, config, gra, rich_disabled_colors
):
    # Add some targets to the config.
    get_target = TargetConfig(
        path="/example",
        method="GET",
        description="Get example",
        data_templates={
            "request": {},
            "response": {},
        },
    )
    post_target = TargetConfig(
        path="/example",
        method="POST",
        description="Post example",
        data_templates={
            "request": {},
            "response": {},
        },
    )
    config.targets = {"get-example": get_target, "post-example": post_target}
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Targets")

    prompt_patcher.add_selections("get-example", "Print Target")
    prompt_patcher.add_selection("<Exit>")

    result = gra(["manage"], catch_exceptions=False)

    assert "get-example" in result.output
    assert "TargetConfig" in result.output
    assert "path='/example'" in result.output
    assert "method='GET'" in result.output
    assert "templates" not in result.output.lower()


def test_target_management_display_maintains_imputed_scope_ordering(
    prompt_patcher, config, openapi_schema, gra, rich_disabled_colors
):
    # TODO - this doesn't work, scopes are combined across stages in a set &
    #     & re-ordered for the global target view.

    # Simulate a laundry list of scopes in the OpenAPI specification to make it
    #   unlikely we accidentally reorder them back into the same order.
    suffixes = ["read", "write", "delete", "admin", "superuser", "owner", "all"]
    scopes = [f"example:{suffix}" for suffix in suffixes]
    # Update the spec to define scopes for a target.
    openapi_schema["paths"]["/example"]["get"]["security"] = [
        {"GlobusAuth": [f"example:{scope}"]} for scope in scopes
    ]

    # Add a target to the config which points at that spec endpoint.
    target = TargetConfig(path="/example", method="GET", description="desc")
    config.targets = {"get-example": target}
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Targets")
    prompt_patcher.add_selections("get-example", "Print Target")
    prompt_patcher.add_selection("<Exit>")

    result = gra(["manage"], catch_exceptions=False)

    # Verify that "order is maintained" by ensuring that the index of the output stream
    #   is increasing as we go through the list of scopes in their original order.
    actual_order = sorted(scopes, key=lambda s: result.output.index(s))
    assert actual_order == scopes


def test_target_management_remove_target(prompt_patcher, config, gra):
    # Add some targets to the config.
    get_target = TargetConfig(path="/example", method="GET", description="d")
    post_target = TargetConfig(path="/example", method="POST", description="d")
    config.targets = {"get-example": get_target, "post-example": post_target}
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Targets")
    prompt_patcher.add_selections("get-example", "Remove Target", "<Exit>")
    prompt_patcher.add_input("confirmation", True)

    gra(["manage"], catch_exceptions=False)

    assert GRAConfig.load().targets == {"post-example": post_target}


def test_target_management_modify_target(prompt_patcher, config, gra):
    # Add a target to the config.
    target = TargetConfig(path="/example", method="GET", description="d")
    config.targets = {"get-example": target}

    # Add a registered api for the target
    ra_config = RegisteredAPIConfig(registered_api_id=uuid4())
    config.stages["production"].registered_apis["get-example"] = ra_config
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Targets", "get-example")

    prompt_patcher.add_selection("Modify Alias")
    prompt_patcher.add_input("click_prompt", "get-example-updated")
    prompt_patcher.add_selection("Modify Description")
    prompt_patcher.add_input("click_prompt", "Updated description")

    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    loaded_config = GRAConfig.load()
    expected = TargetConfig(
        path="/example",
        method="GET",
        description="Updated description",
    )
    assert loaded_config.targets == {"get-example-updated": expected}
    assert loaded_config.stages["production"].registered_apis == {
        "get-example-updated": ra_config,
    }


def test_target_management_remove_scope(prompt_patcher, config, gra):
    get_target = TargetConfig(
        path="/example",
        method="GET",
        description="desc",
        security=TargetConfig.Security(globus_auth_scope="example:read"),
    )
    config.targets = {"get-example": get_target}
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selections("Manage Targets", "get-example")
    prompt_patcher.add_selections("Modify Globus Scope", "<None>")
    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    expected = TargetConfig(path="/example", method="GET", description="desc")
    assert GRAConfig.load().targets == {"get-example": expected}
