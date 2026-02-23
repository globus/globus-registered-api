# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from .analyze import analyze_command
from .api import api_group
from .build import build_command
from .init import init_command
from .manage import manage_command
from .publish import publish_command
from .session import session_group

ROOT_COMMANDS = (
    api_group,
    session_group,
    init_command,
    manage_command,
    build_command,
    publish_command,
    analyze_command,
)

__all__ = ("ROOT_COMMANDS",)
