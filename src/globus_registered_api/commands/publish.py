# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from uuid import UUID

import click
from globus_sdk import GlobusApp

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api.clients import create_flows_client
from globus_registered_api.config import RegisteredAPIConfig, TargetConfig
from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context
from globus_registered_api.manifest import RegisteredAPIManifest, ComputedRegisteredAPI


@click.command
@click.option(
    "--target-alias",
    "target_aliases",
    multiple=True,
    required=False
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@with_cli_context
def publish_command(ctx: CLIContext, target_aliases: list[str], yes: bool) -> None:
    """
    Publish one or more targets to Globus Flows as Registered APIs.
    """
    config = RegisteredAPIConfig.load()
    if not target_aliases:
        target_aliases = [target.alias for target in config.targets]
    target_aliases = sorted(target_aliases)

    manager = _FlowsRegisteredAPIManager(
        globus_app=ctx.globus_app,
        config=config,
        manifest=RegisteredAPIManifest.load(),
    )
    manager.validate_target_aliases(target_aliases)

    click.echo(f"Preparing to publish {len(target_aliases)} following targets:")
    click.echo("\n".join(f"  - {alias}" for alias in target_aliases))
    if not yes and not click.confirm("Would you like to proceed?", default=False):
        click.echo("Aborting publish.")
        raise click.Abort()

    for target_alias in target_aliases:
        manager.publish(target_alias)
    config.commit()


class _FlowsRegisteredAPIManager:
    def __init__(
        self,
        globus_app: GlobusApp,
        config: RegisteredAPIConfig,
        manifest: RegisteredAPIManifest,
    ) -> None:
        self.flows = create_flows_client(globus_app)
        self._config = config
        self._config_index = {target.alias: target for target in config.targets}
        self._manifest = manifest

        self._owners = [role.auth_urn for role in config.roles if role.access_level == "owner"]
        self._administrators = [role.auth_urn for role in config.roles if role.access_level == "administrator"]
        self._viewers = [role.auth_urn for role in config.roles if role.access_level == "viewer"]


    def publish(self, target_alias: str) -> None:
        registered_api_id = self._config_index[target_alias].registered_api_id
        if registered_api_id:
            self._update(target_alias, registered_api_id)
        else:
            self._create(target_alias)

    def _create(self, target_alias: str) -> None:
        target_config = self._config_index[target_alias]
        target_manifest = self._manifest.targets[target_alias]

        click.echo(f"Creating {target_alias} in flows...")
        result = self.flows.create_registered_api(
            name = target_config.alias,
            description=f"GRA CLI-managed Registered API.",
            target=target_manifest.target.to_dict(),
            owners=self._owners,
            administrators=self._administrators,
            viewers=self._viewers,
        )
        click.echo(f"Successfully created Registered API with ID {result['id']}.")
        target_config.registered_api_id = UUID(result["id"])

    def _update(self, target_alias: str, registered_api_id: UUID) -> None:
        target_config = self._config_index[target_alias]
        target_manifest = self._manifest.targets[target_alias]

        click.echo(f"Updating {target_alias} in flows... (id={registered_api_id})")
        self.flows.update_registered_api(
            registered_api_id=registered_api_id,
            name=target_config.alias,
            target=target_manifest.target.to_dict(),
            owners=self._owners,
            administrators=self._administrators,
            viewers=self._viewers,
        )
        click.echo(f"Successfully updated Registered API with ID {registered_api_id}.")

    def validate_target_aliases(self, target_aliases: list[str]) -> None:
        """
        Validate that the provided target aliases are valid and exist in the config and manifest.

        :param target_aliases: List of target aliases to validate
        :raises Abort: If any target alias or missing from the config/manifest
        """
        missing_config = [alias for alias in target_aliases if alias not in self._config_index]
        missing_manifest = [alias for alias in target_aliases if alias not in self._manifest.targets]

        if missing_config or missing_manifest:
            if missing_config:
                click.echo(f"Error: The following target aliases are not configured:")
                click.echo("\n".join(f"  - {alias}" for alias in missing_config))
            if missing_manifest:
                click.echo(f"Error: The following target aliases are not manifested:")
                click.echo("\n".join(f"  - {alias}" for alias in missing_manifest))
            raise click.Abort()
