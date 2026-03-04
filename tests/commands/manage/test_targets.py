# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

import pytest
from rich.console import Console

import globus_registered_api.commands.manage.targets as targets_module
from globus_registered_api.commands.manage.domain import ManageContext
from globus_registered_api.commands.manage.targets import TargetConfigurator
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer


@pytest.fixture
def rich_disabled_colors(monkeypatch):
    monkeypatch.setattr(targets_module, "console", Console(color_system=None))


@pytest.fixture
def target_configurator(config):
    analysis = OpenAPISpecAnalyzer().analyze(config.core.specification)
    ctx = ManageContext(config=config, analysis=analysis, globus_app=MagicMock())
    return TargetConfigurator(ctx)


def test_target_management_add_target(prompt_patcher, target_configurator):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "/example (GET)")
    prompt_patcher.add_input("click_prompt", "get-example")
    prompt_patcher.add_input("confirmation", False)  # Skip scope configurations.

    target_configurator.add_target()

    # Verify we've added the expected target to the config and committed it.
    expected = TargetConfig(path="/example", method="GET", alias="get-example")
    assert RegisteredAPIConfig.load().targets == [expected]


def test_target_management_add_target_with_manual_scope(
    prompt_patcher, target_configurator
):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "/example (GET)")
    prompt_patcher.add_input("click_prompt", "get-example")
    prompt_patcher.add_input("confirmation", True)  # Configure scope.
    prompt_patcher.add_input("selection", "example:read")

    target_configurator.add_target()

    # Verify we've added the expected target to the config and committed it.
    expected = TargetConfig(
        path="/example",
        method="GET",
        alias="get-example",
        security=TargetConfig.Security(globus_auth_scope="example:read"),
    )
    assert RegisteredAPIConfig.load().targets == [expected]


def test_target_management_add_target_with_defined_scopes(
    prompt_patcher, config, capsys, rich_disabled_colors
):
    # Update the spec to define scopes for a target.
    config.core.specification.paths["/example"].get.security = [
        {"GlobusAuth": ["example:read"]},
        {"GlobusAuth": ["example:write"]},
    ]
    config.commit()

    # Re-analyze the updated specification instead of using the fixture-provided one.
    analysis = OpenAPISpecAnalyzer().analyze(config.core.specification)
    ctx = ManageContext(config=config, analysis=analysis, globus_app=MagicMock())
    target_configurator = TargetConfigurator(ctx)

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "/example (GET)")
    prompt_patcher.add_input("click_prompt", "get-example")

    target_configurator.add_target()

    expected = TargetConfig(path="/example", method="GET", alias="get-example")
    assert RegisteredAPIConfig.load().targets == [expected]

    # Spec-defined scopes are not committed to config, but are flagged as "imputed".
    outstream = capsys.readouterr().out
    for keyword in ("Imputed", "example:read", "example:write"):
        assert keyword in outstream


def test_target_management_add_manual_target(prompt_patcher, target_configurator):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "<Enter custom path and method>")
    prompt_patcher.add_input("click_prompt", "/manual")
    prompt_patcher.add_input("selection", "POST")
    prompt_patcher.add_input("click_prompt", "post-manual")
    prompt_patcher.add_input("confirmation", False)  # Skip scope configurations.

    target_configurator.add_target()

    expected = TargetConfig(path="/manual", method="POST", alias="post-manual")
    assert RegisteredAPIConfig.load().targets == [expected]


def test_target_management_list_targets(
    prompt_patcher, config, target_configurator, capsys
):
    # Add some targets to the config.
    config.targets = [
        TargetConfig(path="/example", method="GET", alias="get-example"),
        TargetConfig(path="/example", method="POST", alias="post-example"),
    ]
    config.commit()

    target_configurator.list_targets()

    outstream = capsys.readouterr().out
    for key in ("/example", "GET", "POST", "get-example", "post-example"):
        assert key in outstream


def test_target_management_display_target(
    prompt_patcher, config, target_configurator, rich_disabled_colors, capsys
):
    # Add some targets to the config.
    get_target = TargetConfig(path="/example", method="GET", alias="get-example")
    post_target = TargetConfig(path="/example", method="POST", alias="post-example")
    config.targets = [get_target, post_target]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", get_target)

    target_configurator.display_target()

    outstream = capsys.readouterr().out
    assert "TargetConfig" in outstream
    assert "path='/example'" in outstream
    assert "method='GET'" in outstream
    assert "alias='get-example'" in outstream


def test_target_management_display_maintains_imputed_scope_ordering(
    prompt_patcher, config, rich_disabled_colors, capsys
):
    # Simulate a laundry list of scopes in the OpenAPI specification to make it
    #   unlikely we accidentally reorder them back into the same order.
    suffixes = ["read", "write", "delete", "admin", "superuser", "owner", "all"]
    scopes = [f"example:{suffix}" for suffix in suffixes]
    # Update the spec to define scopes for a target.
    config.core.specification.paths["/example"].get.security = [
        {"GlobusAuth": [f"example:{scope}"]} for scope in scopes
    ]

    # Add a target to the config which points at that spec endpoint.
    target = TargetConfig(path="/example", method="GET", alias="get-example")
    config.targets = [target]
    config.commit()

    # Re-analyze the updated specification instead of using the fixture-provided one.
    analysis = OpenAPISpecAnalyzer().analyze(config.core.specification)
    ctx = ManageContext(config=config, analysis=analysis, globus_app=MagicMock())
    target_configurator = TargetConfigurator(ctx)

    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", target)

    target_configurator.display_target()

    outstream = capsys.readouterr().out
    # Verify that "order is maintained" by ensuring that the index of the output stream
    #   is increasing as we go through the list of scopes in their original order.
    actual_order = sorted(scopes, key=lambda s: outstream.index(s))
    assert actual_order == scopes


def test_target_management_remove_target(prompt_patcher, config, target_configurator):
    # Add some targets to the config.
    get_target = TargetConfig(path="/example", method="GET", alias="get-example")
    post_target = TargetConfig(path="/example", method="POST", alias="post-example")
    config.targets = [get_target, post_target]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", get_target)

    target_configurator.remove_target()

    assert RegisteredAPIConfig.load().targets == [post_target]


def test_target_management_modify_target(prompt_patcher, config, target_configurator):
    # Add a target to the config.
    target = TargetConfig(path="/example", method="GET", alias="get-example")
    config.targets = [target]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", target)
    prompt_patcher.add_input("click_prompt", "get-example-updated")  # Change the alias
    prompt_patcher.add_input("selection", None)  # Don't add a scope.

    target_configurator.modify_target()

    expected = TargetConfig(path="/example", method="GET", alias="get-example-updated")
    assert RegisteredAPIConfig.load().targets == [expected]


def test_target_management_modify_target_remove_scope(
    prompt_patcher, config, target_configurator
):
    target = TargetConfig(
        path="/example",
        method="GET",
        alias="get-example",
        security=TargetConfig.Security(globus_auth_scope="example:read"),
    )
    config.targets = [target]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", target)
    prompt_patcher.add_input("click_prompt", "get-example")  # Don't change the alias
    prompt_patcher.add_input("selection", None)  # Remove the scope.

    target_configurator.modify_target()

    expected = TargetConfig(path="/example", method="GET", alias="get-example")
    assert RegisteredAPIConfig.load().targets == [expected]
