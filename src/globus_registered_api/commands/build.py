from datetime import datetime, timezone

import click

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.manifest import ComputedRegisteredAPI, RegisteredAPIManifest
from globus_registered_api.openapi import process_target
from globus_registered_api.openapi.enricher import OpenAPIEnricher
from globus_registered_api.openapi.loader import load_openapi_spec


@click.command("build")
def build_command() -> None:
    """
    Compute a manifest artifact to be published.
    """
    config = RegisteredAPIConfig.load()

    if isinstance(config.core.specification, str):
        spec = load_openapi_spec(config.core.specification)
        click.echo(f"Loaded OpenAPI specification from {config.core.specification}.")
    else:
        spec = config.core.specification
        click.echo("Loaded inline OpenAPI specification from config.")

    enriched_spec = OpenAPIEnricher(config).enrich(spec)

    registered_apis: dict[str, ComputedRegisteredAPI] = {}
    for target in config.targets:
        result = process_target(enriched_spec, target.specifier)
        registered_apis[target.alias] = ComputedRegisteredAPI(target=result.target)

    manifest = RegisteredAPIManifest(
        build_timestamp=datetime.now(timezone.utc),
        targets=registered_apis,
    )
    click.echo("Successfully computed manifest artifact")

    manifest.commit()
    click.echo("Wrote manifest to disk (.globus_registered_api/manifest.json)")
