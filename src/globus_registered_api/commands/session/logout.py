# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.commands._context import CLIContext
from globus_registered_api.commands._context import with_cli_context


@click.command()
@with_cli_context
def logout_command(ctx: CLIContext) -> None:
    """
    Log out the current user by revoking all tokens.

    When GLOBUS_PROFILE is set, only logs out from the active profile.
    """
    ctx.globus_app.logout()

    if profile := ctx.profile:
        click.echo(f"Logged out successfully from profile '{profile}'.")
    else:
        click.echo("Logged out successfully.")
