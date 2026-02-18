# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from .create import create_command
from .delete import delete_command
from .list import list_command
from .show import show_command
from .update import update_command


@click.group(name="api")
def api_group() -> None:
    """
    Call Flows APIs directly.
    """


api_group.add_command(create_command)
api_group.add_command(delete_command)
api_group.add_command(list_command)
api_group.add_command(show_command)
api_group.add_command(update_command)

__all__ = ("api_group",)
