# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib

import click

from globus_registered_api.clients import create_flows_client
from globus_registered_api.commands.api._common import echo_registered_api
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context


@click.command("create")
@click.argument("name")
@click.argument(
    "target_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=pathlib.Path),
)
@click.option(
    "--description",
    required=True,
    help="Description for the registered API",
)
@click.option(
    "--owner",
    "owners",
    multiple=True,
    help="Set owner URN (can specify multiple, can only be set by owners)",
)
@click.option(
    "--administrator",
    "administrators",
    multiple=True,
    help="Set administrator URN (can specify multiple, can only be set by owners)",
)
@click.option(
    "--viewer",
    "viewers",
    multiple=True,
    help=(
        "Set viewer URN (can specify multiple, can only be set by owners "
        "and administrators)"
    ),
)
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def create_command(
    ctx: CLIContext,
    target_file: pathlib.Path,
    name: str,
    description: str,
    owners: tuple[str, ...],
    administrators: tuple[str, ...],
    viewers: tuple[str, ...],
    format: str,
) -> None:
    """
    Create a new registered API from an OpenAPI specification.

    Extracts a target endpoint from an OpenAPI spec and registers it with
    the Flows service.

    NAME - Name of the registered API.

    TARGET_FILE - A filepath to a target JSON object.

    DESCRIPTION - Description for the registered API.

    Example:

    \b
        gra api create  "My API"  ./target.json--description "My API"
    """
    flows_client = create_flows_client(ctx.globus_app)

    target = json.loads(target_file.read_text())
    res = flows_client.create_registered_api(
        name=name,
        description=description,
        target=target,
        owners=list(owners),
        administrators=list(administrators),
        viewers=list(viewers),
    )

    echo_registered_api(res, format)
