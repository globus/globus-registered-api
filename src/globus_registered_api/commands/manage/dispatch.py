# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import click

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.rendering import prompt_selection

from .domain import BACK_SENTINEL
from .domain import EXIT_SENTINEL
from .domain import BackSentinel
from .domain import ConfiguratorMenu
from .domain import ExitSentinel
from .domain import MainMenu
from .domain import ManageContext
from .roles import RoleConfigurator
from .targets import TargetConfigurator


@click.command("manage")
@with_cli_context
def manage_command(ctx: CLIContext) -> None:
    """Interactively configure your GRA repo."""

    # This command has a lot of back and forth interaction with the user.
    # At a high level, it offers a main menu to select different subcommands from
    #   either the `TargetConfigurator` or the `RoleConfigurator`.
    # Subcommands may be invoked over and over until the user chooses to "exit" from
    #   the dispatch menu handled through this function.

    manage_context = _create_manage_context(ctx)
    main_menu = _create_main_menu(manage_context)

    current_menu: MainMenu | ConfiguratorMenu = main_menu
    with manage_context.globus_app:
        while True:
            option = prompt_selection("Menu Option", current_menu, show_selection=False)
            if isinstance(option, ExitSentinel):
                # Exit the command.
                break
            elif isinstance(option, BackSentinel):
                # Return to the main menu.
                current_menu = main_menu
            elif callable(option):
                # Invoke a subcommand, remaining at the current menu.
                option()
            else:
                # Descend into a sub-menu.
                current_menu = option


def _create_main_menu(manage_context: ManageContext) -> MainMenu:
    """Create a main navigation menu."""
    target_menu = TargetConfigurator(manage_context).menu_options
    role_menu = RoleConfigurator(manage_context).menu_options

    target_menu += [(BACK_SENTINEL, "<Back>"), (EXIT_SENTINEL, "<Exit>")]
    role_menu += [(BACK_SENTINEL, "<Back>"), (EXIT_SENTINEL, "<Exit>")]
    return [
        (target_menu, "Targets"),
        (role_menu, "Roles"),
        (EXIT_SENTINEL, "<Exit>"),
    ]


def _create_manage_context(ctx: CLIContext) -> ManageContext:
    """Create a context object to be provided to configurator subcommand objects."""
    config = RegisteredAPIConfig.load()
    if isinstance(config.core.specification, str):
        spec = load_openapi_spec(config.core.specification)
    else:
        spec = config.core.specification
    analysis = OpenAPISpecAnalyzer().analyze(spec)

    context = ManageContext(config=config, analysis=analysis, globus_app=ctx.globus_app)
    context.globus_app.login()

    return context
