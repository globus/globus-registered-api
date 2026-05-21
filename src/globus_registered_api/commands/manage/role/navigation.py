# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import typing as t

from globus_registered_api.config import GlobusEnvironment
from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.repositories.clients import GlobusClientRepository

from ..context import ManageContext
from .modification import RoleModificationMenu
from .registration import RoleRegistrationMenu


class _ManualInput: ...


class RoleNavigationMenu(DispatchMenu):
    """
    Dispatch menu for target selection.

    Menu Options:
      * Register a New Role
      * Manage 'derek@globus.org' (uuid)
      * Manage 'Flow Admins' (uuid)
      * etc.
    """

    def __init__(self, context: ManageContext, stage: str) -> None:
        self.context = context
        self.stage_config = context.config.stages[stage]
        self.stage = stage

        self._saved_environment: GlobusEnvironment | None = None

    def on_enter(self) -> None:
        globus = GlobusClientRepository.instance()

        self._saved_environment = globus.environment
        globus.environment = self.stage_config.globus_environment

    def on_exit(self) -> None:
        GlobusClientRepository.instance().environment = self._saved_environment
        self._saved_environment = None

    @property
    def menu_title(self) -> str:
        return f"Manage Roles ({self.stage})"

    @property
    def options(self) -> LabeledDispatchOptions:
        _options: LabeledDispatchOptions = [
            (self._add_role_menu(), "<Register a New Role>")
        ]
        for role in self.stage_config.roles:
            menu = RoleModificationMenu(self.context, self.stage, role)
            name, level = menu.modifier.role_name, role.access_level

            _options.append((menu, f"Manage '{name}' ({level.capitalize()})"))
        return _options

    def _add_role_menu(self) -> t.Callable[[], DispatchMenu]:
        return functools.partial(RoleRegistrationMenu, self.context, self.stage)
