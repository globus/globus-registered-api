# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t
from uuid import UUID

import click

from globus_registered_api.commands.manage.context import ManageContext
from globus_registered_api.commands.manage.role._name_resolution import RoleNameResolver
from globus_registered_api.config import ROLE_ACCESS_LEVELS
from globus_registered_api.config import RoleAccessLevel
from globus_registered_api.config import RoleConfig
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import FormMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import prompt_selection
from globus_registered_api.repositories.groups import Group
from globus_registered_api.repositories.groups import GroupRepository


class RoleRegistrationMenu(FormMenu):
    """Dispatch menu for adding new roles to the configuration."""

    menu_title: str = "Add Role"

    def __init__(self, context: ManageContext, stage: str) -> None:
        self.config = context.config
        self.stage_config = self.config.stages[stage]
        self.stage = stage

        self.builder = RoleBuilder(self.stage_config.roles)

    @property
    def options(self) -> LabeledDispatchOptions:
        if self.builder.role_type == "group":
            select_id = (
                self.builder.select_group,
                DataLabel("Select Group", self.builder.display_name),
            )
        else:
            select_id = (
                self.builder.select_identity,
                DataLabel("Select Identity", self.builder.display_name),
            )

        return [
            (
                self.builder.set_role_type,
                DataLabel("Change Role Type", self.builder.role_type.capitalize()),
            ),
            select_id,
            (
                self.builder.set_access_level,
                DataLabel("Set Access Level", self.builder.access_level.capitalize()),
            ),
        ]

    def is_submittable(self) -> bool:
        return bool(
            self.builder.role_type
            and self.builder.role_id
            and self.builder.access_level
        )

    def on_submit(self) -> None:
        self.stage_config.roles.append(self.builder.build())
        self.config.commit()


class RoleBuilder:

    def __init__(self, existing_roles: list[RoleConfig]) -> None:
        self._groups = GroupRepository.instance()
        self._resolver = RoleNameResolver()

        self.role_type: t.Literal["group", "identity"] = "group"
        self.role_id: str | None = None
        self.access_level: RoleAccessLevel = "viewer"

        self._known_group_ids = {
            str(config.id) for config in existing_roles if config.type == "group"
        }
        self._known_identity_ids = {
            str(config.id) for config in existing_roles if config.type == "identity"
        }

    @property
    def display_name(self) -> str | None:
        if not (self.role_type and self.role_id):
            return None

        role = self.role_type, self.role_id
        return self._resolver.resolve_display_name(role)

    def set_role_type(self) -> None:
        old_value = self.role_type
        new_value = prompt_selection(
            "Role Type",
            [("group", "Group"), ("identity", "Identity")],
            default=old_value,
        )
        if old_value != new_value:
            self.role_type = new_value
            self.role_id = None

    def select_group(self):
        old_value = self.role_id if self.role_type == "group" else None
        group = self._prompt_group_selection()

        if old_value != group.id:
            self.role_id = group.id
            self.role_type = "group"

    def _prompt_group_selection(self) -> Group:
        groups = [
            group
            for group in self._groups.active_groups()
            if group.id not in self._known_group_ids
        ]

        selection = prompt_selection(
            "Group",
            #
            [
                (None, "<Manually Enter a Group ID>"),
                *[(group, group.name) for group in groups],
            ],
        )
        if selection is None:
            group_id = str(click.prompt("Group ID", type=click.UUID))
            return Group(id=group_id, name=group_id)

        return selection

    def select_identity(self) -> None:
        old_value = self.role_id if self.role_type == "identity" else None
        new_value = str(click.prompt("Identity ID", type=click.UUID, default=old_value))

        self.role_type = "identity"
        self.role_id = new_value

    def set_access_level(self) -> None:
        old_value = self.access_level
        new_value = prompt_selection(
            "Access Level",
            [(level, level.capitalize()) for level in ROLE_ACCESS_LEVELS],
            default=old_value,
        )

        if old_value != new_value:
            self.access_level = new_value

    def build(self) -> RoleConfig:
        return RoleConfig(
            type=self.role_type,
            id=UUID(self.role_id),
            access_level=self.access_level,
        )
