# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

import click

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig

from .domain import PublishContext


def _get_target_by_alias(config: RegisteredAPIConfig, alias: str) -> TargetConfig:
    """
    Get target by alias or raise RuntimeError if not found.

    :param config: RegisteredAPIConfig to search
    :param alias: Target alias to find
    :return: TargetConfig matching the alias
    :raises RuntimeError: If alias not found in config
    """
    target = next((t for t in config.targets if t.alias == alias), None)
    if target is None:
        raise RuntimeError(
            f"Internal error: Target alias '{alias}' not found in config"
        )
    return target


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
    config_aliases = {target.alias for target in context.config.targets}
    manifest_aliases = set(context.manifest.registered_apis.keys())

    invalid_aliases = [
        alias
        for alias in aliases
        if alias not in config_aliases or alias not in manifest_aliases
    ]

    if invalid_aliases:
        click.echo("Error: The following target aliases are not configured:")
        for alias in invalid_aliases:
            click.echo(f"  - {alias}")
        raise click.Abort()


def publish_target(context: PublishContext, alias: str) -> None:
    """
    Publish a single target by creating or updating the registered API.

    Commits config immediately after successful publish to ensure config
    is always in sync with server state.

    :param context: PublishContext with client and data
    :param alias: The alias of the target to publish
    """
    target = _get_target_by_alias(context.config, alias)

    if target.registered_api_id is None:
        _create_target(context, alias, target)
    else:
        _update_target(context, alias, target)

    # Commit immediately after each successful publish
    context.config.commit()


def _get_description(context: PublishContext, alias: str, target: TargetConfig) -> str:
    """
    Generate description from OpenAPI operation or fallback to sensible default.

    :param context: PublishContext with manifest
    :param alias: Target alias
    :param target: Target configuration
    :return: Description string
    """
    operation = context.manifest.registered_apis[alias].target.operation
    return (
        operation.summary
        or operation.description
        or f"{alias}: {target.method} {target.path}"
    )


def _create_target(context: PublishContext, alias: str, target: TargetConfig) -> None:
    """
    Create a new registered API in Flows service.

    :param context: PublishContext with client and data
    :param alias: The alias of the target
    :param target: The target configuration
    """
    click.echo(f"Creating registered API for {alias}...")

    target_def = context.manifest.registered_apis[alias].target.to_dict()
    description = _get_description(context, alias, target)

    response = context.flows_client.create_registered_api(
        name=alias,
        description=description,
        target=target_def,
        owners=context.role_urns["owners"] or None,
        administrators=context.role_urns["administrators"] or None,
        viewers=context.role_urns["viewers"] or None,
    )

    # Store the returned ID back in config
    target.registered_api_id = UUID(response["id"])
    click.echo(f"  Created with ID: {response['id']}")


def _update_target(context: PublishContext, alias: str, target: TargetConfig) -> None:
    """
    Update an existing registered API in Flows service.

    :param context: PublishContext with client and data
    :param alias: The alias of the target
    :param target: The target configuration
    """
    if target.registered_api_id is None:
        raise RuntimeError(f"Cannot update {alias}: registered_api_id is None")

    click.echo(
        f"Updating registered API for {alias} (ID: {target.registered_api_id})..."
    )

    target_def = context.manifest.registered_apis[alias].target.to_dict()
    description = _get_description(context, alias, target)

    context.flows_client.update_registered_api(
        target.registered_api_id,
        name=alias,
        description=description,
        target=target_def,
        owners=context.role_urns["owners"] or None,
        administrators=context.role_urns["administrators"] or None,
        viewers=context.role_urns["viewers"] or None,
    )

    click.echo("  Updated successfully")
