# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import typing as t
from dataclasses import dataclass

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
from globus_registered_api.openapi.selector import find_target
from globus_registered_api.rendering import prompt_selection

from .domain import ConfiguratorMenu
from .domain import ManageContext

console = Console()


class _ManualInput: ...


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


@dataclass
class ImputedSecurity:
    """
    Dynamic override of TargetSecurityConfig for display purposes.

    Represents a security definition imputed from the OpenAPI spec, not defined in
    the config.
    """

    globus_auth_scopes: list[str]


class TargetConfigurator:
    def __init__(self, context: ManageContext) -> None:
        self.config = context.config
        self.spec = context.spec
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

    @staticmethod
    def _require_targets(method: t.Callable[..., None]) -> t.Callable[..., None]:
        @functools.wraps(method)
        def wrapper(self_: TargetConfigurator, *args: t.Any, **kwargs: t.Any) -> None:
            if not self_.config.targets:
                click.echo("\nNo targets are defined.\n")
                return None
            return method(self_, *args, **kwargs)

        return wrapper

    @_require_targets
    def display_target(self, target: TargetConfig | None = None) -> None:
        if target is None:
            target = self._target_prompter.prompt_for_config()

        if not target.security.globus_auth_scope:
            if spec_scopes := self.analysis.scopes_by_target.get(target.specifier):
                # Create a copy of the target, ignoring type incompatibility for display
                #   purposes.
                target = target.model_copy()
                imputed_security = ImputedSecurity(globus_auth_scopes=spec_scopes)
                target.security = imputed_security  # type: ignore

        panel = Panel(Pretty(target, expand_all=True), title=str(target))
        console.print(panel)

    def list_targets(self) -> None:
        table = TargetSummaryTable(self.config.targets)
        table.print()

    def _get_default_description(
        self, target_specifier: TargetSpecifier, alias: str
    ) -> str:
        """
        Generate default description from OpenAPI operation or fallback.

        :param target_specifier: Target path and method
        :param alias: User-provided alias
        :return: Default description string
        """
        try:
            target_info = find_target(self.spec, target_specifier)
            return (
                target_info.operation.summary
                or target_info.operation.description
                or f"{alias}: {target_specifier.method} {target_specifier.path}"
            )
        except Exception:
            # Target not in spec (manual entry) - use fallback
            return f"{alias}: {target_specifier.method} {target_specifier.path}"

    @_require_targets
    def modify_target(self) -> None:
        target = self._target_prompter.prompt_for_config()
        target.alias = click.prompt("Target Alias", type=str, default=target.alias)
        target.description = click.prompt(
            "Description", type=str, default=target.description
        )
        globus_auth_scope = self._scope_prompter.prompt_for_existing_target(target)
        target.security.globus_auth_scope = globus_auth_scope

        self.config.targets.sort(key=lambda ta: ta.sort_key)
        self.config.commit()
        self.display_target(target)

    def add_target(self) -> None:
        target_specifier = self._target_prompter.prompt_specifier()

        click.echo(f"\nRegistering Target: {target_specifier}")
        click.echo("Provide a human friendly name like 'create-resource'.")
        target_alias = click.prompt("Target Alias", type=str)

        default_description = self._get_default_description(
            target_specifier, target_alias
        )
        description = click.prompt("Description", type=str, default=default_description)

        globus_auth_scope = self._scope_prompter.prompt_for_new_target(target_specifier)

        target = TargetConfig(
            path=target_specifier.path,
            method=target_specifier.method,
            alias=target_alias,
            description=description,
            security=TargetConfig.Security(globus_auth_scope=globus_auth_scope),
        )
        self.config.targets.append(target)

        self.config.targets.sort(key=lambda ta: ta.sort_key)
        self.config.commit()
        self.display_target(target)

    @_require_targets
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
            for target in sorted(
                spec_targets, key=lambda target: (target.path, target.method)
            )
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
    Class responsible for prompting the user to select a scope for a target.

    Scope prompting is skipped if the spec already defines scopes for the target.
    """

    def __init__(self, config: RegisteredAPIConfig, analysis: SpecAnalysis) -> None:
        self._config = config
        self._analysis = analysis

    def prompt_for_new_target(self, target_specifier: TargetSpecifier) -> str | None:
        """
        Prompt for a scope to include in a newly registered target config.

        Target scope prompting is silently skipped if the spec explicitly defines them.
        """
        if self._analysis.scopes_by_target.get(target_specifier):
            return None

        click.echo(f"\nNo Flows-supported security defined for '{target_specifier}'.")
        # TODO - link to gra docs on GlobusAuth scopes once they exist.
        click.echo("Currently the service only supports Globus Auth security.\n")
        if click.confirm("Would you like to include a Globus Auth scope?"):
            return self._prompt_scope_input()
        return None

    def prompt_for_existing_target(self, target: TargetConfig) -> str | None:
        """
        Prompt for a scope to include in an already registered target config.

        Target scope prompting is silently skipped if the spec explicitly defines them.
        """
        if self._analysis.scopes_by_target.get(target.specifier):
            # Special case -
            #   The `gra manage` command only allows attaching a scope to a target that
            #   lacks any in the specification. But since the config file can be
            #   manually edited, always respect an explicitly defined scope.
            if not target.security.globus_auth_scope:
                return None

        return self._prompt_scope_input(default=target.security.globus_auth_scope)

    def _prompt_scope_input(self, default: str | None = None) -> str | None:
        all_known_scopes = set(self._analysis.scope_strings)
        for target in self._config.targets:
            if target.security.globus_auth_scope:
                all_known_scopes.add(target.security.globus_auth_scope)

        scope_options: list[tuple[str | None | _ManualInput, str]] = [
            (None, "<None>"),
            (_ManualInput(), "<Enter a scope string>"),
        ] + [(scope, scope) for scope in sorted(all_known_scopes)]

        resp = prompt_selection("Scope", scope_options, default=default)
        if isinstance(resp, _ManualInput):
            return t.cast(str, click.prompt("Scope String", type=str))
        return resp
