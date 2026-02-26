# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t
from dataclasses import dataclass

from globus_sdk import GlobusApp

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.openapi import SpecAnalysis


@dataclass
class ManageContext:
    """Context object for configurator subcommands."""

    config: RegisteredAPIConfig
    analysis: SpecAnalysis
    globus_app: GlobusApp


# Navigation Controls and Types
class BackSentinel: ...


BACK_SENTINEL = BackSentinel()


class ExitSentinel: ...


EXIT_SENTINEL = ExitSentinel()

ControlSignal: t.TypeAlias = BackSentinel | ExitSentinel

ConfiguratorSubcommand: t.TypeAlias = t.Callable[[], None]
ConfiguratorMenu: t.TypeAlias = list[tuple[ConfiguratorSubcommand | ControlSignal, str]]

MainMenu: t.TypeAlias = list[tuple[ConfiguratorMenu | ExitSentinel, str]]
