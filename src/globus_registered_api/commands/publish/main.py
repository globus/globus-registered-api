# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.config import GRAConfig
from globus_registered_api.errors import GRAArgumentError
from globus_registered_api.manifest import GRAManifest
from globus_registered_api.repositories.clients import GlobusClientRepository

from .domain import PublishContext
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
    "--stage",
    required=False,
    help="The repo-defined stage to build. Required in multi-stage repos.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt and proceed with publish.",
)
def publish_command(
    target_aliases: tuple[str, ...],
    stage: str | None,
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
    config = GRAConfig.load()
    stage = _verify_stage(config, stage)
    manifest = GRAManifest.load()

    # Configure globus environments.
    globus_environment = config.stages[stage].globus_environment
    GlobusClientRepository.instance().environment = globus_environment

    # Create publish context
    publish_context = PublishContext(
        config=config,
        manifest=manifest,
        stage=stage,
        role_urns=prepare_role_urns(config.stages[stage].roles),
    )

    # Determine which targets to publish
    registered_apis = manifest.registered_apis[stage]
    if target_aliases:
        aliases_to_publish: list[str] = list(target_aliases)
    else:
        # Default to all targets if none specified
        aliases_to_publish = list(registered_apis.keys())

    # Validate aliases
    validate_aliases(publish_context, aliases_to_publish)

    # Display list of targets and prompt for confirmation
    if not yes:
        click.echo("The following targets will be published:")
        for alias in aliases_to_publish:
            if alias in publish_context.stage_config.registered_apis:
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


def _verify_stage(config: GRAConfig, stage: str | None) -> str:
    if stage is None:
        if len(config.stages) == 1:
            return next(iter(config.stages.keys()))
        raise GRAArgumentError(
            "Missing `--stage` option (required in a multi-stage repo).",
            allowed_values=config.stages.keys(),
        )

    elif stage in config.stages:
        return stage

    raise GRAArgumentError(
        f"Invalid stage option: '{stage}'",
        allowed_values=config.stages.keys(),
    )
