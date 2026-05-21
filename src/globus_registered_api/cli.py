# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json

import click
import click.exceptions
from globus_sdk import GlobusAPIError

from globus_registered_api.commands import ROOT_COMMANDS
from globus_registered_api.errors import GRACommandLineError


class ExceptionHandlingGroup(click.Group):
    """Click Group that handles GlobusAPIError exceptions."""

    def invoke(self, ctx: click.Context) -> object:
        try:
            return super().invoke(ctx)
        except GlobusAPIError as err:
            _handle_globus_api_error(err)
            return None
        except GRACommandLineError as err:
            err.click_echo()
            raise click.exceptions.Exit(code=1)


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
    raise click.exceptions.Exit(code=1)


# CLI commands
@click.group(cls=ExceptionHandlingGroup)
def cli() -> None:
    """Globus Registered API Command Line Interface."""


for command in ROOT_COMMANDS:
    cli.add_command(command)
