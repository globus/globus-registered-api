# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.commands.manage.context import ManageContext
from globus_registered_api.commands.manage.role._name_resolution import RoleNameResolver
from globus_registered_api.config import ROLE_ACCESS_LEVELS
from globus_registered_api.config import RoleConfig
from globus_registered_api.rendering import BACK_SENTINEL
from globus_registered_api.rendering import ControlSignal
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import prompt_selection


class RoleModificationMenu(DispatchMenu):

    def __init__(
        self, context: ManageContext, stage: str, role_config: RoleConfig
    ) -> None:
        self.context = context
        self.role_config = role_config
        self.stage_config = context.config.stages[stage]
        self.modifier = RoleModifier(context, stage, role_config)

    @property
    def menu_title(self) -> str:
        return self.modifier.role_name

    @property
    def options(self) -> LabeledDispatchOptions:
        return [
            (
                self.modifier.modify_access_level,
                DataLabel(
                    "Modify Access Level", self.role_config.access_level.capitalize()
                ),
            ),
            (self.modifier.remove_role, "Remove Role"),
        ]


class RoleModifier:
    """
    Central management pane of role configuration.

    Each method corresponds to a subcommand of `gra manage` related to role management.
    """

    def __init__(
        self, context: ManageContext, stage: str, role_config: RoleConfig
    ) -> None:
        self.config = context.config
        self.stage_config = self.config.stages[stage]
        self.role_config = role_config

        self.role_name = RoleNameResolver().resolve_display_name(role_config)

    def modify_access_level(self) -> None:
        old_value = self.role_config.access_level
        new_value = prompt_selection(
            "Access Level",
            [(level, level.capitalize()) for level in ROLE_ACCESS_LEVELS],
            default=old_value,
        )
        if old_value != new_value:
            self.role_config.access_level = new_value
            self.config.commit()

    def remove_role(self) -> ControlSignal | None:
        """Remove a role from the configuration."""
        if click.confirm(f"Remove access for '{self.role_name}'?"):
            self.stage_config.roles.remove(self.role_config)
            self.config.commit()
            click.echo(f"Removed '{self.role_name}' role.")
            return BACK_SENTINEL

        click.secho("Aborted removal", fg="yellow")
        return None
