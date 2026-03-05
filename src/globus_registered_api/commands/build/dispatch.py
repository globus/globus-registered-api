# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timezone

import click
import openapi_pydantic as oa

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.context import CLIContext, with_cli_context
from globus_registered_api.manifest import ComputedRegisteredAPI, RegisteredAPIManifest
from globus_registered_api.openapi import process_target
from globus_registered_api.openapi.enricher import OpenAPIEnricher
from globus_registered_api.openapi.loader import load_openapi_spec


@click.command("build")
@with_cli_context
def build_command(_ctx: CLIContext) -> None:
    """
    Build a manifest file for your registered APIs.

    Creates .globus_registered_api/manifest.json with all configured registered API
    endpoints and their specifications. The manifest.json build artifact is used
    to publish registered APIs to the Flows service.
    """
    # Load config
    config = RegisteredAPIConfig.load()

    # Load OpenAPI spec
    if isinstance(config.core.specification, str):
        openapi_spec = load_openapi_spec(config.core.specification)
        click.echo(f"Loaded OpenAPI specification from {config.core.specification}.")
    elif isinstance(config.core.specification, oa.OpenAPI):
        openapi_spec = config.core.specification
        click.echo("Loaded inline OpenAPI specification from config.")
    else:
        click.echo("Error: Invalid specification type in config.", err=True)
        raise click.Abort()

    # Enrich the specification
    enriched_spec = OpenAPIEnricher(config).enrich(openapi_spec)

    # Process each target
    registered_apis: dict[str, ComputedRegisteredAPI] = {}
    for target_config in config.targets:
        result = process_target(
            enriched_spec, target_config.specifier, config.core.base_url
        )
        registered_apis[target_config.alias] = ComputedRegisteredAPI(
            target=result.target
        )

    # Build manifest
    manifest = RegisteredAPIManifest(
        build_timestamp=datetime.now(timezone.utc),
        registered_apis=registered_apis,
    )
    click.echo("Successfully computed manifest artifact")

    # Write to disk
    manifest.commit()
    click.echo("Wrote manifest to disk (.globus_registered_api/manifest.json)")
