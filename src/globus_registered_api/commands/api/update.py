# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import typing as t
from uuid import UUID

import click

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api.commands._context import CLIContext
from globus_registered_api.commands._context import with_cli_context


@click.command("update")
@click.argument("registered_api_id", type=click.UUID)
@click.option("--name", help="Update the name of the registered API")
@click.option("--description", help="Update the description of the registered API")
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
@click.option(
    "--no-administrators",
    is_flag=True,
    help="Clear all administrators (can only be set by owners)",
)
@click.option(
    "--no-viewers",
    is_flag=True,
    help="Clear all viewers (can only be set by owners and administrators)",
)
@click.option(
    "--target-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    help="Path to JSON file containing target definition",
)
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def update_command(
    ctx: CLIContext,
    registered_api_id: UUID,
    name: str | None,
    description: str | None,
    owners: tuple[str, ...],
    administrators: tuple[str, ...],
    viewers: tuple[str, ...],
    no_administrators: bool,
    no_viewers: bool,
    target_file: pathlib.Path | None,
    format: str,
) -> None:
    """
    Update a registered API by ID.

    Use this command to modify the name, description, roles, or target
    definition of an existing registered API.
    """
    flows_client = ExtendedFlowsClient(app=ctx.globus_app)

    # Validate mutually exclusive options
    if administrators and no_administrators:
        raise click.UsageError(
            "--administrator and --no-administrators cannot be used together"
        )
    if viewers and no_viewers:
        raise click.UsageError("--viewer and --no-viewers cannot be used together")

    request: dict[str, t.Any] = {}
    if name is not None:
        request["name"] = name
    if description is not None:
        request["description"] = description
    if owners:
        request["owners"] = list(set(owners))
    if no_administrators:
        request["administrators"] = []
    elif administrators:
        request["administrators"] = list(set(administrators))
    if no_viewers:
        request["viewers"] = []
    elif viewers:
        request["viewers"] = list(set(viewers))
    if target_file is not None:
        try:
            request["target"] = json.loads(target_file.read_text())
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON in target file: {e}")
        except UnicodeDecodeError as e:
            raise click.UsageError(f"Unable to read target file: {e}")

    res = flows_client.update_registered_api(registered_api_id, **request)

    if format == "json":
        click.echo(json.dumps(res.data, indent=2))
    else:
        click.echo(f"ID:             {res['id']}")
        click.echo(f"Name:           {res['name']}")
        click.echo(f"Description:    {res['description']}")
        click.echo(f"Owners:         {res['roles']['owners']}")
        click.echo(f"Administrators: {res['roles']['administrators']}")
        click.echo(f"Viewers:        {res['roles']['viewers']}")
        click.echo(f"Created:        {res['created_timestamp']}")
        if res.get("edited_timestamp"):
            click.echo(f"Edited:         {res['edited_timestamp']}")
