# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
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

from globus_registered_api.commands import ROOT_COMMANDS
from globus_registered_api.context import CLIContext

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
    else:
        msg = json.dumps(err.raw_json, indent=2)
        click.secho(msg, fg="yellow", err=True)
    sys.exit(1)


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


# CLI commands
@click.group(cls=ExceptionHandlingGroup)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Globus Registered API Command Line Interface."""
    ctx.obj = CLIContext(
        globus_app=_create_globus_app(),
        profile=_get_profile(),
    )


for command in ROOT_COMMANDS:
    cli.add_command(command)
