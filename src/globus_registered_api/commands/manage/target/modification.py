# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

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

console = Console()


class _ManualInput: ...


@dataclass
class ImputedSecurity:
    """
    Dynamic override of TargetSecurityConfig for display purposes.

    Represents a security definition imputed from the OpenAPI spec, not defined in
    the config.
    """

    globus_auth_scopes: list[str]


class TargetModificationMenu(DispatchMenu):
    """
    Dispatch menu for a single selected target.

    Menu Options:
      * Print Target
      * Modify Alias
      * Modify Description
      * Modify Globus Scope (<-- inclusion & wording depends on the state of the
            config and OpenAPI specification)
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
            (self.modifier.print_target, "Print Target"),
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

        elif self._well_known_scopes_exist_in_openapi():
            return self.modifier.print_openapi_scopes, "Print Globus Scopes (OpenAPI)"

        else:
            return self.modifier.modify_scope, "Add Globus Scope"

    def _well_known_scopes_exist_in_openapi(self) -> bool:
        specifier = self.target_config.specifier
        analysis = self.analyzer.agg_target_analyses.get(specifier)
        return bool(analysis and analysis.well_known_scopes)


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

    def print_target(self) -> None:
        target_config = self.target_config
        if not target_config.security.globus_auth_scope:
            specifier = target_config.specifier
            analysis = self.context.analyzer.agg_target_analyses.get(specifier)

            # If a target's scope is imputed in any stage's openapi
            #   specification, display it.
            # TODO - distinguish between 'these 3 scopes live in stage A & B' vs
            #    'these 2 scopes live in stage A, this 1 lives in B'
            if analysis and (scopes := analysis.well_known_scopes):
                target_config = target_config.model_copy()
                security = ImputedSecurity(globus_auth_scopes=list(scopes))
                target_config.security = security  # type: ignore

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

    def print_openapi_scopes(self) -> None:
        """
        Print globus scopes from the OpenAPI specification analysis.
        """
        specifier = self.target_config.specifier
        analysis = self.analyzer.agg_target_analyses[specifier]
        scopes = analysis.well_known_scopes

        s = "s" if len(scopes) > 1 else ""
        click.echo(f"The OpenAPI Specification defines {len(scopes)} Globus Scope{s}:")
        for scope in scopes:
            click.echo(f"  - {scope}")
        click.echo()

    def _all_known_scopes(self) -> set[str]:
        #   openapi-analyses and
        all_known_scopes = self.context.analyzer.agg_well_known_scopes.copy()
        #   configured targets.
        for target in self.config.targets.values():
            if scope := target.security.globus_auth_scope:
                all_known_scopes.add(scope)
        return all_known_scopes
