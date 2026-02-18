# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from .api import api_group
from .init import init_command
from .manage import manage_command
from .publish import publish_command
from .session import session_group

ROOT_COMMANDS = (
    api_group,
    session_group,
    manage_command,
    init_command,
    publish_command,
)

__all__ = ("ROOT_COMMANDS",)
