# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.context import CLIContext
from globus_registered_api.context import with_cli_context


@click.command
@with_cli_context
def publish_command(ctx: CLIContext) -> None:
    """
    [Placeholder] Publish Repository Config.
    """
