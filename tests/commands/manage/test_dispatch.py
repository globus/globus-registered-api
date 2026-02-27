# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

from globus_registered_api.commands.manage.domain import BACK_SENTINEL
from globus_registered_api.commands.manage.domain import EXIT_SENTINEL
from globus_registered_api.config import RoleConfig


def test_manage_dispatch_requires_a_config(gra):
    result = gra("manage")

    assert result.exit_code == 1
    assert "Missing repository config file" in result.output
    assert "gra init" in result.output


def test_manage_dispatch_selecting_exit(prompt_patcher, config, gra):
    config.commit()

    prompt_patcher.add_input("selection", EXIT_SENTINEL)

    result = gra("manage", catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output == ""


def test_manage_dispatch_selecting_subcommands(prompt_patcher, config, gra):
    group_id = uuid4()
    config.roles.append(RoleConfig(type="group", id=group_id, access_level="owner"))
    config.commit()

    prompt_patcher.add_input("selection", "Roles")
    prompt_patcher.add_input("selection", "List Roles")
    prompt_patcher.add_input("selection", BACK_SENTINEL)
    prompt_patcher.add_input("selection", "Targets")
    prompt_patcher.add_input("selection", "List Targets")
    prompt_patcher.add_input("selection", EXIT_SENTINEL)

    result = gra("manage", catch_exceptions=False)

    assert result.exit_code == 0
    assert str(group_id) in result.output
    assert "Path" in result.output
