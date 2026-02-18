# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

import click

from globus_registered_api.clients import create_auth_client
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context


@click.command()
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def whoami_command(ctx: CLIContext, format: str) -> None:
    """
    Display information about the authenticated user.

    When GLOBUS_PROFILE is set, shows the active profile name.
    """
    auth_client = create_auth_client(ctx.globus_app)
    profile = ctx.profile

    userinfo = auth_client.userinfo()

    if format == "text":
        username = userinfo["preferred_username"]
        if profile:
            click.echo(f"{username} (profile: {profile})")
        else:
            click.echo(username)
    else:
        output = dict(userinfo.data)
        if profile:
            output["profile"] = profile
        click.echo(json.dumps(output, indent=2))
