# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click
from prompt_toolkit.formatted_text import AnyFormattedText
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from globus_registered_api.commands.manage.context import ManageContext
from globus_registered_api.commands.manage.target.modification import _ManualInput
from globus_registered_api.config import TargetConfig
from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import DispatchOption
from globus_registered_api.rendering import FormMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import prompt_selection
from globus_registered_api.rendering.click_utils import em
from globus_registered_api.rendering.validation.click import ClickAPIRoutePathParam
from globus_registered_api.rendering.validation.click import ClickUniqueValueParam

from ._security import SecurityExplorer

console = Console()


class TargetRegistrationMenu(FormMenu):
    """Dispatch menu for adding new roles to the configuration."""

    menu_title: str = "Add Target"

    def __init__(self, context: ManageContext) -> None:
        self.builder = TargetBuilder(context)
        self.config = context.config
        self.analyzer = context.analyzer

    @property
    def options(self) -> LabeledDispatchOptions:
        return [
            (
                self.builder.set_specifier,
                DataLabel("Select Route", self.builder.specifier),
            ),
            (self.builder.set_alias, DataLabel("Set Alias", self.builder.alias)),
            (
                self.builder.set_description,
                DataLabel("Set Description", self.builder.description),
            ),
            self._scope_option(),
        ]

    def _scope_option(self) -> tuple[DispatchOption, AnyFormattedText]:
        if scope := self.builder.globus_scope:
            scope = scope.removeprefix("urn:globus:auth:scope:")
            label = DataLabel("Set Globus Scope", scope)
            return self.builder.set_globus_scope, label

        elif self.builder.has_discoverable_security():
            return (
                self.builder.display_discovered_security,
                "Display Discovered Security",
            )

        else:
            return self.builder.set_globus_scope, "Set Globus Scope"

    def is_submittable(self) -> bool:
        return self.builder.is_buildable()

    def on_submit(self) -> None:
        alias, target_config = self.builder.build()
        self.config.targets[alias] = target_config
        self.config.commit()


class TargetBuilder:

    def __init__(self, context: ManageContext) -> None:
        self._context = context
        self._analyzer = context.analyzer
        self._config = context.config

        self.alias: str | None = None
        self.specifier: TargetSpecifier | None = None
        self.description: str | None = None
        self.globus_scope: str | None = None

        self._security_explorer: SecurityExplorer | None = None

    def set_alias(self) -> None:
        old_value = self.alias
        new_value = click.prompt(
            "Alias",
            type=ClickUniqueValueParam(list(self._config.targets.keys())),
            default=old_value,
        )
        if old_value != new_value:
            self.alias = new_value
            self._evaluate_default_description()

    def set_specifier(self) -> None:
        old_value = self.specifier

        new_value = self._prompt_specifier_from_discovered()
        if new_value is None:
            new_value = self._prompt_specifier_manual()

        alias_by_specifier = {
            target_config.specifier: alias
            for alias, target_config in self._config.targets.items()
        }
        if (alias := alias_by_specifier.get(new_value)) is not None:
            route = click.style(new_value, bold=True)
            error = f"A target already exists for the route '{em(route)}'."
            click.secho(error, fg="red")
            res = f"To modify it, select {em('<Cancel>')} then {em(alias)}.\n"
            click.echo(click.style(res, fg="yellow"))

        elif old_value != new_value:
            self.specifier = new_value
            self._evaluate_default_description()
            self._security_explorer = SecurityExplorer(self._context, new_value)

    def _prompt_specifier_from_discovered(self) -> TargetSpecifier | None:
        discovered = self._analyzer.agg_target_analyses.keys()
        existing = {tar.specifier for tar in self._config.targets.values()}

        new_discovered = sorted(discovered - existing, key=str)
        if not new_discovered:
            return None

        return prompt_selection(
            "API Route",
            [
                (None, "<Enter custom path and method>"),
                *[(specifier, str(specifier)) for specifier in new_discovered],
            ],
            default=self.specifier,
        )

    def _prompt_specifier_manual(self) -> TargetSpecifier:
        path = click.prompt("API Path", type=ClickAPIRoutePathParam())
        method_options = [(m, m) for m in HTTP_METHODS]
        method = prompt_selection("HTTP Method", method_options)
        return TargetSpecifier(path=path, method=method)

    def _evaluate_default_description(self) -> None:
        """
        Impute the target default description if no description has been
        provided, but alias and specifier have been set.

        :return: Default description string
        """
        alias, specifier, desc = self.alias, self.specifier, self.description
        if desc is not None:
            return

        elif specifier:
            analysis = self._analyzer.agg_target_analyses.get(specifier)
            if analysis and (description := analysis.description):
                self.description = description

            elif alias is not None:
                alias_default = f"{alias}: {specifier.method} {specifier.path}"
                self.description = alias_default

    def set_description(self) -> None:
        old_value = self.description
        new_value = click.prompt("Description", default=old_value)
        if old_value != new_value:
            self.description = new_value

    def set_globus_scope(self) -> None:
        old_value = self.globus_scope

        new_value = prompt_selection(
            "Scope",
            [
                (None, "<None>"),
                (_ManualInput(), "<Enter a scope string>"),
                *[(scope, scope) for scope in sorted(self._all_known_scopes())],
            ],
            default=old_value,
        )
        if new_value == old_value:
            return

        elif isinstance(new_value, _ManualInput):
            new_value = click.prompt("Globus Scope", type=str)

        if new_value != old_value:
            self.globus_scope = new_value

    def has_discoverable_security(self) -> bool:
        return (
            self._security_explorer is not None
            and self._security_explorer.has_discoverable_security()
        )

    def display_discovered_security(self) -> None:
        """
        Print globus scopes from the OpenAPI specification analysis.

        :raises ValueError: if no specifier has been set yet.
        """
        if self._security_explorer is None:
            raise RuntimeError("Requested security discovery without a route")

        panel = Panel(Pretty(self._security_explorer.rich_discovered_security))
        console.print(panel)

    def _all_known_scopes(self) -> set[str]:
        #   openapi-analyses and
        all_known_scopes = self._analyzer.agg_well_known_scopes.copy()
        #   configured targets.
        for target in self._config.targets.values():
            if scope := target.security.globus_auth_scope:
                all_known_scopes.add(scope)
        return all_known_scopes

    def is_buildable(self) -> bool:
        """
        :return: True if `build` is expected to succeed, False otherwise.
        """
        return bool(self.alias and self.specifier and self.description)

    def build(self) -> tuple[str, TargetConfig]:
        """
        Construct an alias & TargetConfig from the internally tracked state.

        :raises ValueError: if a field required for building was not populated.
        :return: alias and TargetConfig tuple
        """
        # Type-verify that alias is set.
        if (alias := self.alias) is None:
            raise ValueError("Unset TargetBuilder.alias value.")

        return alias, TargetConfig.model_validate(
            {
                "path": self.specifier.path if self.specifier else None,
                "method": self.specifier.method if self.specifier else None,
                "description": self.description,
                "security": {
                    "globus_auth_scope": self.globus_scope,
                },
            }
        )
