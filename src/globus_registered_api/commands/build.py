# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from datetime import timezone

import click

from globus_registered_api.config import GRAConfig
from globus_registered_api.manifest import ComputedRegisteredAPI
from globus_registered_api.manifest import GRAManifest
from globus_registered_api.openapi import process_target
from globus_registered_api.openapi.enricher import OpenAPIEnricher
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.repositories.clients import GlobusClientRepository


@click.command("build")
def build_command() -> None:
    """
    Build a manifest file for your registered APIs.

    Creates .globus_registered_api/manifest.json with all configured registered API
    endpoints and their specifications. The manifest.json build artifact is used
    to publish registered APIs to the Flows service.
    """
    # Load config
    config = GRAConfig.load()

    registered_apis = {
        stage: _compute_registered_apis_for_stage(config, stage)
        for stage in config.stages.keys()
    }

    # Build manifest
    manifest = GRAManifest(
        build_timestamp=datetime.now(timezone.utc),
        registered_apis=registered_apis,
    )
    click.echo("Successfully computed manifest artifact")

    # Write to disk
    manifest.commit()
    click.echo("Wrote manifest to disk:")
    click.echo(f"  {manifest.path().absolute()}")


def _compute_registered_apis_for_stage(
    config: GRAConfig, stage: str
) -> dict[str, ComputedRegisteredAPI]:
    stage_config = config.stages[stage]
    GlobusClientRepository.instance().environment = stage_config.globus_environment

    # Load OpenAPI spec
    openapi_spec = load_openapi_spec(stage_config.specification)

    # Enrich the specification
    enriched_spec = OpenAPIEnricher(config, stage).enrich(openapi_spec)

    # Process each target
    registered_apis: dict[str, ComputedRegisteredAPI] = {}
    for alias, target_config in config.targets.items():
        if target_config.stages == "*" or stage in target_config.stages:
            result = process_target(enriched_spec, target_config.specifier)
            registered_apis[alias] = ComputedRegisteredAPI(
                target=result.target, description=target_config.description
            )
    return registered_apis
