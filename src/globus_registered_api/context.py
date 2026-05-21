# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import os
import typing as t
from dataclasses import dataclass
from uuid import UUID

from globus_sdk import ClientApp
from globus_sdk import GlobusApp
from globus_sdk import GlobusAppConfig
from globus_sdk import UserApp
from globus_sdk.scopes import AuthScopes
from globus_sdk.scopes import FlowsScopes
from globus_sdk.scopes import GroupsScopes
from globus_sdk.scopes import SearchScopes
from globus_sdk.token_storage import JSONTokenStorage
from globus_sdk.token_storage import TokenStorage

# Constants
NATIVE_CLIENT_ID = "5fde3f3e-78b3-4459-aea2-a91dfd9ace1a"

GLOBUS_PROFILE_ENV_VAR = "GLOBUS_PROFILE"
GLOBUS_INTERNAL_USER_ENV_VAR = "GLOBUS_INTERNAL_USER"

SCOPE_REQUIREMENTS = {
    AuthScopes.resource_server: [
        AuthScopes.openid,
        AuthScopes.profile,
        AuthScopes.email,
    ],
    GroupsScopes.resource_server: [GroupsScopes.view_my_groups_and_memberships],
    SearchScopes.resource_server: [SearchScopes.search],
    FlowsScopes.resource_server: [FlowsScopes.all],
}


@dataclass
class CLIContext:
    globus_app: GlobusApp
    profile: str | None

    @classmethod
    def from_environment(cls) -> CLIContext:
        return cls(
            globus_app=create_globus_app(),
            profile=_get_profile(),
        )


P = t.ParamSpec("P")
R = t.TypeVar("R")


def with_cli_context(
    func: t.Callable[t.Concatenate[CLIContext, P], R],
) -> t.Callable[P, R]:
    """
    Decorator to inject CLIContext into Click command functions.

    Usage:
        @click.command()
        @click.argument("MY_ARG")
        @with_cli_context
        def my_command(ctx: CLIContext, my_arg: ...):
            ...
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        cli_context = CLIContext.from_environment()
        return func(cli_context, *args, **kwargs)

    return wrapper


def _get_profile() -> str | None:
    """Get the current profile from GLOBUS_PROFILE environment variable."""
    profile = os.getenv(GLOBUS_PROFILE_ENV_VAR)
    return profile.strip() if profile else None


def is_internal_globus_user() -> bool:
    return bool(os.getenv(GLOBUS_INTERNAL_USER_ENV_VAR))


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
        config: GlobusAppConfig,
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


# Helper functions
def create_globus_app(environment: str | None = None) -> UserApp | ClientApp:
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

    config_data: dict[str, t.Any] = {"auto_redrive_gares": True}
    if environment:
        config_data["environment"] = environment

    if client_id and client_secret:
        return ClientApp(
            app_name=app_name,
            client_id=client_id,
            client_secret=client_secret,
            scope_requirements=SCOPE_REQUIREMENTS,
            config=GlobusAppConfig(**config_data),
        )
    else:
        # UserApp uses profile-aware token storage
        config_data["token_storage"] = ProfileAwareJSONTokenStorage

        return UserApp(
            app_name=app_name,
            client_id=NATIVE_CLIENT_ID,
            scope_requirements=SCOPE_REQUIREMENTS,
            config=GlobusAppConfig(**config_data),
        )
