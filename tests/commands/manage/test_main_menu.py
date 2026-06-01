# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0


def test_manage_requires_a_config(gra):
    result = gra("manage")

    assert result.exit_code == 1
    assert "Missing config file" in result.output
    assert "gra init" in result.output


def test_manage_main_menu_exiting(prompt_patcher, config, gra):
    config.commit()

    prompt_patcher.add_selection("<Exit>")

    result = gra("manage", catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output == ""


def test_manage_main_menu_navigation(prompt_patcher, config, gra):
    config.commit()

    # Descend into the role management menu.
    prompt_patcher.add_selections("Manage Roles", "<Register a New Role>")
    prompt_patcher.add_selections("<Cancel>", "<Back>")

    # Descend into the target management menu.
    prompt_patcher.add_selections("Manage Targets", "<Register a New Target>")
    prompt_patcher.add_selections("<Cancel>", "<Back>")

    # Descend into the stage management menu.
    prompt_patcher.add_selections("Manage Stages", "<Register a New Stage>")
    prompt_patcher.add_selections("<Cancel>", "<Exit>")

    result = gra("manage", catch_exceptions=False)

    assert result.exit_code == 0
