# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from .logout import logout_command
from .whoami import whoami_command


@click.group("session")
def session_group() -> None:
    """
    Manage your Globus session.
    """


session_group.add_command(logout_command)
session_group.add_command(whoami_command)

__all__ = ("session_group",)
