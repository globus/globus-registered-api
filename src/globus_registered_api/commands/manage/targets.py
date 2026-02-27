# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi import SpecAnalysis
from globus_registered_api.rendering import prompt_multiselection
from globus_registered_api.rendering import prompt_selection

from .domain import ConfiguratorMenu
from .domain import ManageContext

console = Console()


class TargetSummaryTable(Table):
    def __init__(self, targets: list[TargetConfig]) -> None:
        super().__init__(title="Target List")
        self.add_column()
        self.add_column("Alias", style="red")
        self.add_column("Path", style="magenta")
        self.add_column("Method", style="cyan")

        for target in sorted(targets, key=lambda ta: ta.sort_key):
            self.add_row(
                str(self.row_count + 1),
                target.alias,
                target.path,
                target.method,
            )

    def print(self) -> None:
        console.print(self)


class TargetConfigurator:
    def __init__(self, context: ManageContext) -> None:
        self.config = context.config
        self.analysis = context.analysis
        self._target_prompter = _TargetPrompter(context.config, context.analysis)
        self._scope_prompter = _TargetScopePrompter(context.config, context.analysis)

    @property
    def menu_options(self) -> ConfiguratorMenu:
        """The available target management subcommands."""
        return [
            (self.display_target, "Display Target"),
            (self.list_targets, "List Targets"),
            (self.modify_target, "Modify Target"),
            (self.add_target, "Add Target"),
            (self.remove_target, "Remove Target"),
        ]

    def display_target(self, target: TargetConfig | None = None) -> None:
        if target is None:
            target = self._target_prompter.prompt_for_config()

        if not target.scope_strings:
            # Impute scopes from the spec analysis if they aren't defined explicitly.
            if spec_scopes := self.analysis.scopes_by_target.get(target.specifier):
                target = target.model_copy()
                target.scope_strings = [f"<Imputed> {scope}" for scope in spec_scopes]

        panel = Panel(
            Pretty(target, expand_all=True),
            title=str(target),
        )
        console.print(panel)

    def list_targets(self) -> None:
        table = TargetSummaryTable(self.config.targets)
        table.print()

    def modify_target(self) -> None:
        target = self._target_prompter.prompt_for_config()
        target.alias = click.prompt("Target Alias", type=str, default=target.alias)
        target.scope_strings = self._scope_prompter.prompt_for_existing_target(target)
        self.config.targets.sort(key=lambda ta: ta.sort_key)
        self.config.commit()
        self.display_target(target)

    def add_target(self) -> None:
        target_specifier = self._target_prompter.prompt_specifier()

        click.echo(f"\nRegistering Target: {target_specifier}")
        click.echo("Provide a human friendly name like 'create-resource'.")
        target_alias = click.prompt("Target Alias", type=str)

        scope_strings = self._scope_prompter.prompt_for_new_target(target_specifier)

        target = TargetConfig(
            path=target_specifier.path,
            method=target_specifier.method,
            alias=target_alias,
            scope_strings=scope_strings,
        )
        self.config.targets.append(target)
        self.config.targets.sort(key=lambda ta: ta.sort_key)
        self.config.commit()
        self.display_target(target)

    def remove_target(self) -> None:
        target = self._target_prompter.prompt_for_config()
        self.config.targets.remove(target)
        self.config.commit()


class _TargetPrompter:
    def __init__(self, config: RegisteredAPIConfig, analysis: SpecAnalysis) -> None:
        self._config = config
        self._analysis = analysis

    def prompt_for_config(self) -> TargetConfig:
        """
        Prompt for a target config from the existing config.
        """
        target_options = [
            (target, str(target))
            for target in sorted(self._config.targets, key=lambda ta: ta.sort_key)
        ]
        return prompt_selection("Target", target_options)

    def prompt_specifier(self) -> TargetSpecifier:
        """
        Prompt for a target specifier (a method and path).

        Target specifiers are derived from the OpenAPI spec. An escape hatch however
        allows inputting explicit method and path strings in the case that the spec
        is missing targets or targets are being registered multiple times.
        """
        selection = self._prompt_specifier_from_spec()
        if selection is not None:
            return selection

        return self._prompt_specifier_from_user_input()

    def _prompt_specifier_from_spec(self) -> TargetSpecifier | None:
        """
        Prompt for a target specifier that exists in the OpenAPI spec but isn't already
        registered in the config.
        """

        configured_specifiers = {target.specifier for target in self._config.targets}
        spec_targets = set(self._analysis.targets) - configured_specifiers
        if not spec_targets:
            return None

        target_options: list[tuple[TargetSpecifier | None, str]] = [
            (None, "<Enter custom path and method>")
        ] + [
            (target, f"{target.path} ({target.method})")
            for target in sorted(spec_targets, key=lambda target: target.path)
        ]
        return prompt_selection("Target", target_options)

    def _prompt_specifier_from_user_input(self) -> TargetSpecifier:
        """
        Prompt for a target specifier by explicitly entering a path and method.
        """

        click.echo("Enter the path and method for the target you want to register.")
        path = click.prompt("Path", type=str)

        method_options = [(m, m) for m in HTTP_METHODS]
        method = prompt_selection("Method", method_options)
        return TargetSpecifier(path=path, method=method)


class _TargetScopePrompter:
    """
    Class responsible for prompting the user to select scopes for a target.

    Scope prompting is skipped if the spec already defines scopes for the target.
    """

    def __init__(self, config: RegisteredAPIConfig, analysis: SpecAnalysis) -> None:
        self._config = config
        self._analysis = analysis

    def prompt_for_new_target(self, target_specifier: TargetSpecifier) -> list[str]:
        """
        Prompt for scopes to include in a newly registered target config.

        Target scope prompting is silently skipped if the spec explicitly defines them.
        """
        if self._analysis.scopes_by_target.get(target_specifier):
            return []

        click.echo(
            f"\nThe {target_specifier} OpenAPI specification doesn't define any "
            "Globus Auth scopes."
        )
        # TODO - link to gra docs on GlobusAuth scopes once they exist.
        if not click.confirm("Would you like to register any?", default=True):
            return []

        all_scopes = self._all_scopes()
        return prompt_multiselection(
            "Scope",
            [(scope, scope) for scope in sorted(all_scopes)],
            defaults=[scope for scope in all_scopes if scope.endswith(":all")],
            custom_input=True,
        )

    def prompt_for_existing_target(self, target: TargetConfig) -> list[str]:
        """
        Prompt for scopes to include in an already registered target config.

        Target scope prompting is silently skipped if the spec explicitly defines them.
        """
        if self._analysis.scopes_by_target.get(target.specifier):
            # Special case -
            #   The `gra manage` command only allows attaching scopes to targets that
            #   lack them in the specification. But since the config file can be
            #   manually edited; always respect an explicitly defined scope list.
            if not target.scope_strings:
                return []

        return prompt_multiselection(
            "Scope",
            [(scope, scope) for scope in sorted(self._all_scopes())],
            defaults=target.scope_strings,
            custom_input=True,
        )

    def _all_scopes(self) -> set[str]:
        """Get the set of all scope strings between the spec and config."""
        scope_strings = set(self._analysis.scope_strings)
        for target in self._config.targets:
            scope_strings.update(target.scope_strings)
        return scope_strings
