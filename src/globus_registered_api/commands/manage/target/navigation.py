# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import typing as t

from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import LabeledDispatchOptions

from ..context import ManageContext
from .modification import TargetModificationMenu
from .registration import TargetRegistrationMenu


class TargetNavigationMenu(DispatchMenu):
    """
    Dispatch menu for target selection.

    Menu Options:
      * <Register a New Target>
      * target-alias-1
      * target-alias-2
      * etc.
    """

    menu_title: str = "Manage Targets"

    def __init__(self, context: ManageContext) -> None:
        self.context = context
        self.config = context.config

    @property
    def options(self) -> LabeledDispatchOptions:
        alias_options: LabeledDispatchOptions = []
        for alias in sorted(self.config.targets.keys()):
            target_config = self.config.targets[alias]
            route = f"{target_config.method} {target_config.path}"
            option = (self._target_menu(alias), DataLabel(alias, route))
            alias_options.append(option)

        return [
            (TargetRegistrationMenu(self.context), "<Register a New Target>"),
            *alias_options,
        ]

    def _target_menu(self, alias: str) -> t.Callable[[], DispatchMenu]:
        return functools.partial(TargetModificationMenu, self.context, alias)
