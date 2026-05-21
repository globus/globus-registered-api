# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.config import GRAConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import DispatchOption
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import MenuDispatcher
from globus_registered_api.rendering import prompt_selection
from globus_registered_api.repositories.clients import GlobusClientRepository

from .context import ManageContext
from .role import RoleNavigationMenu
from .stage import StageNavigationMenu
from .target import TargetNavigationMenu


@click.command("manage")
def manage_command() -> None:
    """Interactively configure your GRA repo."""
    # Prompt for login on create to avoid some mid-execution login cases.
    GlobusClientRepository.instance().globus_app.login()

    # This command has a lot of back and forth interaction with the user.
    # It creates a main menu of resource management menus and hands off
    #   execution to the MenuDispatch to provide a persistent management
    #   interface.
    context = _create_manage_context()
    menu = ManageMainMenu(context)

    MenuDispatcher(menu).dispatch()


def _create_manage_context() -> ManageContext:
    """Create a context object to be provided to configurator subcommand objects."""
    config = GRAConfig.load()

    # Create an analyzer & analyze the current config.
    # If additional stages with distinct openapi specifications are added
    #   mid-execution additional analysis will be performed as needed.
    analyzer = OpenAPISpecAnalyzer()
    analyzer.analyze(config)

    return ManageContext(config=config, analyzer=analyzer)


class ManageMainMenu(DispatchMenu):
    menu_title = "Main Menu"

    def __init__(self, context: ManageContext) -> None:
        self.context = context

    @property
    def options(self) -> LabeledDispatchOptions:
        return [
            (TargetNavigationMenu(self.context), "Manage Targets"),
            (self._role_navigation_menu(), "Manage Roles"),
            (StageNavigationMenu(self.context), "Manage Stages"),
        ]

    def _role_navigation_menu(self) -> DispatchOption:
        if len(self.context.config.stages) == 1:
            only_stage = next(iter(self.context.config.stages.keys()))
            return RoleNavigationMenu(self.context, only_stage)

        def _select_role_stage() -> DispatchMenu:
            stage = prompt_selection(
                "Stage",
                [(stage, stage) for stage in sorted(self.context.config.stages.keys())],
            )
            return RoleNavigationMenu(self.context, stage)

        return _select_role_stage
