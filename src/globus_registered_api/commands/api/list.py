# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

import click

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api.commands._context import CLIContext
from globus_registered_api.commands._context import with_cli_context


@click.command("list")
@click.option(
    "--filter-roles",
    multiple=True,
    type=click.Choice(["owner", "administrator", "viewer"]),
    help="Filter by role(s). Can be specified multiple times.",
)
@click.option(
    "--per-page",
    type=click.IntRange(1, 100),
    default=10,
    help="Number of results per page (max 100)",
)
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def list_command(
    ctx: CLIContext, filter_roles: tuple[str, ...], per_page: int, format: str
) -> None:
    """
    List registered APIs for which the caller has a role.
    """
    flows_client = ExtendedFlowsClient(app=ctx.globus_app)

    paginator = flows_client.paginated.list_registered_apis(
        filter_roles=filter_roles if filter_roles else None, per_page=per_page
    )

    if format == "json":
        results: list[dict[str, object]] = []
        for page in paginator:
            results.extend(page["registered_apis"])
        click.echo(json.dumps(results, indent=2))
    else:
        first = True
        for page in paginator:
            for api in page["registered_apis"]:
                if first:
                    click.echo("ID                                   | Name")
                    click.echo("-------------------------------------|-----")
                    first = False
                click.echo(f"{api['id']} | {api['name']}")
