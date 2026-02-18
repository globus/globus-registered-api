# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t

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

from .domain import ManageContext
from .domain import ManageMenuOptions

console = Console()


class TargetSummaryTable(Table):
    _console: t.ClassVar[Console] = console

    def __init__(self, targets: list[TargetConfig]) -> None:
        super().__init__(title="Target List")
        self.add_column()
        self.add_column("Alias", style="red")
        self.add_column("Path", style="magenta")
        self.add_column("Method", style="cyan")

        for idx, target in enumerate(sorted(targets, key=lambda ta: ta.sort_key)):
            self._populate_target(idx + 1, target)

    def _populate_target(self, idx: int, target_config: TargetConfig) -> None:
        self.add_row(
            str(idx),
            target_config.alias,
            target_config.path,
            target_config.method,
        )

    def print(self) -> None:
        self._console.print(self)


class TargetConfigurator:
    def __init__(self, context: ManageContext) -> None:
        self.config = context.config
        self._target_selector = _TargetSelector(context.config, context.analysis)
        self._scope_selector = _ScopeSelector(context.config, context.analysis)

    @property
    def menu_options(self) -> ManageMenuOptions:
        """The available target management subcommands."""
        return [
            ("Display Target", self.print_target),
            ("List Targets", self.list_targets),
            ("Modify Target", self.modify_target),
            ("Add Target", self.add_target),
            ("Remove Target", self.remove_target),
        ]

    def print_target(self) -> None:
        target = self._target_selector.prompt()
        panel = Panel(
            Pretty(target, expand_all=True),
            title=str(target),
        )
        console.print(panel)

    def list_targets(self) -> None:
        table = TargetSummaryTable(self.config.targets)
        table.print()

    def modify_target(self) -> None:
        target = self._target_selector.prompt()
        target.alias = click.prompt("Target Alias", type=str, default=target.alias)
        target.scope_strings = self._scope_selector.prompt(target)
        self.config.commit()

    def add_target(self) -> None:
        target_specifier = self._target_selector.prompt_specifier()

        click.echo(f"\nRegistering Target: {target_specifier}")
        click.echo("Provide a human friendly name like 'create-resource'.")
        target_alias = click.prompt("Target Alias", type=str)
        scope_strings = self._scope_selector.prompt(target_specifier)

        target_config = TargetConfig(
            path=target_specifier.path,
            method=target_specifier.method,
            alias=target_alias,
            scope_strings=scope_strings,
        )

        self.config.targets.append(target_config)
        self.config.commit()

    def remove_target(self) -> None:
        target = self._target_selector.prompt()
        self.config.targets.remove(target)
        self.config.commit()


class _TargetSelector:
    def __init__(self, config: RegisteredAPIConfig, analysis: SpecAnalysis) -> None:
        self._config = config
        self._analysis = analysis

    def prompt(self) -> TargetConfig:
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
        click.echo("Enter the path and method for the target you want to register.")
        path = click.prompt("Path", type=str)
        method_options = [(method, method) for method in HTTP_METHODS]
        method = prompt_selection("Method", method_options)
        return TargetSpecifier(path=path, method=method)


class _ScopeSelector:
    def __init__(self, config: RegisteredAPIConfig, analysis: SpecAnalysis) -> None:
        self._config = config
        self._analysis = analysis

    def prompt(self, target: TargetSpecifier | TargetConfig) -> list[str]:
        """
        Prompt the user to select one or more scope strings for a target.
        """
        if isinstance(target, TargetSpecifier):
            defaults = self._analysis.scopes_by_target.get(target, [])
        else:
            defaults = target.scope_strings

        possible_scopes = self._all_scopes()
        for scope in possible_scopes:
            if scope.endswith(":all") and scope not in defaults:
                defaults.append(scope)

        scope_options = [(scope, scope) for scope in possible_scopes]
        return prompt_multiselection(
            "Scope",
            scope_options,
            defaults=defaults,
            custom_input=True,
        )

    def _all_scopes(self) -> list[str]:
        """Get the set of all scope strings from the spec and config."""
        scope_strings = set(self._analysis.scope_strings)
        for target in self._config.targets:
            for scope in target.scope_strings:
                scope_strings.add(scope)
        return sorted(scope_strings)
