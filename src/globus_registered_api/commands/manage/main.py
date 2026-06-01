# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.config import GRAConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.rendering import DispatchMenu
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
    # If an stage is added or removed during command usage, it will be
    # automatically analyzed or removed from the analyzer's state.
    analyzer = OpenAPISpecAnalyzer()
    analyzer.analyze(config)

    return ManageContext(config=config, analyzer=analyzer)


class ManageMainMenu(DispatchMenu):
    menu_title = "Main Menu"

    def __init__(self, context: ManageContext) -> None:
        self.context = context

        self._manage_targets_menu = TargetNavigationMenu(self.context)
        self._manage_stages_menu = StageNavigationMenu(self.context)

    @property
    def options(self) -> LabeledDispatchOptions:
        return [
            (self._manage_targets_menu, "Manage Targets"),
            (self._select_role_menu_by_stage, "Manage Roles"),
            (self._manage_stages_menu, "Manage Stages"),
        ]

    def _select_role_menu_by_stage(self) -> DispatchMenu:
        stages = sorted(self.context.config.stages.keys())
        stage_options = [(stage, stage) for stage in stages]
        # Note - this will not actually prompt if there is only one stage.
        stage = prompt_selection("Stage", stage_options)
        return RoleNavigationMenu(self.context, stage)
