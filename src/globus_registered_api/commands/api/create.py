# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

import click

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api.commands._context import CLIContext
from globus_registered_api.commands._context import with_cli_context
from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi import AmbiguousContentTypeError
from globus_registered_api.openapi import OpenAPILoadError
from globus_registered_api.openapi import TargetNotFoundError
from globus_registered_api.openapi import process_target


@click.command("create")
@click.argument("openapi_spec")
@click.argument("method", type=click.Choice(HTTP_METHODS, case_sensitive=False))
@click.argument("route")
@click.argument("name")
@click.option(
    "--content-type",
    default="*",
    help="Target content-type for request body (required if multiple exist)",
)
@click.option(
    "--description",
    required=True,
    help="Description for the registered API",
)
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@with_cli_context
def create_command(
    ctx: CLIContext,
    openapi_spec: str,
    method: str,
    route: str,
    name: str,
    content_type: str,
    description: str,
    format: str,
) -> None:
    """
    Create a new registered API from an OpenAPI specification.

    Extracts a target endpoint from an OpenAPI spec and registers it with
    the Flows service.

    OPENAPI_SPEC - A filepath or URL to an OpenAPI specification (JSON or YAML).

    METHOD - Target API's HTTP method (e.g., get, post, put, delete).

    ROUTE - Target API's route path (e.g., /items or /items/{item_id}).

    NAME - Name for the registered API.

    Example:

        globus-registered-api create ./spec.json get /items "My API"
            --description "My API"
    """
    try:
        target = TargetSpecifier.create(method, route, content_type)
    except ValueError as e:
        raise click.ClickException(str(e))

    try:
        result = process_target(openapi_spec, target)
    except (OpenAPILoadError, TargetNotFoundError, AmbiguousContentTypeError) as e:
        raise click.ClickException(str(e))

    flows_client = ExtendedFlowsClient(app=ctx.globus_app)

    res = flows_client.create_registered_api(
        name=name,
        description=description,
        target=result.to_dict(),
    )

    if format == "json":
        click.echo(json.dumps(res.data, indent=2))
    else:
        click.echo(f"ID:          {res['id']}")
        click.echo(f"Name:        {res['name']}")
        click.echo(f"Description: {res['description']}")
        click.echo(f"Created:     {res['created_timestamp']}")
