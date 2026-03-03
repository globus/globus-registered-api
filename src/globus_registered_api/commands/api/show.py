# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.clients import create_flows_client
from globus_registered_api.commands.api._common import echo_registered_api
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context


@click.command("show")
@click.argument("registered_api_id")
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def show_command(ctx: CLIContext, registered_api_id: str, format: str) -> None:
    """
    Get a registered API by ID.
    """
    flows_client = create_flows_client(ctx.globus_app)

    res = flows_client.get_registered_api(registered_api_id)

    echo_registered_api(res, format)
