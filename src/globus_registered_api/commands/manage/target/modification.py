# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import click
from prompt_toolkit.formatted_text import AnyFormattedText
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from globus_registered_api.rendering import BACK_SENTINEL
from globus_registered_api.rendering import ControlSignal
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import DispatchOption
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import prompt_selection

from ..context import ManageContext
from ._security import SecurityExplorer

console = Console()


class _ManualInput: ...


class TargetModificationMenu(DispatchMenu):
    """
    Dispatch menu for a single selected target.

    Menu Options:
      * Display Target
      * Modify Alias
      * Modify Description
      * Modify/Add Globus Scope
        * Note: if the OpenAPI spec has discoverable globus security already,
                this is replaced by a "Display Discovered Security" option.
      * Remove Target
    """

    def __init__(self, context: ManageContext, alias: str) -> None:
        self.config = context.config
        self.analyzer = context.analyzer

        self.modifier = TargetModifier(context, alias)
        self.target_config = context.config.targets[alias]

    @property
    def menu_title(self) -> str:
        # Reference the modifier's attribute in case it gets changed.
        return f"'{self.modifier.alias}'"

    @property
    def options(self) -> LabeledDispatchOptions:
        modify_alias_label = DataLabel("Modify Alias", self.modifier.alias)

        description = self.target_config.description
        if len(description) > 30:
            description = description[:27] + "..."
        modify_desc_label = DataLabel("Modify Description", description)

        return [
            (self.modifier.display_target, "Display Target"),
            (self.modifier.modify_alias, modify_alias_label),
            (self.modifier.modify_description, modify_desc_label),
            self._scope_option(),
            (self.modifier.remove_target, "Remove Target"),
        ]

    def _scope_option(self) -> tuple[DispatchOption, AnyFormattedText]:
        if scope := self.target_config.security.globus_auth_scope:
            scope = scope.removeprefix("urn:globus:auth:scope:")
            label = DataLabel("Modify Globus Scope", scope)
            return self.modifier.modify_scope, label

        elif self.modifier.security_explorer.has_discoverable_security():
            return (
                self.modifier.display_discovered_security,
                "Display Discovered Security",
            )

        else:
            return self.modifier.modify_scope, "Add Globus Scope"

    class LazyLoader:
        """
        Target Modification Menu lazy loader.

        Customizes equality checks without actually instantiating the menu.
        Custom equality matching is required for DispatchMenu breadcrumbs.
        """

        def __init__(self, context: ManageContext, alias: str) -> None:
            self._context = context
            self.alias = alias

        def __call__(self) -> TargetModificationMenu:
            return TargetModificationMenu(self._context, self.alias)

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, TargetModificationMenu.LazyLoader)
                and self.alias == other.alias
            )


class TargetModifier:
    def __init__(
        self,
        context: ManageContext,
        alias: str,
    ) -> None:
        self.context = context
        self.analyzer = context.analyzer
        self.config = context.config
        self.alias = alias
        self.target_config = self.config.targets[alias]
        self.security_explorer = SecurityExplorer.for_config(
            context, self.target_config
        )

    def display_target(self) -> None:
        """
        Print a 'pretty' version of the target to stdout.
        """
        target_config = self.target_config
        if not target_config.security.globus_auth_scope:
            if self.security_explorer.has_discoverable_security():
                target_config = target_config.model_copy(deep=True)
                security = self.security_explorer.rich_discovered_security
                target_config.security = security

        panel = Panel(Pretty(target_config, expand_all=True), title=self.alias)
        console.print(panel)

    def remove_target(self) -> ControlSignal | None:
        # Warn if any stages have registered apis deployed for this target.
        existing_registered_apis = {}
        for stage, stage_config in self.config.stages.items():
            if ra_id := stage_config.registered_apis.get(self.alias):
                existing_registered_apis[stage] = ra_id

        if existing_registered_apis:
            s = "s" if len(existing_registered_apis) > 1 else ""
            click.secho(
                f"[Warning] {len(existing_registered_apis)} stage{s} have"
                f"Registered APIs published for this target:",
                fg="yellow",
            )
            for stage, ra_id in existing_registered_apis.items():
                click.secho(f"  - {stage}: {str(ra_id)}", fg="yellow")
            click.secho("Removing the config will orphan those APIs.", fg="yellow")

        if not click.confirm(f"Do you really want to remove '{self.alias}'?"):
            click.echo("Removal Aborted.\n")
            return None

        # 1. Delete alias from target registry.
        del self.config.targets[self.alias]

        # 2. Delete alias from each stage's registered api trackers.
        for stage in existing_registered_apis.keys():
            del self.config.stages[stage].registered_apis[self.alias]

        click.echo(f"Removed '{self.alias}'.")
        click.echo()
        self.config.commit()
        # Back out to the target management menu since we've just deleted this.
        return BACK_SENTINEL

    def modify_alias(self) -> None:
        old_value = self.alias

        while True:
            new_value = click.prompt("Target Alias", default=old_value)
            if old_value == new_value:
                return
            if new_value not in self.config.targets:
                break

            click.secho(f"'{new_value}' already exists!", fg="yellow")
            click.echo("Please choose a unique alias.")

        # 1. Swap config.stages[old_value] -> config.stages[new_value]
        self.config.targets[new_value] = self.target_config
        del self.config.targets[old_value]

        # 2. Update registered api ID references
        for stage_config in self.config.stages.values():
            if old_value in stage_config.registered_apis:
                stage_config.registered_apis[new_value] = stage_config.registered_apis[
                    old_value
                ]
                del stage_config.registered_apis[old_value]

        # 3. Modify internal instance reference
        self.alias = new_value
        self.config.commit()

    def modify_description(self) -> None:
        old_value = self.target_config.description

        new_value = click.prompt("Target Description", default=old_value)
        if old_value == new_value:
            return

        self.target_config.description = new_value
        self.config.commit()

    def modify_scope(self) -> None:
        old_value = self.target_config.security.globus_auth_scope

        scope_options: list[tuple[str | None | _ManualInput, str]] = [
            (None, "<None>"),
            (_ManualInput(), "<Enter a scope string>"),
        ] + [(scope, scope) for scope in sorted(self._all_known_scopes())]

        new_value = prompt_selection("Scope", scope_options, default=old_value)
        if new_value == old_value:
            return

        elif isinstance(new_value, _ManualInput):
            new_value = click.prompt("Globus Scope", type=str)

        self.target_config.security.globus_auth_scope = new_value
        self.config.commit()

    def display_discovered_security(self) -> None:
        """
        Print a 'pretty' version of the discovered security (globus auth scopes)
        to stdout.
        """
        panel = Panel(
            Pretty(self.security_explorer.rich_discovered_security),
            title=f"{self.alias} security",
        )
        console.print(panel)

    def _all_known_scopes(self) -> set[str]:
        #   openapi-analyses and
        all_known_scopes = self.context.analyzer.agg_well_known_scopes.copy()
        #   configured targets.
        for target in self.config.targets.values():
            if scope := target.security.globus_auth_scope:
                all_known_scopes.add(scope)
        return all_known_scopes
