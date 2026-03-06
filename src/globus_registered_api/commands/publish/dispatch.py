# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.clients import create_flows_client
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context
from globus_registered_api.manifest import RegisteredAPIManifest

from .domain import PublishContext
from .publisher import _get_target_by_alias
from .publisher import prepare_role_urns
from .publisher import publish_target
from .publisher import validate_aliases


@click.command("publish")
@click.option(
    "--target-alias",
    "target_aliases",
    multiple=True,
    help="Publish only the specified target(s). Can be specified multiple times.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt and proceed with publish.",
)
@with_cli_context
def publish_command(
    ctx: CLIContext,
    target_aliases: tuple[str, ...],
    yes: bool,
) -> None:
    """
    Publish registered APIs to Flows service.

    Creates new registered APIs for targets without IDs, or updates existing
    registered APIs for targets that have already been published.

    The manifest file must exist before publishing. Run 'gra build' first to
    generate it.
    """
    # Load config and manifest
    config = RegisteredAPIConfig.load()
    manifest = RegisteredAPIManifest.load()

    # Create publish context
    flows_client = create_flows_client(ctx.globus_app)
    role_urns = prepare_role_urns(config.roles)
    publish_context = PublishContext(
        config=config,
        manifest=manifest,
        flows_client=flows_client,
        role_urns=role_urns,
    )

    # Determine which targets to publish
    if target_aliases:
        aliases_to_publish: list[str] = list(target_aliases)
    else:
        # Default to all targets if none specified
        aliases_to_publish = [t.alias for t in config.targets]

    # Validate aliases
    validate_aliases(publish_context, aliases_to_publish)

    # Display list of targets and prompt for confirmation
    if not yes:
        click.echo("The following targets will be published:")
        for alias in aliases_to_publish:
            target = _get_target_by_alias(config, alias)
            if target.registered_api_id:
                click.echo(f"  - {alias} (update)")
            else:
                click.echo(f"  - {alias} (create)")

        if not click.confirm("Would you like to proceed?"):
            click.echo("Aborting publish.")
            raise click.Abort()

    # Publish each target
    for alias in aliases_to_publish:
        publish_target(publish_context, alias)

    click.echo(f"\nSuccessfully published {len(aliases_to_publish)} target(s).")
