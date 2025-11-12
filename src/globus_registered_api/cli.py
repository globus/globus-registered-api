# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: MIT

import click

group = click.Group()


@group.command()
def bogus() -> None:
    """Print 'bogus'."""

    print("bogus")
