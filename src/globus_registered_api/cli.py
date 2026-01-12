# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterable
import typing as t

import json
import os
from difflib import Differ

import click
from globus_sdk import AuthClient
from globus_sdk import ClientApp
from globus_sdk import FlowsClient
from globus_sdk import GlobusAPIError
from globus_sdk import GlobusAppConfig
from globus_sdk import Scope
from globus_sdk import UserApp

from globus_registered_api.extended_flows_client import ExtendedFlowsClient
from globus_registered_api.aperture_science import OpenApiEnrichmentCenter
from globus_registered_api.loader import load_openapi_schema
from globus_registered_api.services import SERVICE_CONFIGS

# Constants
RAPI_NATIVE_CLIENT_ID = "9dc7dfff-cfe8-4339-927b-28d29e1b2f42"

SCOPE_REQUIREMENTS: dict[str, str | Scope | Iterable[str | Scope]] = {
    AuthClient.scopes.resource_server: [AuthClient.scopes.openid],
    FlowsClient.scopes.resource_server: [FlowsClient.scopes.all],
}

_APP_CONFIG = GlobusAppConfig(auto_redrive_gares=True)


# Error handling
def _handle_globus_api_error(err: GlobusAPIError) -> None:
    """
    Handle GlobusAPIError, providing helpful messaging for auth errors.

    :param err: The GlobusAPIError that was raised
    :raises GlobusAPIError: Re-raises if not an authentication error
    """
    if err.code == "AUTHENTICATION_ERROR":
        click.secho("Authentication Error", fg="red", bold=True, err=True)
        click.echo(
            "Your authentication tokens are invalid or have been revoked.\n"
            "Please run:\n\n"
            "    globus-registered-api logout\n"
            "    globus-registered-api whoami\n\n"
            "to re-authenticate.",
            err=True,
        )
        sys.exit(1)
    raise err


class ExceptionHandlingGroup(click.Group):
    """Click Group that handles GlobusAPIError exceptions."""

    def invoke(self, ctx: click.Context) -> object:
        try:
            return super().invoke(ctx)
        except GlobusAPIError as err:
            _handle_globus_api_error(err)
            return None


# Helper functions
def _create_globus_app() -> UserApp | ClientApp:
    """
    Create and return a Globus app based on environment variables.

    Checks for GLOBUS_CLIENT_ID and GLOBUS_CLIENT_SECRET environment variables.
    If both are present, creates a ClientApp for client credentials authentication.
    Otherwise, creates a UserApp with a registered native client.

    :return: A ClientApp if both environment variables are set, otherwise a UserApp
    :raises ValueError: If only one of the required environment variables is set
    """
    client_id = os.getenv("GLOBUS_REGISTERED_API_CLIENT_ID")
    client_secret = os.getenv("GLOBUS_REGISTERED_API_CLIENT_SECRET")
    app_name = "globus-registered-api-cli"

    # Validate: both or neither
    if bool(client_id) ^ bool(client_secret):
        raise ValueError(
            "Both GLOBUS_CLIENT_ID and GLOBUS_CLIENT_SECRET must be set, or neither."
        )

    if client_id and client_secret:
        return ClientApp(
            app_name=app_name,
            client_id=client_id,
            client_secret=client_secret,
            scope_requirements=SCOPE_REQUIREMENTS,
            config=_APP_CONFIG,
        )
    else:
        return UserApp(
            app_name=app_name,
            client_id=RAPI_NATIVE_CLIENT_ID,
            scope_requirements=SCOPE_REQUIREMENTS,
            config=_APP_CONFIG,
        )


def _create_auth_client(app: UserApp | ClientApp) -> AuthClient:
    """
    Create an AuthClient for the given app.

    :param app: A Globus app instance to use for authentication
    :return: An AuthClient configured with the provided app
    """
    return AuthClient(app=app)


def _create_flows_client(app: UserApp | ClientApp) -> ExtendedFlowsClient:
    """
    Create an ExtendedFlowsClient for the given app.

    :param app: A Globus app instance to use for authentication
    :return: An ExtendedFlowsClient configured with the provided app
    """
    return ExtendedFlowsClient(app=app)


