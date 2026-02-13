import os
import typing as t

import click
import openapi_pydantic as oa
from globus_sdk import AuthClient
from globus_sdk import GlobusApp
from prompt_toolkit import prompt
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.validation import Validator

from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.openapi.loader import OpenAPILoadError
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.rendering import prompt_selection


class OpenAPISpecPath(click.ParamType):
    name = "openapi_spec_path"

    def convert(
        self,
        value: t.Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> str:
        if not isinstance(value, str):
            self.fail(f"{value!r} is not a valid string", param, ctx)

        try:
            load_openapi_spec(value)
        except OpenAPILoadError as e:
            self.fail(str(e), param, ctx)

        return value


class OpenAPISpecPathValidator(Validator):
    def validate(self, document: Document) -> None:
        try:
            load_openapi_spec(document.text)
        except OpenAPILoadError as e:
            # TODO - Extract more specific error messaging from OpenAPILoadError
            #         will need to upstream a change into loader.py to do this.
            raise ValidationError(cursor_position=len(document.text), message=str(e))


class ClickURLParam(click.ParamType):
    name = "url"

    def convert(
        self,
        value: t.Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> str:
        if not isinstance(value, str):
            self.fail(f"{value!r} is not a valid string", param, ctx)

        if not (value.startswith("http://") or value.startswith("https://")):
            self.fail(f"{value!r} is not a valid URL", param, ctx)

        return value


@click.command("init")
@click.pass_context
def init_command(ctx: click.Context) -> None:
    """Initialize a local Registered API Repository."""
    if RegisteredAPIConfig.exists():
        click.echo("Error: Cannot re-initialize an existing repository.")
        click.echo("Please use 'globus-registered-api manage' instead.")
        raise click.Abort()
    globus_app: GlobusApp = ctx.obj
    identity_id = AuthClient(app=globus_app).userinfo()["sub"]

    click.echo("Initializing a new local registered API repository...")
    click.echo("Registered APIs leverage the OpenAPI specification.")
    click.echo("Many common frameworks, like FastAPI, will generate these for you.")
    click.echo("For more information see: https://learn.openapis.org/")
    click.echo()

    if click.confirm("Does your service have an OpenAPI specification?", default=True):
        core_config = _prompt_for_reference_core_config()
    else:
        core_config = _prompt_for_inline_core_config()

    initial_role = RoleConfig(type="identity", id=identity_id, access_level="owner")
    config = RegisteredAPIConfig(core=core_config, targets=[], roles=[initial_role])
    config.commit()

    click.echo()
    click.echo("Successfully initialized repository!")
    click.echo()
    click.echo("To start registering targets, use 'globus-registered-api manage'.")


def _prompt_for_inline_core_config() -> CoreConfig:
    click.echo("No problem, I'll need 2 pieces of basic info about it then.")
    click.echo("You can always update the OpenAPI spec later.")
    click.echo()

    # Prompt the user to fill in basic openapi.info fields
    # https://swagger.io/specification/#info-object
    click.echo("1. What is your service's name?")
    click.echo("This should be something human readable, for example, 'Globus Search'.")
    name = click.prompt("Service Name", type=str)
    click.echo()

    click.echo("2. What is the base URL for your service?")
    click.echo("This is the common http prefix for all of the API endpoints.")
    click.echo("For example, 'https://api.example.com'.")
    base_url = click.prompt("Base URL", type=ClickURLParam())

    return CoreConfig(
        base_url=base_url,
        specification=oa.OpenAPI(
            openapi="3.1.0",
            info=oa.Info(title=name, version="-1"),
            paths={},
        ),
    )


def _prompt_for_reference_core_config() -> CoreConfig:
    click.echo("Great, can I find this specification?")
    click.echo("This may be either a URL or a local filesystem path.")
    click.echo()

    spec_path = prompt(
        "Specification Location (Path or URL): ",
        completer=OpenAPISpecCompleter(),
        validator=OpenAPISpecPathValidator(),
        validate_while_typing=False,
    )
    click.echo("Looks like an OpenAPI specification, perfect.")

    openapi_spec = load_openapi_spec(spec_path)
    analysis = OpenAPISpecAnalyzer().analyze(openapi_spec)

    if len(analysis.https_servers) == 1:
        server = analysis.https_servers[0]
        click.echo(f"I found one HTTPS server in the specification: {server}.")
        if click.confirm("Should I use this as the base URL of your service?"):
            return CoreConfig(base_url=server, specification=spec_path)
        else:
            click.echo("No problem, I'll need you to tell me the base URL then.")

    elif len(analysis.https_servers) > 1:
        click.echo("I found multiple HTTPS servers in the specification:")
        for server in analysis.https_servers:
            click.echo(f"  - {server}")
        if click.confirm("Would you like to use one of these as the service base URL?"):
            server_options = [(server, server) for server in analysis.https_servers]
            selected_server = prompt_selection("Server", server_options)
            return CoreConfig(base_url=selected_server, specification=spec_path)
        else:
            click.echo("No problem, I'll need you to tell me the base URL then.")

    else:
        click.echo("I couldn't find any HTTPS servers in the specification.")
        click.echo("Please enter the base URL manually.")

    base_url = click.prompt("Base URL", type=ClickURLParam())
    return CoreConfig(base_url=base_url, specification=spec_path)


class OpenAPISpecCompleter(Completer):
    """
    Specialized Completer for OpenAPI specs.

    If the input looks like it could be a URL, do nothing.
    Otherwise, complete filesystem paths.
    """

    def __init__(self) -> None:
        self._path_completer = PathCompleter(
            expanduser=True,
            file_filter=_is_dir_or_data_file,
        )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> t.Iterable[Completion]:
        text = document.text_before_cursor

        could_input_be_http = text.startswith(
            "http://"[: len(text)]
        ) or text.startswith("https://"[: len(text)])
        if not could_input_be_http:
            yield from self._path_completer.get_completions(document, complete_event)


def _is_dir_or_data_file(filename: str) -> bool:
    if os.path.isdir(filename):
        return True

    _, ext = os.path.splitext(filename)
    return ext.lower() in {".json", ".yaml", ".yml"}
