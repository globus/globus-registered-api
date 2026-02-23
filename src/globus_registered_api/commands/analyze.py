import click

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.openapi.loader import load_openapi_spec


@click.command("analyze")
def analyze_command() -> None:
    """
    Analyze a target definition for potential issues before publishing.

    This command is not yet implemented.
    """
    config = RegisteredAPIConfig.load()
    if isinstance(config.core.specification, str):
        spec = load_openapi_spec(config.core.specification)
    else:
        spec = config.core.specification

    analysis = OpenAPISpecAnalyzer().analyze(spec)
    click.echo("Analyzed OpenAPI specification.")

    for target_specifier, scopes in analysis.scopes_by_target.items():
        click.echo(f"{target_specifier.method} {target_specifier.path}: {len(scopes)}")