# CLI commands
@click.group(cls=ExceptionHandlingGroup)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Globus Registered API Command Line Interface."""
    ctx.obj = _create_globus_app()


@cli.command()
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@click.pass_context
def whoami(ctx: click.Context, format: str) -> None:
    """
    Display information about the authenticated user.
    """
    app: UserApp | ClientApp = ctx.obj
    auth_client = _create_auth_client(app)
    res = auth_client.userinfo()

    if format == "text":
        click.echo(res["preferred_username"])
    else:
        click.echo(json.dumps(res.data, indent=2))


@cli.command()
@click.pass_context
def logout(ctx: click.Context) -> None:
    """
    Log out the current user by revoking all tokens.
    """
    app: UserApp | ClientApp = ctx.obj
    app.logout()
    click.echo("Logged out successfully.")


@cli.command("list")
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
@click.pass_context
def list_registered_apis(
    ctx: click.Context, filter_roles: tuple[str, ...], per_page: int, format: str
) -> None:
    """
    List registered APIs for which the caller has a role.
    """
    app: UserApp | ClientApp = ctx.obj
    flows_client = _create_flows_client(app)

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


@cli.command()
@click.argument("service_name", type=click.Choice(["search", "groups"]))
def enrich_known(service_name: str) -> None:
    """
    Enrich a service's openapi schema with registered-api associated information.

    To be "known" a service must have a distinct config in the `services` module.
    """
    if service_name not in SERVICE_CONFIGS:
        raise click.ClickException(f"Service '{service_name}' is not a known service.")
    config = SERVICE_CONFIGS[service_name]

    orig_schema = load_openapi_schema(config["openapi_uri"])
    enriched_schema = OpenApiEnrichmentCenter(config).enrich(orig_schema)

    schema_diff = _diff(orig_schema, enriched_schema)

    click.echo(schema_diff)


def _diff(orig_schema: dict[str, t.Any], enriched_schema: dict[str, t.Any]) -> str:
    """ Produce a minimized diff between two OpenAPI schemas. """

    left = json.dumps(orig_schema, indent=2).splitlines(keepends=True)
    right = json.dumps(enriched_schema, indent=2).splitlines(keepends=True)

    diff_lines = list(Differ().compare(left, right))
    return "".join(_minimize_diff_lines(diff_lines))


def _minimize_diff_lines(lines: list[str]) -> t.Iterator[str]:
    """
    Minimize diff lines, yielding a generator of lines that should be shown.

    Lines will be printed if they:
        1. Have a "+ " or "- " prefix (indicating addition or removal)
        2. Are contextually useful are parents of added/removed lines.
    """

    ranges = _compute_diff_index_ranges(lines)

    for range_idx, (start, end) in enumerate(ranges):
        prev = ranges[range_idx - 1] if range_idx > 0 else (0, 0)

        context_lines: list[str] = []
        if start > 0:
            # Add lines of parent elements, identified by indentation changes.
            indent_level = _compute_indent_level(lines[start])
            for idx in reversed(range(prev[1] + 1, start)):
                new_level = _compute_indent_level(lines[idx])
                if new_level < indent_level:
                    context_lines.append(lines[idx])
                    indent_level = new_level

        for line in reversed(context_lines):
            yield line
        for idx in range(start, end + 1):
            yield lines[idx]


def _compute_diff_index_ranges(lines: t.Iterable[str]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    current_range = None

    for idx, line in enumerate(lines):
        if not line.startswith("  "):
            # Line is "important" (addition, removal)
            if current_range is None:
                current_range = idx, None
            else:
                current_range = current_range[0], idx

        else:
            # Line is not "important"
            if current_range is not None:
                ranges.append(current_range)
                current_range = None

    if current_range is not None:
        ranges.append(current_range)
    return ranges

def _compute_indent_level(line: str) -> int:
    return len(line[1:]) - len(line[1:].lstrip())
