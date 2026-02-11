# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import os
import pathlib
import sys
import typing as t
from collections.abc import Iterable
from uuid import UUID

import click
from globus_sdk import AuthClient
from globus_sdk import ClientApp
from globus_sdk import FlowsClient
from globus_sdk import GlobusAPIError
from globus_sdk import GlobusAppConfig
from globus_sdk import Scope
from globus_sdk import UserApp
from globus_sdk.token_storage import JSONTokenStorage
from globus_sdk.token_storage import TokenStorage

from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.extended_flows_client import ExtendedFlowsClient
from globus_registered_api.openapi import AmbiguousContentTypeError
from globus_registered_api.openapi import OpenAPILoadError
from globus_registered_api.openapi import TargetNotFoundError
from globus_registered_api.openapi import process_target
from globus_registered_api.openapi.enchricher import OpenAPIEnricher
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.schema_diff import diff_schema
from globus_registered_api.services import SERVICE_CONFIGS

if t.TYPE_CHECKING:
    from globus_sdk.globus_app.config import GlobusAppConfig as SDKGlobusAppConfig

# Constants
NATIVE_CLIENT_ID = "5fde3f3e-78b3-4459-aea2-a91dfd9ace1a"
GLOBUS_PROFILE_ENV_VAR = "GLOBUS_PROFILE"


def _get_profile() -> str | None:
    """Get the current profile from GLOBUS_PROFILE environment variable."""
    profile = os.getenv(GLOBUS_PROFILE_ENV_VAR)
    return profile.strip() if profile else None


def _resolve_namespace(environment: str = "production") -> str:
    """
    Resolve token storage namespace based on GLOBUS_PROFILE.

    :param environment: The Globus environment (e.g., "production", "sandbox")
    :return: A namespace string for token storage partitioning
    """
    profile = _get_profile()
    if profile:
        return f"userprofile/{environment}/{profile}"
    return "DEFAULT"


class ProfileAwareJSONTokenStorage:
    """
    TokenStorageProvider that creates JSONTokenStorage with profile-aware namespaces.

    This class implements the SDK's TokenStorageProvider protocol, allowing it to be
    passed to GlobusAppConfig's token_storage parameter. When for_globus_app is called,
    it computes the namespace based on the GLOBUS_PROFILE environment variable and
    delegates to JSONTokenStorage.for_globus_app with the computed namespace.

    This enables switching between multiple authenticated user profiles without
    logout/login cycles, matching the behavior of globus-cli.
    """

    @classmethod
    def for_globus_app(
        cls,
        *,
        app_name: str,
        config: SDKGlobusAppConfig,
        client_id: UUID | str,
        namespace: str,
    ) -> TokenStorage:
        """
        Create a JSONTokenStorage with a profile-aware namespace.

        The namespace parameter is ignored; instead, the namespace is computed
        from the GLOBUS_PROFILE environment variable.

        :param app_name: The name supplied to the GlobusApp
        :param config: The GlobusAppConfig for the GlobusApp
        :param client_id: The client_id of the GlobusApp
        :param namespace: Ignored; computed from GLOBUS_PROFILE
        :return: A JSONTokenStorage instance with profile-aware namespace
        """
        resolved_namespace = _resolve_namespace(config.environment)
        return JSONTokenStorage.for_globus_app(
            app_name=app_name,
            config=config,
            client_id=client_id,
            namespace=resolved_namespace,
        )


SCOPE_REQUIREMENTS: dict[str, str | Scope | Iterable[str | Scope]] = {
    AuthClient.scopes.resource_server: [AuthClient.scopes.openid],
    FlowsClient.scopes.resource_server: [FlowsClient.scopes.all],
}


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

    Checks for GLOBUS_REGISTERED_API_CLIENT_ID and GLOBUS_REGISTERED_API_CLIENT_SECRET.
    If both are present, creates a ClientApp for client credentials authentication.
    Otherwise, creates a UserApp with a registered native client.

    For UserApp, the token storage is profile-aware: if GLOBUS_PROFILE is set,
    tokens are stored in a separate namespace for that profile, enabling
    switching between multiple authenticated users without logout/login cycles.

    :return: A ClientApp if both environment variables are set, otherwise a UserApp
    :raises ValueError: If only one of the required environment variables is set
    """
    client_id = os.getenv("GLOBUS_REGISTERED_API_CLIENT_ID")
    client_secret = os.getenv("GLOBUS_REGISTERED_API_CLIENT_SECRET")
    app_name = "globus-registered-api-cli"

    # Validate: both or neither
    if bool(client_id) ^ bool(client_secret):
        raise ValueError(
            "Both GLOBUS_REGISTERED_API_CLIENT_ID and "
            "GLOBUS_REGISTERED_API_CLIENT_SECRET must be set, or neither."
        )

    if client_id and client_secret:
        return ClientApp(
            app_name=app_name,
            client_id=client_id,
            client_secret=client_secret,
            scope_requirements=SCOPE_REQUIREMENTS,
            config=GlobusAppConfig(auto_redrive_gares=True),
        )
    else:
        # UserApp uses profile-aware token storage
        return UserApp(
            app_name=app_name,
            client_id=NATIVE_CLIENT_ID,
            scope_requirements=SCOPE_REQUIREMENTS,
            config=GlobusAppConfig(
                auto_redrive_gares=True,
                token_storage=ProfileAwareJSONTokenStorage,
            ),
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

    When GLOBUS_PROFILE is set, shows the active profile name.
    """
    app: UserApp | ClientApp = ctx.obj
    auth_client = _create_auth_client(app)
    res = auth_client.userinfo()
    profile = _get_profile()

    if format == "text":
        username = res["preferred_username"]
        if profile:
            click.echo(f"{username} (profile: {profile})")
        else:
            click.echo(username)
    else:
        output = dict(res.data)
        if profile:
            output["profile"] = profile
        click.echo(json.dumps(output, indent=2))


