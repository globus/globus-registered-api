# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import click

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.rendering import prompt_selection

from ...context import CLIContext
from ...context import with_cli_context
from .domain import ManageContext
from .domain import SubcommandCanceled
from .roles import RoleConfigurator
from .targets import TargetConfigurator

_SENTINELS = SimpleNamespace(
    BACK=lambda: None,
    EXIT=lambda: None,
)


@click.command("manage")
@with_cli_context
def manage_command(ctx: CLIContext) -> None:
    """Manage Globus Registered API configuration."""
    manage_context = _create_manage_context(ctx)

    target_configurator = TargetConfigurator(manage_context)
    role_configurator = RoleConfigurator(manage_context)

    _common_registry_options = [("Back", _SENTINELS.BACK), ("Exit", _SENTINELS.EXIT)]
    main_menu = [
        ("Targets", target_configurator.menu_options + _common_registry_options),
        ("Roles", role_configurator.menu_options + _common_registry_options),
        ("Exit", _SENTINELS.EXIT),
    ]

    # Re-order to fit prompt-toolkit choice format
    menu_options = [(func, label) for label, func in main_menu]

    with manage_context.globus_app:
        while True:
            subcommand = prompt_selection("Menu Option", menu_options)
            match subcommand:
                case _SENTINELS.BACK:
                    # Back out of a sub-menu.
                    menu_options = [(func, label) for label, func in main_menu]
                case _SENTINELS.EXIT:
                    # Exit the application.
                    click.echo("Exiting.")
                    break
                case _ if callable(subcommand):
                    # Invoke a subcommand.
                    try:
                        subcommand()
                    except SubcommandCanceled:
                        pass
                case _:
                    # Descend into a sub-menu.
                    menu_options = [(func, label) for label, func in subcommand]


def _create_manage_context(ctx: CLIContext) -> ManageContext:
    config = RegisteredAPIConfig.load()
    if isinstance(config.core.specification, str):
        spec = load_openapi_spec(config.core.specification)
    else:
        spec = config.core.specification
    analysis = OpenAPISpecAnalyzer().analyze(spec)

    context = ManageContext(config=config, analysis=analysis, globus_app=ctx.globus_app)
    context.globus_app.login()

    return context
