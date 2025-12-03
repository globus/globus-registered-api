# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
import os

import click
from globus_sdk import AuthClient
from globus_sdk import ClientApp
from globus_sdk import UserApp

RAPI_NATIVE_CLIENT_ID = "9dc7dfff-cfe8-4339-927b-28d29e1b2f42"


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
            app_name=app_name, client_id=client_id, client_secret=client_secret
        )
    else:
        return UserApp(app_name=app_name, client_id=RAPI_NATIVE_CLIENT_ID)


def _create_auth_client(app: UserApp | ClientApp) -> AuthClient:
    """
    Create an AuthClient for the given app.

    :param app: A Globus app instance to use for authentication
    :return: An AuthClient configured with the provided app
    """
    return AuthClient(app=app)


@click.group()
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
