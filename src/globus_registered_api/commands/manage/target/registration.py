# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click
from prompt_toolkit.formatted_text import AnyFormattedText

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
from globus_registered_api.rendering.validation.click import ClickUniqueValueParam


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

        elif self._well_known_scopes_exist_in_openapi():
            return self.builder.print_openapi_scopes, "Print Globus Scopes (OpenAPI)"

        else:
            return self.builder.set_globus_scope, "Set Globus Scope"

    def _well_known_scopes_exist_in_openapi(self) -> bool:
        analysis = self.analyzer.agg_target_analyses.get(self.builder.specifier)
        return bool(analysis and analysis.well_known_scopes)

    def is_submittable(self) -> bool:
        return bool(
            self.builder.alias and self.builder.specifier and self.builder.description
        )

    def on_submit(self) -> None:
        alias, target_config = self.builder.build()
        self.config.targets[alias] = target_config
        self.config.commit()


class TargetBuilder:

    def __init__(self, context: ManageContext) -> None:
        self._analyzer = context.analyzer
        self._config = context.config

        self.alias: str | None = None
        self.specifier: TargetSpecifier | None = None
        self.description: str | None = None
        self.globus_scope: str | None = None

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

        new_value = self._prompt_specifier_from_imputed()
        if new_value is None:
            new_value = self._prompt_specifier_manual()

        if old_value != new_value:
            self.specifier = new_value
            self._evaluate_default_description()

    def _prompt_specifier_from_imputed(self) -> TargetSpecifier | None:
        imputed = self._analyzer.agg_target_analyses.keys()
        existing = {tar.specifier for tar in self._config.targets.values()}

        new_imputed = sorted(imputed - existing, key=str)
        if not new_imputed:
            return None

        return prompt_selection(
            "API Route",
            [
                (None, "<Enter custom path and method>"),
                *[(specifier, str(specifier)) for specifier in new_imputed],
            ],
            default=self.specifier,
        )

    def _prompt_specifier_manual(self) -> TargetSpecifier:
        path = click.prompt("API Path", type=str)
        method_options = [(m, m) for m in HTTP_METHODS]
        method = prompt_selection("HTTP Method", method_options)
        # TODO - prevent registering a duplicate here as well.
        return TargetSpecifier(path=path, method=method)

    def _evaluate_default_description(self) -> None:
        """
        Impute the target default description if no description has been
        provided, but alias and specifier have been set.

        :return: Default description string
        """
        alias, specifier, desc = self.alias, self.specifier, self.description
        if desc is not None or not (alias and specifier):
            return

        analysis = self._analyzer.agg_target_analyses.get(specifier)
        if analysis and (description := analysis.description):
            self.description = description
        else:
            self.description = f"{alias}: {specifier.method} {specifier.path}"

    def set_description(self) -> None:
        old_value = self.description
        new_value = click.prompt("Description", default=old_value)
        if old_value != new_value:
            self.description = new_value

    def set_globus_scope(self):
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

    def print_openapi_scopes(self) -> None:
        # TODO - error handling? This is gated by the usage site but that's a
        #   bad code smell.
        analysis = self._analyzer.agg_target_analyses[self.specifier]
        scopes = analysis.well_known_scopes

        s = "s" if len(scopes) > 1 else ""
        click.echo(f"The OpenAPI Specification defines {len(scopes)} Globus Scope{s}:")
        for scope in scopes:
            click.echo(f"  - {scope}")
        click.echo()

    def _all_known_scopes(self) -> set[str]:
        #   openapi-analyses and
        all_known_scopes = self._analyzer.agg_well_known_scopes.copy()
        #   configured targets.
        for target in self._config.targets.values():
            if scope := target.security.globus_auth_scope:
                all_known_scopes.add(scope)
        return all_known_scopes

    def build(self) -> tuple[str, TargetConfig]:
        target_config = TargetConfig(
            path=self.specifier.path,
            method=self.specifier.method,
            description=self.description,
        )
        if self.globus_scope:
            target_config.security = TargetConfig.Security(
                globus_auth_scope=self.globus_scope
            )

        return self.alias, target_config
