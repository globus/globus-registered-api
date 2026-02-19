# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime
from uuid import UUID

import click

from globus_registered_api.clients import create_flows_client
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context


def _format_deletion_date(timestamp_str: str) -> str:
    """Format a deletion timestamp into a user-friendly string."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y at %H:%M UTC")
    except (ValueError, AttributeError):
        return timestamp_str


@click.command("delete")
@click.argument("registered_api_id", type=click.UUID)
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def delete_command(
    ctx: CLIContext,
    registered_api_id: UUID,
    format: str,
) -> None:
    """
    Delete a registered API by ID.

    This marks the API as DELETE_PENDING with a grace period.
    After the grace period, the API will be marked as DELETED.

    Only owners can delete a registered API.
    """
    flows_client = create_flows_client(ctx.globus_app)

    res = flows_client.delete_registered_api(registered_api_id)

    if format == "json":
        click.echo(json.dumps(res.data, indent=2))
    else:
        deletion_date = _format_deletion_date(res["scheduled_deletion_timestamp"])
        click.echo("Registered API marked for deletion:")
        click.echo(f"  ID:     {res['id']}")
        click.echo(f"  Name:   {res['name']}")
        click.echo("  Status: DELETE_PENDING")
        click.echo()
        click.echo(f"This API will be permanently deleted on {deletion_date}.")