@cli.command()
@click.pass_context
def logout(ctx: click.Context) -> None:
    """
    Log out the current user by revoking all tokens.

    When GLOBUS_PROFILE is set, only logs out from the active profile.
    """
    app: UserApp | ClientApp = ctx.obj
    app.logout()
    profile = _get_profile()
    if profile:
        click.echo(f"Logged out successfully from profile '{profile}'.")
    else:
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


@cli.command("get")
@click.argument("registered_api_id")
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
@click.pass_context
def get_registered_api(ctx: click.Context, registered_api_id: str, format: str) -> None:
    """
    Get a registered API by ID.
    """
    app: UserApp | ClientApp = ctx.obj
    flows_client = _create_flows_client(app)

    res = flows_client.get_registered_api(registered_api_id)

    if format == "json":
        click.echo(json.dumps(res.data, indent=2))
    else:
        click.echo(f"ID:          {res['id']}")
        click.echo(f"Name:        {res['name']}")
        click.echo(f"Description: {res['description']}")
        click.echo(f"Created:     {res['created_timestamp']}")
        click.echo(f"Updated:     {res['updated_timestamp']}")


@cli.command("update")
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
@click.pass_context
def update_registered_api(
    ctx: click.Context,
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
    app: UserApp | ClientApp = ctx.obj
    flows_client = _create_flows_client(app)

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


@cli.command("create")
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
@click.pass_context
def create_registered_api(
    ctx: click.Context,
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

    app: UserApp | ClientApp = ctx.obj
    flows_client = _create_flows_client(app)

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


# --- willdelete command group ---


@cli.group()
def willdelete() -> None:
    """Temporary commands for OpenAPI processing development."""


@willdelete.command("print-target")
@click.argument("openapi_spec", type=click.Path(exists=False))
@click.argument("method", type=click.Choice(HTTP_METHODS, case_sensitive=False))
@click.argument("route")
@click.option(
    "--content-type",
    default="*",
    help="Target content-type for request body (required if multiple exist)",
)
def willdelete_print_target(
    openapi_spec: str,
    method: str,
    route: str,
    content_type: str,
) -> None:
    """
    Print a target api, narrowed from a supplied full OpenAPI spec.

    OPENAPI_SPEC - A filepath or URL to a OpenAPI specification containing the target
        (JSON or YAML).
    ROUTE - Target API's route path (e.g., /items or /items/{item_id}).
    METHOD - Target API's HTTP method (e.g., get, post, put, delete).
    """
    try:
        target = TargetSpecifier.create(method, route, content_type)
    except ValueError as e:
        raise click.ClickException(str(e))

    try:
        result = process_target(openapi_spec, target)
    except (OpenAPILoadError, TargetNotFoundError, AmbiguousContentTypeError) as e:
        raise click.ClickException(str(e))

    click.echo(json.dumps(result.to_dict(), indent=2))


@willdelete.command("print-service-target")
@click.argument(
    "service_name",
    metavar="SERVICE_NAME",
    type=click.Choice(SERVICE_CONFIGS.keys()),
)
@click.argument(
    "method",
    metavar="METHOD",
    type=click.Choice(HTTP_METHODS, case_sensitive=False),
)
@click.argument("route")
@click.option(
    "--content-type",
    default="*",
    help="Target content-type for request body (required if multiple exist)",
)
@click.option(
    "--environment",
    type=click.Choice(
        ["sandbox", "integration", "test", "preview", "staging", "production"]
    ),
    default="production",
)
@click.option(
    "--diff-only",
    is_flag=True,
    default=False,
    help="Print only the enrichments performed on the target.",
)
def willdelete_print_service_target(
    service_name: str,
    method: str,
    route: str,
    content_type: str,
    environment: str,
    diff_only: bool,
) -> None:
    """
    Print a uniquely matched api target from a registered service's OpenAPI spec.

    SERVICE_NAME - A known service with a registered config.
    ROUTE - Target API's route path (e.g., /items or /items/{item_id}).
    METHOD - Target API's HTTP method (e.g., get, post, put, delete).
    """
    config = SERVICE_CONFIGS[service_name]

    try:
        target = TargetSpecifier.create(method, route, content_type)
    except ValueError as e:
        raise click.ClickException(str(e))

    try:
        orig_schema = load_openapi_spec(config["openapi_uri"])
        enriched_schema = OpenAPIEnricher(config, environment).enrich(orig_schema)

        enriched_target = process_target(enriched_schema, target)

        if diff_only:
            orig_target = process_target(orig_schema, target)
            click.echo(diff_schema(orig_target.to_dict(), enriched_target.to_dict()))
        else:
            click.echo(json.dumps(enriched_target.to_dict(), indent=2))

    except (OpenAPILoadError, TargetNotFoundError, AmbiguousContentTypeError) as e:
        raise click.ClickException(str(e))
