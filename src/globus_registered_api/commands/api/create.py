# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib

import click

from globus_registered_api.commands.api._common import echo_registered_api
from globus_registered_api.repositories.clients import GlobusClientRepository


@click.command("create")
@click.argument("name")
@click.option(
    "--target",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="Filepath to a JSON object containing the target definition",
)
@click.option(
    "--description",
    required=True,
    help="Description for the registered API",
)
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
    "--subscription-id",
    required=True,
    help="Subscription ID that grants access to registered APIs",
)
@click.option(
    "--data-templates",
    "data_templates_path",
    hidden=True,
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="A path to a file containing a JSON-formatted data template.",
)
@click.option(
    "--state-input-schema",
    "state_input_schema_path",
    hidden=True,
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="A path to a file containing a JSON-formatted state input schema.",
)
@click.option(
    "--format", "format_", type=click.Choice(["json", "text"]), default="text"
)
def create_command(
    target: pathlib.Path,
    name: str,
    description: str,
    subscription_id: str,
    owners: tuple[str, ...],
    administrators: tuple[str, ...],
    viewers: tuple[str, ...],
    format_: str,
    data_templates_path: pathlib.Path | None,
    state_input_schema_path: pathlib.Path | None,
) -> None:
    """
    Create a new registered API from an OpenAPI specification.

    Extracts a target endpoint from an OpenAPI spec and registers it with
    the Flows service.

    NAME - Name of the new registered API.

    Example:

    \b
        gra api create "My API" --target ./target.json --description "My API" \\
            --subscription-id 00000000-e5f6-4a5b-8c9d-0e1f2a3b4c5d
    """
    flows_client = GlobusClientRepository.instance().flows

    target_content = json.loads(target.read_text())
    data_templates = {}
    if data_templates_path is not None:
        data_templates = json.loads(data_templates_path.read_text())
    state_input_schema = {}
    if state_input_schema_path is not None:
        state_input_schema = json.loads(state_input_schema_path.read_text())
    res = flows_client.create_registered_api(
        name=name,
        description=description,
        target=target_content,
        subscription_id=subscription_id,
        owners=list(owners),
        administrators=list(administrators),
        viewers=list(viewers),
        data_templates=data_templates or None,
        state_input_schema=state_input_schema or None,
    )

    echo_registered_api(res, format_)
