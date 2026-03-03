# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

import click
from globus_sdk import GlobusHTTPResponse


def echo_registered_api(response: GlobusHTTPResponse, format: str) -> None:
    if format == "json":
        click.echo(json.dumps(response.data, indent=2))
    else:
        click.echo(f"ID:             {response['id']}")
        click.echo(f"Name:           {response['name']}")
        click.echo(f"Description:    {response['description']}")
        _echo_list("Owners:         ", response["roles"]["owners"])
        _echo_list("Administrators: ", response["roles"]["administrators"])
        _echo_list("Viewers:        ", response["roles"]["viewers"])
        click.echo(f"Created:        {response['created_timestamp']}")
        click.echo(f"Updated:        {response['updated_timestamp']}")


def _echo_list(key: str, items: list[str]) -> None:
    """
    Print a list of items, indented to a common length (the length of the key).
    """

    if not items:
        click.echo(f"{key}")
        return

    # Print the first item prefixed with the key.
    prefix = key
    for item in items:
        click.echo(f"{prefix}{item}")
        # Print subsequent items prefixed with spaces to align with the first item.
        prefix = " " * len(key)
