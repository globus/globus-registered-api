# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

import click

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.errors import GRAArgumentError
from globus_registered_api.repositories.clients import GlobusClientRepository

from .domain import PublishContext


def prepare_role_urns(roles: list[RoleConfig]) -> dict[str, list[str]]:
    """
    Convert role configs to URN lists grouped by access level.

    :param roles: List of role configurations
    :return: Dict mapping access level to list of URNs
    """
    result: dict[str, list[str]] = {
        "owners": [],
        "administrators": [],
        "viewers": [],
    }

    for role in roles:
        urn = role.auth_urn
        if role.access_level == "owner":
            result["owners"].append(urn)
        elif role.access_level == "admin":
            result["administrators"].append(urn)
        elif role.access_level == "viewer":
            result["viewers"].append(urn)

    return result


def validate_aliases(context: PublishContext, aliases: list[str]) -> None:
    """
    Validate that all aliases exist in both config and manifest.

    :param context: PublishContext with config and manifest
    :param aliases: List of target aliases to validate
    :raises click.Abort: If any alias is not found
    """
    config_aliases = {
        alias
        for alias, target_config in context.config.targets.items()
        if target_config.stages == "*" or context.stage in target_config.stages
    }
    manifest_aliases = set(context.registered_apis.keys())
    allowed_aliases = config_aliases & manifest_aliases

    invalid_aliases = set(aliases) - allowed_aliases

    if invalid_aliases:
        raise GRAArgumentError(
            f"Invalid target aliases: {', '.join(invalid_aliases)}",
            allowed_aliases,
        )


def publish_target(context: PublishContext, alias: str) -> None:
    """
    Publish a single target by creating or updating the registered API.

    Commits config immediately after successful publish to ensure config
    is always in sync with server state.

    :param context: PublishContext with client and data
    :param alias: The alias of the target to publish
    """
    target_config = context.config.targets[alias]

    if alias not in context.stage_config.registered_apis:
        # Create a Registered API, storing the generated ID back into config.
        api_id = _create_target(context, alias, target_config)
        new_config = RegisteredAPIConfig(registered_api_id=api_id)

        context.stage_config.registered_apis[alias] = new_config
    else:
        # Modify the existing Registered API
        api_id = context.stage_config.registered_apis[alias].registered_api_id
        _update_target(context, api_id, alias, target_config)

    # Commit immediately after each successful publish
    context.config.commit()


def _create_target(
    context: PublishContext,
    alias: str,
    target: TargetConfig,
) -> UUID:
    """
    Create a new registered API in Flows service.

    :param context: PublishContext with client and data
    :param alias: The alias of the target
    :param target: The target configuration
    """
    click.echo(f"Creating '{alias}'...")

    # TODO - source other metadata from the manifest, not the config.
    target_def = context.registered_apis[alias].target.to_dict()
    description = context.registered_apis[alias].description

    flows_client = GlobusClientRepository.instance().flows
    response = flows_client.create_registered_api(
        name=alias,
        description=description,
        target=target_def,
        subscription_id=context.stage_config.subscription_id,
        owners=context.role_urns["owners"] or None,
        administrators=context.role_urns["administrators"] or None,
        viewers=context.role_urns["viewers"] or None,
        data_templates=target.data_templates,
        state_input_schema=target.state_input_schema,
    )
    click.echo(f"  Created with ID: {response['id']}")

    return UUID(response["id"])


def _update_target(
    context: PublishContext,
    registered_api_id: UUID,
    alias: str,
    target: TargetConfig,
) -> None:
    """
    Update an existing registered API in Flows service.

    :param context: PublishContext with client and data
    :param registered_api_id: The registered API ID
    :param alias: The alias of the target
    :param target: The target configuration
    """
    click.echo(f"Updating '{alias}' (ID: {str(registered_api_id)})...")

    # TODO - source other metadata from the manifest, not the config.
    target_def = context.registered_apis[alias].target.to_dict()
    description = context.registered_apis[alias].description

    flows_client = GlobusClientRepository.instance().flows
    flows_client.update_registered_api(
        str(registered_api_id),
        name=alias,
        description=description,
        target=target_def,
        subscription_id=context.stage_config.subscription_id,
        owners=context.role_urns["owners"] or None,
        administrators=context.role_urns["administrators"] or None,
        viewers=context.role_urns["viewers"] or None,
        data_templates=target.data_templates,
        state_input_schema=target.state_input_schema,
    )

    click.echo("  Updated successfully")
