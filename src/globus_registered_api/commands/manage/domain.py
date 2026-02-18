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
    """Context object for manage subcommands."""

    config: RegisteredAPIConfig
    analysis: SpecAnalysis
    globus_app: GlobusApp


ManageSubcommand = t.Callable[[], None]
ManageMenuOptions = list[tuple[str, ManageSubcommand]]


class SubcommandCanceled(Exception):
    """Exception raised that the in-progress command has been canceled."""
