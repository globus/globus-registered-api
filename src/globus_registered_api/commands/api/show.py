# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.commands.api._common import echo_registered_api
from globus_registered_api.repositories.clients import GlobusClientRepository


@click.command("show")
@click.argument("registered_api_id")
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
def show_command(registered_api_id: str, format: str) -> None:
    """
    Get a registered API by ID.
    """
    flows_client = GlobusClientRepository.instance().flows

    res = flows_client.get_registered_api(registered_api_id)

    echo_registered_api(res, format)
