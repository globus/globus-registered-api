# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import typing as t

from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import LabeledDispatchOptions

from ..context import ManageContext
from .modification import StageModificationMenu
from .registration import StageRegistrationMenu


class _ManualInput: ...


class StageNavigationMenu(DispatchMenu):
    """
    Dispatch menu for target selection.

    Menu Options:
      * Register a New Stage
      * Set Default ('current-default-stage')
      * Manage 'stage-1'
      * Manage 'stage-2'
      * etc.
    """

    menu_title: str = "Manage Stages"

    def __init__(self, context: ManageContext) -> None:
        self.context = context
        self.config = context.config

        self._add_stage_menu = functools.partial(StageRegistrationMenu, context)

    @property
    def options(self) -> LabeledDispatchOptions:
        return [
            (self._add_stage_menu, "<Register a New Stage>"),
            *[
                (self._stage_menu(stage), f"Manage '{stage}'")
                for stage in sorted(self.config.stages)
            ],
        ]

    def _stage_menu(self, stage: str) -> t.Callable[[], StageModificationMenu]:
        return functools.partial(StageModificationMenu, self.context, stage)
